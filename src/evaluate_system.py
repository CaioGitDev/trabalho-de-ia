"""Fase 8 - Avaliacao e validacao.

Mede Accuracy / Precision / Recall / F1 (com a ferramenta do professor,
`eval_metrics` -> confusion_matrix2) em tres frentes:

A) MODELO SUPERVISIONADO: o melhor classificador da Fase 5 (Random Forest)
   no conjunto de teste retido. Confirma o desempenho ML.

B) PIPELINE NLP+REGRAS (end-to-end, NAO circular): corre o motor de NLP +
   regras sobre o TEXTO LIVRE de ingredientes (`ingredients_text`) e compara
   a deteccao de gluten com um ROTULO INDEPENDENTE - o campo `allergens` da
   OFF (preenchido por contribuidores, e que o pipeline NUNCA le). Pergunta
   binaria: "o produto contem gluten?".

C) IMPACTO DO OCR: nas 5 imagens reais, compara o veredicto obtido a partir
   do texto OCR vs. do texto de referencia limpo, evidenciando a degradacao
   introduzida pela qualidade fotografica.

Tambem imprime exemplos de erros e uma discussao de limitacoes, e grava um
resumo em docs/reports/avaliacao_fase8.md.

Uso:
    python src/evaluate_system.py            # amostra (rapido)
    python src/evaluate_system.py --full     # usa todos os produtos elegiveis
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

from classifier_rules import CONTEM_GLUTEN, assess
from eval_metrics import evaluate
from features import build_dataset
from nlp_ingredients import analyze_ingredients

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "processed" / "products_portugal.csv"
SAMPLES = ROOT / "data" / "sample_labels" / "_results.json"
OUT_MD = ROOT / "docs" / "reports" / "avaliacao_fase8.md"
RANDOM_STATE = 42

GT_CONTEM = "contem"
GT_SEM = "sem"


def _p(buf: list[str], line: str = "") -> None:
    print(line)
    buf.append(line)


# ----------------------------------------------------------------------
# A) Modelo supervisionado
# ----------------------------------------------------------------------

def eval_supervised(buf: list[str]) -> None:
    _p(buf, "## A) Modelo supervisionado (Random Forest) - conjunto de teste\n")
    ds = build_dataset()
    X_tr, X_te, y_tr, y_te = train_test_split(
        ds.X, ds.y, test_size=0.25, stratify=ds.y, random_state=RANDOM_STATE)
    rf = RandomForestClassifier(n_estimators=120, random_state=RANDOM_STATE, n_jobs=-1)
    rf.fit(X_tr, y_tr)
    ev = evaluate(list(y_te), list(rf.predict(X_te)))
    _p(buf, f"Amostras de teste: {len(y_te)}")
    _p(buf, f"Exatidao={ev.accuracy*100:.2f}%  macro-F1={ev.macro_f1*100:.2f}%  "
            f"macro-P={ev.macro_precision*100:.2f}%  macro-R={ev.macro_recall*100:.2f}%\n")
    _p(buf, "Matriz de confusao (linhas=real, colunas=previsto):")
    _p(buf, "```")
    _p(buf, ev.cm_string.rstrip())
    _p(buf, "```")
    for c, m in ev.per_class.items():
        _p(buf, f"- {c}: P={m['precision']*100:.1f}%  R={m['recall']*100:.1f}%  "
                f"F1={m['f1']*100:.1f}%")
    _p(buf)


# ----------------------------------------------------------------------
# B) Pipeline end-to-end vs rotulo independente
# ----------------------------------------------------------------------

def eval_pipeline(buf: list[str], sample: int | None) -> None:
    _p(buf, "## B) Pipeline NLP+regras sobre texto livre vs. rotulo independente\n")
    _p(buf, "Ground-truth: campo `allergens` da OFF contem `en:gluten` (sim/nao).")
    _p(buf, "O pipeline so le `ingredients_text` -> avaliacao nao circular.\n")

    df = pd.read_csv(DATA_FILE, low_memory=False)
    mask = (df["ingredients_text"].notna()
            & df["allergens"].notna()
            & df["allergens"].astype(str).str.strip().ne(""))
    sub = df[mask].copy()
    if sample and sample < len(sub):
        sub = sub.sample(n=sample, random_state=RANDOM_STATE)
    _p(buf, f"Produtos avaliados: {len(sub)}")

    gt = np.where(sub["allergens"].astype(str).str.lower().str.contains("en:gluten"),
                  GT_CONTEM, GT_SEM)

    preds: list[str] = []
    for txt in sub["ingredients_text"].astype(str):
        grade = assess(analyze_ingredients(txt)).gluten_grade
        preds.append(GT_CONTEM if grade == CONTEM_GLUTEN else GT_SEM)

    actual = list(gt)
    ev = evaluate(actual, preds)
    _p(buf, f"Exatidao={ev.accuracy*100:.2f}%  macro-F1={ev.macro_f1*100:.2f}%  "
            f"macro-P={ev.macro_precision*100:.2f}%  macro-R={ev.macro_recall*100:.2f}%\n")
    _p(buf, "Matriz de confusao (linhas=real, colunas=previsto):")
    _p(buf, "```")
    _p(buf, ev.cm_string.rstrip())
    _p(buf, "```")
    for c, m in ev.per_class.items():
        _p(buf, f"- {c}: P={m['precision']*100:.1f}%  R={m['recall']*100:.1f}%  "
                f"F1={m['f1']*100:.1f}%")
    _p(buf)

    # exemplos de erros
    sub = sub.reset_index(drop=True)
    fn, fp = [], []
    for i, (a, pr) in enumerate(zip(actual, preds)):
        if a == GT_CONTEM and pr == GT_SEM and len(fn) < 3:
            fn.append(sub.iloc[i])
        elif a == GT_SEM and pr == GT_CONTEM and len(fp) < 3:
            fp.append(sub.iloc[i])
    _p(buf, "Exemplos de FALSOS NEGATIVOS (allergens diz gluten, pipeline nao detetou):")
    for r in fn:
        _p(buf, f"  - {str(r.get('product_name'))[:40]}: "
                f"\"{str(r['ingredients_text'])[:90]}\"")
    _p(buf, "\nExemplos de FALSOS POSITIVOS (pipeline detetou gluten, allergens nao lista):")
    for r in fp:
        _p(buf, f"  - {str(r.get('product_name'))[:40]}: "
                f"\"{str(r['ingredients_text'])[:90]}\"")
    _p(buf)


# ----------------------------------------------------------------------
# C) Impacto do OCR nas imagens reais
# ----------------------------------------------------------------------

def eval_ocr_impact(buf: list[str]) -> None:
    _p(buf, "## C) Impacto do OCR (5 imagens reais)\n")
    if not SAMPLES.exists():
        _p(buf, "(sem amostras OCR)")
        return
    data = json.loads(SAMPLES.read_text(encoding="utf-8"))
    _p(buf, "| Produto | Conf. OCR | Veredicto (referencia) | Veredicto (OCR) |")
    _p(buf, "| --- | --- | --- | --- |")
    for d in data:
        ref = d.get("ref_ingredients") or ""
        ocr = d.get("ocr_ingredients") or ""
        g_ref = assess(analyze_ingredients(ref)).gluten_grade if ref else "-"
        g_ocr = assess(analyze_ingredients(ocr)).gluten_grade if ocr else "-"
        _p(buf, f"| {str(d.get('product_name'))[:28]} | {d.get('mean_conf', 0):.0f}% "
                f"| {g_ref} | {g_ocr} |")
    _p(buf)


# ----------------------------------------------------------------------
# Limitacoes
# ----------------------------------------------------------------------

LIMITATIONS = """## Limitacoes e discussao

- **OCR e a maior fonte de erro.** Em fotografias reais (confianca media ~48%)
  grande parte do texto nao e recuperada, pelo que o veredicto a partir da
  imagem e frequentemente menos grave do que o real (ver seccao C). O sistema
  funciona muito melhor sobre texto de ingredientes limpo.
- **Lingua do texto (principal causa de falsos negativos).** O lexico e em
  portugues; produtos cujo `ingredients_text` esta em ingles/frances ("wheat
  flour", "flocons d'avoine") nao sao reconhecidos. Uma extensao natural e
  juntar termos EN/FR ao lexico ou usar a coluna `ingredients_tags` quando
  disponivel.
- **Ground-truth ruidoso (seccao B).** O campo `allergens` da OFF e preenchido
  por contribuidores e tem falsos negativos (produtos com gluten sem o declarar).
  Varios "falsos positivos" do pipeline sao, na verdade, deteccoes CORRETAS que
  o rotulo OFF omitiu (ex.: "pao ralado (farinha de trigo)", "semola de trigo-
  duro") -- ou seja, a precisao real e superior a medida.
- **Mojibake do dump OFF.** Alguns textos trazem caracteres corrompidos
  (ex.: "prote�na", "�gua"), o que tambem prejudica o reconhecimento; por isso
  a Fase 2 preferiu a coluna normalizada `ingredients_tags` para a estatistica.
- **Supervisao fraca (Fase 5).** Os classificadores foram treinados com rotulos
  gerados pelas proprias regras; medem sobretudo a capacidade de reproduzir a
  logica de regras a partir do "bag-of-tags", nao um juizo humano independente.
- **Matching difuso favorece o recall.** Ha falsos positivos por semelhanca
  (ex.: "lactone" ~ "lactose"). E uma escolha deliberada (mais seguro sobre-
  assinalar risco), mas reduz a precisao.
- **Cobertura do lexico PT.** Ingredientes fora do lexico ficam por classificar;
  a aveia e tratada como gluten por precaucao (contaminacao cruzada frequente).
"""


def main() -> int:
    ap = argparse.ArgumentParser(description="Avaliacao do sistema (Fase 8)")
    ap.add_argument("--full", action="store_true",
                    help="Usa todos os produtos elegiveis (mais lento)")
    ap.add_argument("--sample", type=int, default=1500,
                    help="Nº de produtos na avaliacao B (default 1500)")
    args = ap.parse_args()

    buf: list[str] = []
    _p(buf, "# Fase 8 - Avaliacao e validacao do sistema\n")

    eval_supervised(buf)
    eval_pipeline(buf, sample=None if args.full else args.sample)
    eval_ocr_impact(buf)
    _p(buf, LIMITATIONS)

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(buf), encoding="utf-8")
    print(f"\nResumo gravado em: {OUT_MD.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
