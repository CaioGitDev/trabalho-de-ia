"""Fase 5 - Classificador baseado em REGRAS especializadas.

E a abordagem simbolica do enunciado ("Regras especializadas") e tambem a
referencia explicavel sobre a qual assenta a Fase 6. Tem duas faces:

1. Nivel de DATASET (`classify_gluten_status_row`): a partir das tags
   normalizadas (`ingredients_tags`, `allergens`, `labels_tags`) de um
   produto OFF, atribui sem/contem/suspeito/desconhecido. E usado para
   rotular o dataset de treino dos classificadores supervisionados (Fase 5)
   e ja era a logica da analise estatistica da Fase 2.

2. Nivel de TEXTO (`assess`): a partir do `AnalysisResult` do motor NLP
   (Fase 4), produz o grau de risco de gluten em 5 niveis e o estado de
   alergenios, conforme pedido no enunciado.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from knowledge_base import (
    AMBIGUOUS_TAGS,
    GLUTEN_FREE_LABEL_TAGS,
    GLUTEN_TAGS,
)
from nlp_ingredients import (
    AnalysisResult,
    DECL_TRACES,
    GLUTEN as G_GLUTEN,
)


# ----------------------------------------------------------------------
# 1) Regras ao nivel do dataset (tags OFF) -> rotulo para ML
# ----------------------------------------------------------------------

# Os 4 estados usados na Fase 2 e como rotulo de treino na Fase 5.
STATUS_SEM = "sem"
STATUS_CONTEM = "contem"
STATUS_SUSPEITO = "suspeito"
STATUS_DESCONHECIDO = "desconhecido"


def _s(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    return str(v).lower()


def classify_gluten_status_row(row: pd.Series) -> str:
    """Estado de gluten de um produto OFF a partir das suas tags.

    Hierarquia (mais especifico ganha):
      1. allergens contem en:gluten                 -> 'contem'
      2. ingredients_tags contem tag de gluten      -> 'contem'
      3. labels indica certificacao sem gluten      -> 'sem'
      4. ingredients_tags contem tag ambigua        -> 'suspeito'
      5. ingredients_tags presente, sem nada acima  -> 'sem'
      6. ingredients_tags ausente                   -> 'desconhecido'
    """
    allergens = _s(row.get("allergens"))
    ingredients = _s(row.get("ingredients_tags"))
    labels = _s(row.get("labels_tags"))

    if "en:gluten" in allergens:
        return STATUS_CONTEM

    if ingredients:
        ing_set = {t.strip() for t in ingredients.split(",")}
        if ing_set & GLUTEN_TAGS:
            return STATUS_CONTEM
        if any(lbl.strip() in GLUTEN_FREE_LABEL_TAGS for lbl in labels.split(",")):
            return STATUS_SEM
        if ing_set & AMBIGUOUS_TAGS:
            return STATUS_SUSPEITO
        return STATUS_SEM

    if any(lbl.strip() in GLUTEN_FREE_LABEL_TAGS for lbl in labels.split(",")):
        return STATUS_SEM
    return STATUS_DESCONHECIDO


# ----------------------------------------------------------------------
# 2) Regras ao nivel do texto (AnalysisResult) -> grau de risco
# ----------------------------------------------------------------------

# Grau de risco de gluten (5 niveis do enunciado)
SEM_GLUTEN = "Sem Gluten"
BAIXO_RISCO = "Baixo Risco"
MEDIO_RISCO = "Medio Risco"
ALTO_RISCO = "Alto Risco"
CONTEM_GLUTEN = "Contem Gluten"

# Estado de alergenios
ALERG_NENHUM = "Sem alergenios conhecidos"
ALERG_POSSUI = "Possui alergenios"
ALERG_SUSPEITO = "Possui ingredientes suspeitos"


@dataclass
class RiskAssessment:
    gluten_grade: str
    allergen_status: str
    allergens: dict[str, str] = field(default_factory=dict)  # label -> declaracao
    reasons: list[str] = field(default_factory=list)         # justificacoes (Fase 6)


def grade_gluten(analysis: AnalysisResult) -> tuple[str, list[str]]:
    """Atribui o grau de risco de gluten e devolve tambem as justificacoes.

    Logica (mais grave ganha):
      - Contem Gluten: ingrediente com gluten declarado (nao em tracos),
        salvo rotulo "sem gluten" certificado.
      - Alto Risco: gluten apenas como "pode conter tracos".
      - Medio Risco: ingredientes ambiguos (origem nao declarada).
      - Baixo Risco: sem gluten/ambiguos reconhecidos mas com muita
        incerteza (muitos segmentos por reconhecer).
      - Sem Gluten: rotulo certificado, ou ingredientes reconhecidos sem
        gluten nem ambiguos.
    """
    reasons: list[str] = []

    gluten_declared = [m for m in analysis.gluten_ingredients
                       if m.declaration != DECL_TRACES]
    gluten_traces = [m for m in analysis.gluten_ingredients
                     if m.declaration == DECL_TRACES]
    ambiguous = analysis.ambiguous_ingredients

    if analysis.gluten_free_label:
        reasons.append('Rotulo "sem gluten" presente no texto.')
        # rotulo certificado prevalece, mas avisamos se houver contradicao
        if gluten_declared:
            reasons.append("Atencao: rotulo sem gluten mas foram detetados "
                           f"cereais com gluten ({', '.join(m.term for m in gluten_declared)}).")
        return SEM_GLUTEN, reasons

    if gluten_declared:
        for m in gluten_declared:
            reasons.append(f"'{m.term}' contem gluten (cereal/derivado).")
        return CONTEM_GLUTEN, reasons

    if gluten_traces:
        for m in gluten_traces:
            reasons.append(f"'{m.term}' presente apenas como possivel traco.")
        return ALTO_RISCO, reasons

    if ambiguous:
        for m in ambiguous:
            reasons.append(f"'{m.term}': origem nao especificada -> risco potencial.")
        return MEDIO_RISCO, reasons

    # Sem gluten nem ambiguos reconhecidos
    if analysis.matches and len(analysis.unknown_segments) > len(analysis.matches):
        reasons.append("Nenhum ingrediente de risco reconhecido, mas grande "
                       "parte do texto nao foi interpretada (OCR incompleto).")
        return BAIXO_RISCO, reasons

    if analysis.matches:
        reasons.append("Ingredientes reconhecidos sem cereais com gluten nem "
                       "ingredientes ambiguos.")
        return SEM_GLUTEN, reasons

    reasons.append("Texto insuficiente para uma classificacao fiavel.")
    return BAIXO_RISCO, reasons


def classify_allergens(analysis: AnalysisResult) -> tuple[str, list[str]]:
    reasons: list[str] = []
    allergens = analysis.allergens  # label -> declaracao
    if allergens:
        for label, decl in allergens.items():
            reasons.append(f"Alergenio '{label}' ({decl}).")
        return ALERG_POSSUI, reasons
    if analysis.ambiguous_ingredients:
        return ALERG_SUSPEITO, ["Ingredientes ambiguos podem esconder alergenios."]
    return ALERG_NENHUM, ["Nenhum dos 14 alergenios obrigatorios detetado."]


def assess(analysis: AnalysisResult) -> RiskAssessment:
    """Avaliacao de risco completa a partir da analise NLP (Fase 4)."""
    grade, g_reasons = grade_gluten(analysis)
    a_status, a_reasons = classify_allergens(analysis)
    return RiskAssessment(
        gluten_grade=grade,
        allergen_status=a_status,
        allergens=analysis.allergens,
        reasons=g_reasons + a_reasons,
    )
