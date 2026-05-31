"""Fase 7 - Relatorio de resultado (gerado automaticamente).

Junta todo o pipeline (OCR -> NLP -> regras -> explicabilidade) num relatorio
com as quatro seccoes pedidas no enunciado:

    RESUMO                  -> classificacao global do produto
    ANALISE DOS INGREDIENTES-> tabela detalhada (motor de explicabilidade)
    ALERGENIOS DETETADOS    -> lista dos 14 alergenios EU encontrados
    RECOMENDACOES           -> accoes sugeridas ao consumidor

As recomendacoes sao derivadas por regras a partir do grau de risco, dos
ingredientes ambiguos, dos alergenios e da qualidade do reconhecimento.

Uso CLI:
    python src/report.py --text "Farinha de trigo, agua, sal."
    python src/report.py --image data/sample_labels/5601009935185.jpg
    python src/report.py --image ... --md docs/reports/exemplo.md
    python src/report.py                # corre sobre as amostras OCR
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path

from nlp_ingredients import AnalysisResult, analyze_ingredients, DECL_TRACES
from classifier_rules import (
    ALERG_POSSUI,
    ALTO_RISCO,
    BAIXO_RISCO,
    CONTEM_GLUTEN,
    MEDIO_RISCO,
    SEM_GLUTEN,
)
from explain import Explanation, explain, render_markdown, render_text

ROOT = Path(__file__).resolve().parent.parent


@dataclass
class Report:
    title: str
    gluten_grade: str
    allergen_status: str
    explanation: Explanation
    recommendations: list[str] = field(default_factory=list)


# ----------------------------------------------------------------------
# Recomendacoes (regras)
# ----------------------------------------------------------------------

def build_recommendations(exp: Explanation, ocr_quality: float | None = None) -> list[str]:
    a = exp.assessment
    recs: list[str] = []

    # --- veredicto de gluten ---
    if a.gluten_grade == CONTEM_GLUTEN:
        recs.append("Produto INADEQUADO para celiacos ou intolerantes ao gluten.")
    elif a.gluten_grade == ALTO_RISCO:
        recs.append("Pode conter vestigios de gluten: evitar em caso de doenca "
                    "celiaca ou alergia grave.")
    elif a.gluten_grade == MEDIO_RISCO:
        ambiguos = ", ".join(r.ingredient for r in exp.rows if r.symbol == "?")
        recs.append(f"Confirmar a origem dos ingredientes ambiguos ({ambiguos}) "
                    "junto do fabricante antes de consumir.")
    elif a.gluten_grade == SEM_GLUTEN:
        recs.append("Produto aparentemente seguro quanto ao gluten.")
    elif a.gluten_grade == BAIXO_RISCO:
        recs.append("Sem ingredientes de risco identificados, mas a analise nao "
                    "foi conclusiva: confirmar no rotulo original.")

    # --- alergenios ---
    if a.allergen_status == ALERG_POSSUI:
        declarados = [k for k, v in a.allergens.items() if v != DECL_TRACES]
        tracos = [k for k, v in a.allergens.items() if v == DECL_TRACES]
        if declarados:
            recs.append("Contem alergenios declarados: " + ", ".join(declarados)
                        + ". Inadequado para alergicos a estes.")
        if tracos:
            recs.append("Pode conter vestigios de: " + ", ".join(tracos) + ".")

    # --- qualidade do reconhecimento ---
    if exp.n_unknown > len(exp.rows):
        recs.append("Parte do texto nao foi interpretada (imagem/OCR de baixa "
                    "qualidade): rever manualmente o rotulo.")
    if ocr_quality is not None and ocr_quality < 60:
        recs.append(f"Confianca de OCR baixa ({ocr_quality:.0f}%): fotografar o "
                    "rotulo com melhor iluminacao e foco.")

    recs.append("Em caso de duvida, contactar sempre o fabricante.")
    return recs


def generate_report(analysis: AnalysisResult, title: str = "Produto",
                    ocr_quality: float | None = None) -> Report:
    exp = explain(analysis)
    return Report(
        title=title,
        gluten_grade=exp.assessment.gluten_grade,
        allergen_status=exp.assessment.allergen_status,
        explanation=exp,
        recommendations=build_recommendations(exp, ocr_quality),
    )


# ----------------------------------------------------------------------
# Renderizacao
# ----------------------------------------------------------------------

def render_report_text(rep: Report) -> str:
    L = []
    L.append("#" * 70)
    L.append(f"# RELATORIO DE ANALISE: {rep.title}")
    L.append("#" * 70)
    L.append("")
    L.append("== RESUMO ==")
    L.append(f"  Estado relativo ao gluten : {rep.gluten_grade}")
    L.append(f"  Estado de alergenios      : {rep.allergen_status}")
    L.append("")
    L.append("== ANALISE DOS INGREDIENTES ==")
    L.append(render_text(rep.explanation, emoji=False, header=False))
    L.append("")
    L.append("== ALERGENIOS DETETADOS ==")
    if rep.explanation.assessment.allergens:
        for label, decl in rep.explanation.assessment.allergens.items():
            L.append(f"  - {label} ({decl})")
    else:
        L.append("  Nenhum dos 14 alergenios obrigatorios (UE) detetado.")
    L.append("")
    L.append("== RECOMENDACOES ==")
    for r in rep.recommendations:
        L.append(f"  * {r}")
    L.append("")
    return "\n".join(L)


def render_report_markdown(rep: Report) -> str:
    L = []
    L.append(f"# Relatório de análise: {rep.title}\n")
    L.append("## Resumo\n")
    L.append(f"- **Estado relativo ao glúten:** {rep.gluten_grade}")
    L.append(f"- **Estado de alergénios:** {rep.allergen_status}\n")
    L.append("## Análise dos ingredientes\n")
    L.append(render_markdown(rep.explanation, emoji=True, header=False))
    L.append("\n## Alergénios detetados\n")
    if rep.explanation.assessment.allergens:
        for label, decl in rep.explanation.assessment.allergens.items():
            L.append(f"- {label} ({decl})")
    else:
        L.append("- Nenhum dos 14 alergénios obrigatórios (UE) detetado.")
    L.append("\n## Recomendações\n")
    for r in rep.recommendations:
        L.append(f"- {r}")
    L.append("")
    return "\n".join(L)


# ----------------------------------------------------------------------
# Pipeline / CLI
# ----------------------------------------------------------------------

def _print(text: str) -> None:
    sys.stdout.buffer.write((text + "\n").encode("utf-8", "replace"))


def report_from_text(text: str, title: str = "Produto (texto)") -> Report:
    return generate_report(analyze_ingredients(text), title=title)


def report_from_image(image_path: str | Path) -> Report:
    from ocr_pipeline import run as ocr_run
    p = Path(image_path)
    res = ocr_run(p)
    analysis = analyze_ingredients(res.ingredients_only or res.cleaned_text)
    return generate_report(analysis, title=p.name, ocr_quality=res.mean_confidence)


def _run_samples() -> None:
    import json
    samples = ROOT / "data" / "sample_labels" / "_results.json"
    if not samples.exists():
        _print(f"Amostras nao encontradas: {samples}")
        return
    data = json.loads(samples.read_text(encoding="utf-8"))
    for d in data:
        ref = d.get("ref_ingredients") or ""
        if not ref:
            continue
        rep = generate_report(analyze_ingredients(ref),
                              title=d.get("product_name", "?"))
        _print(render_report_text(rep))


def main() -> int:
    ap = argparse.ArgumentParser(description="Relatorio de analise de rotulo (Fase 7)")
    ap.add_argument("--text", help="Analisa uma string de ingredientes")
    ap.add_argument("--image", help="Pipeline OCR+NLP sobre uma imagem")
    ap.add_argument("--md", help="Grava o relatorio em markdown no caminho indicado")
    args = ap.parse_args()

    if not args.text and not args.image:
        _run_samples()
        return 0

    if args.text:
        rep = report_from_text(args.text)
    else:
        if not Path(args.image).exists():
            _print(f"Imagem nao encontrada: {args.image}")
            return 2
        rep = report_from_image(args.image)

    _print(render_report_text(rep))
    if args.md:
        out = Path(args.md)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render_report_markdown(rep), encoding="utf-8")
        _print(f"\nRelatorio markdown gravado em: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
