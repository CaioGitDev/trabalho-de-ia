"""Demo da Fase 4 (NLP): texto de ingredientes -> analise estruturada.

Modos de uso:

    # 1) Sobre as amostras OCR ja guardadas (data/sample_labels/_results.json),
    #    comparando texto de referencia (limpo) vs texto OCR (ruidoso):
    python src/nlp_demo.py

    # 2) Pipeline completo a partir de uma imagem (OCR -> NLP):
    python src/nlp_demo.py --image data/sample_labels/5601009935185.jpg

    # 3) Analisar uma string de ingredientes diretamente:
    python src/nlp_demo.py --text "Farinha de trigo, agua, sal, aroma."
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from nlp_ingredients import analyze_ingredients, format_report

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "data" / "sample_labels" / "_results.json"
NLP_OUT = ROOT / "data" / "sample_labels" / "_nlp_results.json"


def _serialize(result) -> dict:
    return {
        "gluten_free_label": result.gluten_free_label,
        "gluten_ingredients": [m.term for m in result.gluten_ingredients],
        "ambiguous_ingredients": [m.term for m in result.ambiguous_ingredients],
        "allergens": result.allergens,
        "n_recognized": len(result.matches),
        "n_unknown": len(result.unknown_segments),
        "ingredients": [
            {
                "term": m.term, "gluten": m.gluten, "allergen": m.allergen_label,
                "tag": m.tag, "score": round(m.score, 3),
                "method": m.method, "declaration": m.declaration,
            }
            for m in result.matches
        ],
    }


def _print(*args):
    # garante UTF-8 mesmo em consolas Windows cp1252
    text = " ".join(str(a) for a in args)
    sys.stdout.buffer.write((text + "\n").encode("utf-8", errors="replace"))


def run_samples() -> None:
    if not SAMPLES.exists():
        _print(f"Amostras nao encontradas: {SAMPLES}")
        _print("Corre primeiro o pipeline OCR (Fase 3).")
        return
    data = json.loads(SAMPLES.read_text(encoding="utf-8"))
    out = []
    for d in data:
        _print("=" * 80)
        _print(f"PRODUTO: {d.get('product_name', '?')}  (conf. OCR: {d.get('mean_conf', 0):.1f}%)")

        ref = d.get("ref_ingredients") or ""
        ref_res = analyze_ingredients(ref) if ref else None
        if ref_res is not None:
            _print("\n[Referencia limpa (OFF)]")
            _print(format_report(ref_res))

        ocr = d.get("ocr_ingredients") or ""
        ocr_res = analyze_ingredients(ocr)
        _print("\n[Texto OCR (ruidoso) -> NLP]")
        _print(format_report(ocr_res))
        _print("")

        out.append({
            "code": d.get("code"),
            "product_name": d.get("product_name"),
            "mean_conf": d.get("mean_conf"),
            "nlp_reference": _serialize(ref_res) if ref_res else None,
            "nlp_ocr": _serialize(ocr_res),
        })

    NLP_OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    _print(f"\nResultados NLP gravados em: {NLP_OUT.relative_to(ROOT)}")


def run_image(image_path: str) -> int:
    try:
        from ocr_pipeline import run as ocr_run
    except Exception as exc:  # pragma: no cover - depende de Tesseract
        _print(f"Nao foi possivel importar o pipeline OCR: {exc}")
        return 2
    p = Path(image_path)
    if not p.exists():
        _print(f"Imagem nao encontrada: {p}")
        return 2
    res = ocr_run(p)
    _print("=" * 80)
    _print(f"IMAGEM: {p.name}  (conf. OCR: {res.mean_confidence:.1f}%)")
    _print("\n[Seccao de ingredientes extraida]")
    _print(res.ingredients_only or "(nao detetada)")
    _print("\n[Analise NLP]")
    _print(format_report(analyze_ingredients(res.ingredients_only or res.cleaned_text)))
    return 0


def run_text(text: str) -> int:
    _print("=" * 80)
    _print(format_report(analyze_ingredients(text)))
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Demo NLP de ingredientes (Fase 4)")
    p.add_argument("--image", help="Corre OCR+NLP sobre uma imagem de rotulo")
    p.add_argument("--text", help="Analisa uma string de ingredientes")
    args = p.parse_args()

    if args.text:
        return run_text(args.text)
    if args.image:
        return run_image(args.image)
    run_samples()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
