"""Fase 6 - Motor de explicabilidade.

O enunciado exige que o sistema justifique TODAS as decisoes, com uma tabela
por ingrediente do tipo:

    | Ingrediente      | Estado | Observacao              |
    | Farinha de trigo | X      | Contem gluten           |
    | Acucar           | OK     | Seguro                  |
    | Amido modificado | ?      | Origem nao especificada |

Este modulo traduz cada `IngredientMatch` (Fase 4) numa linha explicada
(simbolo + observacao) e combina com a `RiskAssessment` (Fase 5) para um
veredicto global justificado. Nao introduz nova logica de decisao: apenas
TORNA TRANSPARENTE a que as regras/NLP ja produziram (rastreio pela tag en:).
"""
from __future__ import annotations

from dataclasses import dataclass

from nlp_ingredients import (
    AnalysisResult,
    IngredientMatch,
    DECL_CONTAINS,
    DECL_TRACES,
    GLUTEN as G_GLUTEN,
    AMBIGUOUS as G_AMBIGUOUS,
)
from classifier_rules import RiskAssessment, assess

# Simbolos de estado (versao ASCII + emoji para o relatorio)
SYM_GLUTEN = "X"      # contem gluten
SYM_SAFE = "OK"       # seguro
SYM_AMBIG = "?"       # ambiguo / origem nao declarada
EMOJI = {SYM_GLUTEN: "❌", SYM_SAFE: "✅", SYM_AMBIG: "⚠️"}


@dataclass
class ExplanationRow:
    ingredient: str
    symbol: str        # SYM_GLUTEN | SYM_SAFE | SYM_AMBIG
    observation: str
    tag: str | None    # tag en: canonica (rastreio)


def _declaration_suffix(decl: str) -> str:
    if decl == DECL_TRACES:
        return " (declarado apenas como possivel traco)"
    if decl == DECL_CONTAINS:
        return ' (na declaracao "contem")'
    return ""


def explain_match(m: IngredientMatch) -> ExplanationRow:
    """Constroi a observacao justificada de um ingrediente reconhecido."""
    suffix = _declaration_suffix(m.declaration)

    if m.gluten == G_GLUTEN:
        symbol = SYM_GLUTEN
        obs = "Contem gluten (cereal ou derivado)"
    elif m.gluten == G_AMBIGUOUS:
        symbol = SYM_AMBIG
        obs = "Origem nao especificada: pode conter gluten"
    else:
        symbol = SYM_SAFE
        obs = "Sem gluten conhecido"

    # acrescenta informacao de alergenio (independente do gluten)
    if m.allergen_label:
        obs += f"; alergenio: {m.allergen_label}"
        if symbol == SYM_SAFE:
            # seguro quanto a gluten mas e alergenio declarado -> alerta
            symbol = SYM_AMBIG

    if m.method == "difuso":
        obs += f" [correspondencia aproximada {m.score*100:.0f}%]"

    return ExplanationRow(
        ingredient=m.term,
        symbol=symbol,
        observation=obs + suffix,
        tag=m.tag,
    )


@dataclass
class Explanation:
    rows: list[ExplanationRow]
    assessment: RiskAssessment
    n_unknown: int

    def counts(self) -> dict[str, int]:
        out = {SYM_GLUTEN: 0, SYM_AMBIG: 0, SYM_SAFE: 0}
        for r in self.rows:
            out[r.symbol] += 1
        return out


def explain(analysis: AnalysisResult) -> Explanation:
    rows = [explain_match(m) for m in analysis.matches]
    return Explanation(
        rows=rows,
        assessment=assess(analysis),
        n_unknown=len(analysis.unknown_segments),
    )


# ----------------------------------------------------------------------
# Renderizacao
# ----------------------------------------------------------------------

def _sym(symbol: str, emoji: bool) -> str:
    return EMOJI[symbol] if emoji else symbol


def render_text(exp: Explanation, emoji: bool = False, header: bool = True) -> str:
    a = exp.assessment
    lines = []
    if header:
        lines.append(f"VEREDICTO GLUTEN .... {a.gluten_grade}")
        lines.append(f"ALERGENIOS .......... {a.allergen_status}")
        if a.allergens:
            det = ", ".join(f"{k} ({v})" for k, v in a.allergens.items())
            lines.append(f"  -> {det}")
        lines.append("")
    lines.append(f"{'Ingrediente':<28} {'Estado':<7} Observacao")
    lines.append("-" * 78)
    for r in exp.rows:
        lines.append(f"{r.ingredient[:27]:<28} {_sym(r.symbol, emoji):<7} {r.observation}")
    if exp.n_unknown:
        lines.append("-" * 78)
        lines.append(f"({exp.n_unknown} segmento(s) de texto nao reconhecido(s) - ver limitacoes OCR)")
    return "\n".join(lines)


def render_markdown(exp: Explanation, emoji: bool = True, header: bool = True) -> str:
    a = exp.assessment
    out = []
    if header:
        out.append(f"**Veredicto glúten:** {a.gluten_grade}  ")
        out.append(f"**Alergénios:** {a.allergen_status}")
        if a.allergens:
            det = ", ".join(f"{k} ({v})" for k, v in a.allergens.items())
            out.append(f" — {det}")
        out.append("\n")
    out.append("| Ingrediente | Estado | Observação |")
    out.append("| --- | :---: | --- |")
    for r in exp.rows:
        out.append(f"| {r.ingredient} | {_sym(r.symbol, emoji)} | {r.observation} |")
    return "\n".join(out)


# ----------------------------------------------------------------------
# Demo
# ----------------------------------------------------------------------

def _demo() -> None:
    import sys
    from nlp_ingredients import analyze_ingredients

    def p(*a):
        sys.stdout.buffer.write((" ".join(str(x) for x in a) + "\n").encode("utf-8", "replace"))

    casos = [
        "Farinha de trigo, agua, sal, amido modificado, leite, acucar. "
        "Pode conter tracos de soja.",
        "Acucar, oleo de girassol, milho, sal. Sem gluten.",
    ]
    for txt in casos:
        p("=" * 78)
        p("TEXTO:", txt)
        p("")
        p(render_text(explain(analyze_ingredients(txt)), emoji=True))
        p("")


if __name__ == "__main__":
    _demo()
