"""Fase 5 - Treino e comparacao de classificadores supervisionados.

Compara tres algoritmos lecionados a reproduzir a classificacao de gluten
(sem / contem / suspeito) a partir do "bag-of-tags" de ingredientes:

  - Naive Bayes (Bernoulli)  -> implementacao propria (`naive_bayes.py`)
  - Arvore de Decisao        -> scikit-learn
  - Random Forest            -> scikit-learn

Protocolo (conceitos das aulas):
  - train_test_split estratificado (treino/teste).
  - Validacao cruzada K-Fold estratificada (robustez da estimativa).
  - Avaliacao com a ferramenta do professor (`eval_metrics` -> confusion_matrix2):
    Accuracy / Precision / Recall / F1 + matriz de confusao.

Saidas:
  - data/processed/stats/08_model_comparison.csv
  - docs/figures/08_model_comparison.png
  - matrizes de confusao impressas para cada modelo.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.tree import DecisionTreeClassifier

from eval_metrics import evaluate
from features import build_dataset
from naive_bayes import BernoulliNaiveBayes

ROOT = Path(__file__).resolve().parent.parent
STATS_DIR = ROOT / "data" / "processed" / "stats"
FIG_DIR = ROOT / "docs" / "figures"
RANDOM_STATE = 42


def make_models() -> dict[str, object]:
    return {
        "Naive Bayes": BernoulliNaiveBayes(alpha=1.0),
        "Arvore de Decisao": DecisionTreeClassifier(
            criterion="entropy", random_state=RANDOM_STATE),
        "Random Forest": RandomForestClassifier(
            n_estimators=120, random_state=RANDOM_STATE, n_jobs=-1),
    }


def cross_validate(name: str, X: np.ndarray, y: np.ndarray, k: int = 5) -> tuple[float, float]:
    """Exatidao media e desvio-padrao por K-Fold estratificado."""
    skf = StratifiedKFold(n_splits=k, shuffle=True, random_state=RANDOM_STATE)
    accs: list[float] = []
    for train_idx, test_idx in skf.split(X, y):
        model = make_models()[name]
        model.fit(X[train_idx], y[train_idx])
        preds = model.predict(X[test_idx])
        accs.append(float(np.mean(preds == y[test_idx])))
    return float(np.mean(accs)), float(np.std(accs))


def main() -> None:
    print("A construir o dataset rotulado (regras -> rotulo, bag-of-tags -> features)...")
    ds = build_dataset()
    print(" ", ds)

    X_train, X_test, y_train, y_test = train_test_split(
        ds.X, ds.y, test_size=0.25, stratify=ds.y, random_state=RANDOM_STATE)
    print(f"  treino={X_train.shape[0]}  teste={X_test.shape[0]}\n")

    rows = []
    for name in make_models():
        print("=" * 72)
        print(f"MODELO: {name}")
        print("=" * 72)

        # validacao cruzada (so no treino)
        cv_mean, cv_std = cross_validate(name, X_train, y_train, k=5)
        print(f"K-Fold(5) exatidao: {cv_mean*100:.2f}% +/- {cv_std*100:.2f}%")

        # treino final + avaliacao no conjunto de teste retido
        model = make_models()[name]
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        ev = evaluate(list(y_test), list(preds))

        print(f"Teste: exatidao={ev.accuracy*100:.2f}%  "
              f"macro-F1={ev.macro_f1*100:.2f}%  "
              f"macro-precisao={ev.macro_precision*100:.2f}%  "
              f"macro-recall={ev.macro_recall*100:.2f}%")
        print("\nMatriz de confusao (linhas=real, colunas=previsto):")
        print(ev.cm_string)
        for c, m in ev.per_class.items():
            print(f"  {c:<12} P={m['precision']*100:5.1f}%  "
                  f"R={m['recall']*100:5.1f}%  F1={m['f1']*100:5.1f}%")
        print()

        rows.append({
            "modelo": name,
            "cv_acc_mean": round(cv_mean * 100, 2),
            "cv_acc_std": round(cv_std * 100, 2),
            "test_acc": round(ev.accuracy * 100, 2),
            "macro_precision": round(ev.macro_precision * 100, 2),
            "macro_recall": round(ev.macro_recall * 100, 2),
            "macro_f1": round(ev.macro_f1 * 100, 2),
        })

    df = pd.DataFrame(rows)
    STATS_DIR.mkdir(parents=True, exist_ok=True)
    out_csv = STATS_DIR / "08_model_comparison.csv"
    df.to_csv(out_csv, index=False, encoding="utf-8")

    print("=" * 72)
    print("RESUMO COMPARATIVO")
    print("=" * 72)
    print(df.to_string(index=False))

    # ---- figura comparativa ----
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(9, 5))
    x = np.arange(len(df))
    w = 0.38
    ax.bar(x - w / 2, df["test_acc"], w, label="Exatidao (teste)", color="#3b7dd8")
    ax.bar(x + w / 2, df["macro_f1"], w, label="Macro-F1 (teste)", color="#2ca02c")
    ax.set_xticks(x)
    ax.set_xticklabels(df["modelo"])
    ax.set_ylim(0, 105)
    ax.set_ylabel("%")
    ax.set_title("Fase 5 - Comparacao de classificadores (estado de gluten)")
    ax.legend()
    ax.grid(axis="y", linestyle=":", alpha=0.6)
    for i, (a, f) in enumerate(zip(df["test_acc"], df["macro_f1"])):
        ax.text(i - w / 2, a + 1, f"{a:.1f}", ha="center", fontsize=8)
        ax.text(i + w / 2, f + 1, f"{f:.1f}", ha="center", fontsize=8)
    out_png = FIG_DIR / "08_model_comparison.png"
    fig.savefig(out_png, dpi=120, bbox_inches="tight")
    plt.close(fig)

    print(f"\nSaidas:")
    print(f"  {out_csv.relative_to(ROOT)}")
    print(f"  {out_png.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
