"""Demo OCR end-to-end com imagens reais do Open Food Facts.

Escolhe alguns produtos PT do dataset filtrado, descarrega as imagens
da lista de ingredientes via API do OFF, corre o pipeline e mostra o
texto extraido junto com a confianca media reportada pelo Tesseract.

Resultado serve para:
- validar que toda a cadeia (download -> preprocess -> tesseract ->
  clean -> extract) funciona;
- ter material para a Fase 4 (NLP), com pares (imagem, texto OCR,
  ingredients_text de referencia do OFF) para medir erro.
"""
from __future__ import annotations

import io
import json
import sys
import time
from pathlib import Path

# Console Windows e tipicamente cp1252 -> falha em chars Unicode.
# Forca stdout para UTF-8 com fallback "replace".
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import pandas as pd
import requests

from ocr_pipeline import run as run_ocr


ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "processed" / "products_portugal.csv"
IMG_DIR = ROOT / "data" / "sample_labels"

USER_AGENT = "TrabalhoIIA-UFP/0.1 (academic)"
API_PRODUCT = "https://world.openfoodfacts.org/api/v2/product/{code}.json"


def fetch_product_meta(code: str) -> dict | None:
    url = API_PRODUCT.format(code=code)
    headers = {"User-Agent": USER_AGENT}
    r = requests.get(url, headers=headers, timeout=30)
    if r.status_code != 200:
        return None
    data = r.json()
    if data.get("status") != 1:
        return None
    return data.get("product", {})


def best_ingredients_image_url(product: dict) -> str | None:
    """Procura o URL da imagem de ingredientes em PT (ou fallback).

    A OFF disponibiliza varios tamanhos em sub-dicts (`display`, `small`,
    `thumb`). `display` e ~400px e `full` (que reconstituimos a partir do
    URL) e a versao original. Para OCR, full e essencial.
    """
    sel = product.get("selected_images", {}).get("ingredients", {})
    candidates: list[str] = []
    for size in ("full", "display"):
        sub = sel.get(size, {})
        for lang in ("pt", "en", "fr", "es"):
            if sub.get(lang):
                candidates.append(sub[lang])
    fallback = product.get("image_ingredients_url")
    if fallback:
        candidates.append(fallback)
    if not candidates:
        return None
    # Converte qualquer URL ".<size>.jpg" -> ".full.jpg" para garantir
    # resolucao maxima (OFF aceita "full" sempre).
    chosen = candidates[0]
    return _upgrade_to_full(chosen)


def _upgrade_to_full(url: str) -> str:
    """Substitui .<digits>.jpg por .full.jpg quando aplicavel."""
    import re
    return re.sub(r"\.(\d+)\.jpg(\?.*)?$", r".full.jpg\2", url)


def download(url: str, out_path: Path) -> bool:
    headers = {"User-Agent": USER_AGENT}
    r = requests.get(url, headers=headers, timeout=60, stream=True)
    if r.status_code != 200:
        return False
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("wb") as f:
        for chunk in r.iter_content(64 * 1024):
            f.write(chunk)
    return True


def pick_candidates(n: int = 5) -> list[dict]:
    """Escolhe produtos PT com ingredientes textuais (boa chance de
    terem imagem de ingredientes correspondente).
    """
    df = pd.read_csv(DATA_FILE, low_memory=False)
    has_ing = df.dropna(subset=["ingredients_text", "code"])
    # nomes legiveis (para o relatorio) e codigos longos (mais provavel
    # serem produtos novos com fotos)
    has_ing = has_ing[has_ing["product_name"].notna()]
    has_ing = has_ing[has_ing["ingredients_text"].str.len() > 30]
    # Amostra deterministica
    sample = has_ing.sample(n=min(n, len(has_ing)), random_state=42)
    return sample[["code", "product_name", "brands", "ingredients_text"]].to_dict("records")


def main(n: int = 5) -> int:
    if not DATA_FILE.exists():
        print(f"Falta {DATA_FILE}. Corre src/filter_portugal.py primeiro.", file=sys.stderr)
        return 1

    print(f"A escolher {n} produtos candidatos do dataset PT...")
    candidates = pick_candidates(n=n)

    results: list[dict] = []
    IMG_DIR.mkdir(parents=True, exist_ok=True)

    for i, cand in enumerate(candidates, 1):
        code = str(cand["code"])
        print(f"\n[{i}/{len(candidates)}] {cand['product_name']} ({code})")

        prod = fetch_product_meta(code)
        time.sleep(0.5)
        if not prod:
            print("  - produto inacessivel via API")
            continue
        url = best_ingredients_image_url(prod)
        if not url:
            print("  - sem imagem de ingredientes disponivel")
            continue

        ext = url.split(".")[-1].split("?")[0].lower()
        img_path = IMG_DIR / f"{code}.{ext}"
        if not img_path.exists():
            print(f"  - download: {url}")
            if not download(url, img_path):
                print("  - falha no download")
                continue
        else:
            print(f"  - ja em cache: {img_path.name}")

        try:
            result = run_ocr(img_path)
        except Exception as e:
            print(f"  - erro OCR: {e}")
            continue

        print(f"  -> confianca media: {result.mean_confidence:.1f}%")
        print(f"  -> chars extraidos: {len(result.cleaned_text)}")
        results.append({
            "code": code,
            "product_name": cand["product_name"],
            "ref_ingredients": cand["ingredients_text"],
            "ocr_raw": result.raw_text,
            "ocr_clean": result.cleaned_text,
            "ocr_ingredients": result.ingredients_only,
            "mean_conf": round(result.mean_confidence, 1),
            "image": str(img_path.relative_to(ROOT)),
        })

    if not results:
        print("\nNenhum produto foi processado com sucesso.", file=sys.stderr)
        return 2

    out_json = IMG_DIR / "_results.json"
    with out_json.open("w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 72)
    print(f"RESUMO ({len(results)} produtos com OCR bem-sucedido)")
    print("=" * 72)
    avg_conf = sum(r["mean_conf"] for r in results) / len(results)
    print(f"Confianca media global: {avg_conf:.1f}%")
    for r in results:
        print(f"\n[{r['code']}] {r['product_name']}  (conf={r['mean_conf']}%)")
        print(f"  Referencia OFF: {r['ref_ingredients'][:140]}...")
        ocr_snippet = r["ocr_ingredients"] or r["ocr_clean"]
        print(f"  OCR extraido:   {ocr_snippet[:140].replace(chr(10), ' / ')}...")
    print(f"\nJSON com resultados completos: {out_json.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    n_arg = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    raise SystemExit(main(n=n_arg))
