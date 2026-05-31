"""Fase 5 - Construcao do dataset rotulado e das features para os modelos.

Estrategia de aprendizagem (supervisao fraca / weak supervision):
- As REGRAS especializadas (`classifier_rules.classify_gluten_status_row`)
  geram o rotulo de cada produto a partir das suas tags OFF. Funcionam como
  "professor" automatico para gerar o dataset de treino.
- Cada produto e representado por um vetor binario "bag-of-tags": para cada
  tag de ingrediente do vocabulario, 1 se o produto a contem, 0 caso
  contrario (multi-hot). E a representacao tipica de texto em NLP/ML.

Depois (em `train_compare.py`) comparam-se Naive Bayes, Arvore de Decisao e
Random Forest a reproduzir a classificacao de gluten a partir desta
representacao. Sobre se a tarefa e "facil" demais ver a nota de limitacao no
README/Fase 8: o objetivo e DEMONSTRAR e COMPARAR os algoritmos lecionados.

So entram produtos COM lista de ingredientes (senao nao ha features) e com
rotulo em {sem, contem, suspeito} (descartado 'desconhecido').
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from classifier_rules import (
    STATUS_DESCONHECIDO,
    classify_gluten_status_row,
)

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "processed" / "products_portugal.csv"

# Uma tag entra no vocabulario se aparecer em pelo menos MIN_DF produtos.
MIN_DF = 10


@dataclass
class Dataset:
    X: np.ndarray              # (n_amostras, n_features) binario
    y: np.ndarray             # (n_amostras,) rotulos string
    feature_names: list[str]   # nomes das tags (colunas de X)
    classes: list[str]         # rotulos distintos ordenados

    def __str__(self) -> str:
        dist = ", ".join(f"{c}={int((self.y == c).sum())}" for c in self.classes)
        return (f"Dataset(amostras={self.X.shape[0]}, features={self.X.shape[1]}, "
                f"classes=[{dist}])")


def _tag_list(cell) -> list[str]:
    if cell is None or (isinstance(cell, float) and pd.isna(cell)):
        return []
    return [t.strip().lower() for t in str(cell).split(",") if t.strip()]


def build_dataset(data_file: Path = DATA_FILE, min_df: int = MIN_DF) -> Dataset:
    if not data_file.exists():
        raise SystemExit(f"Falta {data_file}. Corre src/filter_portugal.py primeiro.")

    df = pd.read_csv(data_file, low_memory=False)

    # rotulo via regras
    df["__label"] = df.apply(classify_gluten_status_row, axis=1)

    # so produtos com ingredientes e rotulo informativo
    mask = df["ingredients_tags"].notna() & (df["__label"] != STATUS_DESCONHECIDO)
    df = df[mask].reset_index(drop=True)

    tag_lists = df["ingredients_tags"].apply(_tag_list)

    # vocabulario por frequencia documental
    doc_freq: dict[str, int] = {}
    for tags in tag_lists:
        for t in set(tags):
            doc_freq[t] = doc_freq.get(t, 0) + 1
    vocab = sorted(t for t, n in doc_freq.items() if n >= min_df)
    index = {t: i for i, t in enumerate(vocab)}

    # matriz multi-hot
    X = np.zeros((len(df), len(vocab)), dtype=np.int8)
    for row_i, tags in enumerate(tag_lists):
        for t in set(tags):
            j = index.get(t)
            if j is not None:
                X[row_i, j] = 1

    y = df["__label"].to_numpy()
    classes = sorted(set(y.tolist()))
    return Dataset(X=X, y=y, feature_names=vocab, classes=classes)


if __name__ == "__main__":
    ds = build_dataset()
    print(ds)
    print(f"Exemplos de features: {ds.feature_names[:8]} ...")
