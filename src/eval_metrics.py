"""Avaliacao de classificadores REUTILIZANDO o codigo do professor.

`exemplos-de-aulas/260505_simplest_cifar_with_cnn/confusion_matrix2.py` traz
uma implementacao didatica (plain Python) de matriz de confusao e das metricas
Accuracy / Precision / Recall / F1 por classe. Este modulo importa essa
ferramenta e constroi, por cima dela, um resumo macro (media das classes) +
exatidao global, para comparar varios modelos de forma uniforme.

Mantem-se o uso do bloco de contagem do professor
(`count_times_when_at_the_same_index_...`) para construir a matriz, de modo a
demonstrar a reutilizacao efetiva do material das aulas (tambem servira a
Fase 8).
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_TEACHER_DIR = ROOT / "exemplos-de-aulas" / "260505_simplest_cifar_with_cnn"
if str(_TEACHER_DIR) not in sys.path:
    sys.path.insert(0, str(_TEACHER_DIR))

import confusion_matrix2 as cm2  # noqa: E402  (codigo do professor)


def build_confusion_matrix(actual: list, preds: list) -> dict[tuple[int, int], int]:
    """Matriz de confusao (dict) usando o bloco de contagem do professor,
    mas sem os prints da funcao original `cm2.confusion_matrix`.
    """
    labels = list(enumerate(sorted(set(actual))))
    cm: dict[tuple[int, int], int] = {}
    for i, row_label in labels:
        for j, col_label in labels:
            cm[(i, j)] = cm2.count_times_when_at_the_same_index_of_actual_and_preds_cols_the_stated_values_are_found(
                row_label, col_label, actual, preds
            )
    return cm


@dataclass
class EvalResult:
    accuracy: float                 # exatidao global
    macro_precision: float
    macro_recall: float
    macro_f1: float
    per_class: dict[str, dict[str, float]]
    cm_string: str


def _safe(fn, metrics, c) -> float:
    try:
        value, _ = fn(metrics, c)
        return float(value)
    except ZeroDivisionError:
        return 0.0


def evaluate(actual: list, preds: list) -> EvalResult:
    actual = list(actual)
    preds = list(preds)
    classes = sorted(set(actual))

    cm = build_confusion_matrix(actual, preds)
    metrics = cm2.confusion_matrix_metrics(cm, actual)

    per_class: dict[str, dict[str, float]] = {}
    for c in classes:
        per_class[c] = {
            "precision": _safe(cm2.confusion_matrix_precision_from_metrics_for_class, metrics, c),
            "recall": _safe(cm2.confusion_matrix_recall_from_metrics_for_class, metrics, c),
            "f1": _safe(cm2.confusion_matrix_f1_score_from_metrics_for_class, metrics, c),
        }

    n = len(actual)
    correct = sum(1 for a, p in zip(actual, preds) if a == p)
    accuracy = correct / n if n else 0.0

    k = len(classes)
    macro_p = sum(per_class[c]["precision"] for c in classes) / k
    macro_r = sum(per_class[c]["recall"] for c in classes) / k
    macro_f1 = sum(per_class[c]["f1"] for c in classes) / k

    return EvalResult(
        accuracy=accuracy,
        macro_precision=macro_p,
        macro_recall=macro_r,
        macro_f1=macro_f1,
        per_class=per_class,
        cm_string=cm2.confusion_matrix_to_string(cm, actual),
    )
