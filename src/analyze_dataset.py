"""Analise estatistica do dataset Open Food Facts (subset Portugal).

Cumpre a "Fase 2 / Requisitos de Avaliacao do Dataset" do enunciado:
- Numero total de produtos analisados
- Numero de categorias alimentares
- Frequencia dos alergenios
- Frequencia dos ingredientes associados ao gluten
- Percentagem de produtos sem gluten / com gluten / suspeitos / desconhecidos
- Percentagem de produtos com ingredientes ambiguos

Saidas:
- Tabelas impressas + gravadas em data/processed/stats/*.csv
- Graficos PNG em docs/figures/
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # headless: nao tenta abrir janela
import matplotlib.pyplot as plt
import pandas as pd

from knowledge_base import (
    AMBIGUOUS_TAGS,
    EU_ALLERGEN_TAGS,
    GLUTEN_TAGS,
)
# Fonte unica da regra de estado de gluten (Fase 5 formalizou-a aqui).
from classifier_rules import classify_gluten_status_row as classify_gluten_status


ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "processed" / "products_portugal.csv"
STATS_DIR = ROOT / "data" / "processed" / "stats"
FIG_DIR = ROOT / "docs" / "figures"


def explode_tags(series: pd.Series) -> pd.Series:
    """Expande uma coluna de tags separadas por virgula numa serie longa."""
    return (
        series.dropna()
        .astype(str)
        .str.lower()
        .str.split(",")
        .explode()
        .str.strip()
    )


def save_table(df: pd.DataFrame, name: str) -> None:
    STATS_DIR.mkdir(parents=True, exist_ok=True)
    path = STATS_DIR / f"{name}.csv"
    df.to_csv(path, index=False, encoding="utf-8")
    print(f"  > {path.relative_to(ROOT)}")


def save_figure(fig, name: str) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    path = FIG_DIR / f"{name}.png"
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print(f"  > {path.relative_to(ROOT)}")


def bar_chart(series: pd.Series, title: str, xlabel: str, name: str, color="#3b7dd8"):
    fig, ax = plt.subplots(figsize=(9, max(3, 0.35 * len(series))))
    series[::-1].plot.barh(ax=ax, color=color)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.grid(axis="x", linestyle=":", alpha=0.6)
    save_figure(fig, name)


def pie_chart(series: pd.Series, title: str, name: str):
    fig, ax = plt.subplots(figsize=(7, 7))
    colors = ["#2ca02c", "#d62728", "#ff7f0e", "#7f7f7f"]
    ax.pie(
        series.values,
        labels=[f"{i}\n({v:,})" for i, v in series.items()],
        autopct="%1.1f%%",
        startangle=90,
        colors=colors[: len(series)],
    )
    ax.set_title(title)
    save_figure(fig, name)


def section(title: str) -> None:
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def main() -> None:
    if not DATA_FILE.exists():
        raise SystemExit(f"Falta {DATA_FILE}. Corre src/filter_portugal.py primeiro.")

    print(f"A ler {DATA_FILE} ...")
    df = pd.read_csv(DATA_FILE, low_memory=False)
    n_total = len(df)

    # ---------------- 1. Cobertura geral ----------------
    section("1. COBERTURA GERAL DO DATASET")
    coverage = (
        df.notna().sum().sort_values(ascending=False)
        .rename("nao_nulos").to_frame()
        .assign(pct=lambda d: (d["nao_nulos"] / n_total * 100).round(1))
    )
    print(f"Total de produtos (Portugal): {n_total:,}")
    print(coverage.head(15).to_string())
    save_table(coverage.reset_index().rename(columns={"index": "coluna"}), "01_coverage")

    fig, ax = plt.subplots(figsize=(9, 6))
    coverage["pct"].head(15)[::-1].plot.barh(ax=ax, color="#3b7dd8")
    ax.set_title(f"Cobertura das colunas (n={n_total:,})")
    ax.set_xlabel("% de produtos com valor nao-nulo")
    ax.grid(axis="x", linestyle=":", alpha=0.6)
    save_figure(fig, "01_coverage")

    # ---------------- 2. Categorias alimentares ----------------
    section("2. CATEGORIAS ALIMENTARES")
    cats = explode_tags(df["main_category_en"])
    cat_counts = cats.value_counts()
    print(f"Numero de categorias distintas (main_category_en): {cat_counts.size:,}")
    print(f"\nTop 15 categorias:")
    print(cat_counts.head(15).to_string())
    save_table(cat_counts.head(50).rename_axis("categoria").reset_index(name="n"), "02_categorias_top50")
    bar_chart(cat_counts.head(15), "Top 15 categorias alimentares (PT)", "Numero de produtos", "02_categorias_top15", color="#5b8def")

    # ---------------- 3. Frequencia de alergenios (Anexo II) ----------------
    section("3. FREQUENCIA DE ALERGENIOS")
    allergens = explode_tags(df["allergens"])
    allergen_counts = allergens.value_counts()
    rows = []
    for tag, label in EU_ALLERGEN_TAGS.items():
        n = int(allergen_counts.get(tag, 0))
        rows.append({"tag": tag, "alergenio": label, "n_produtos": n, "pct": round(n / n_total * 100, 2)})
    df_allergens = pd.DataFrame(rows).sort_values("n_produtos", ascending=False)
    print(df_allergens.to_string(index=False))
    save_table(df_allergens, "03_alergenios_eu14")

    s = df_allergens.set_index("alergenio")["n_produtos"]
    bar_chart(s, "Frequencia dos 14 alergenios obrigatorios (UE)", "Numero de produtos", "03_alergenios_eu14", color="#d62728")

    # ---------------- 4. Ingredientes associados ao gluten ----------------
    section("4. INGREDIENTES ASSOCIADOS AO GLUTEN")
    ing = explode_tags(df["ingredients_tags"])
    ing_counts = ing.value_counts()

    gluten_rows = []
    for tag in GLUTEN_TAGS:
        n = int(ing_counts.get(tag, 0))
        if n > 0:
            gluten_rows.append({"tag": tag, "n_produtos": n})
    df_gluten = pd.DataFrame(gluten_rows).sort_values("n_produtos", ascending=False)
    print(f"Tags de gluten conhecidas: {len(GLUTEN_TAGS)}  |  detectadas no dataset: {len(df_gluten)}")
    print(df_gluten.head(20).to_string(index=False))
    save_table(df_gluten, "04_ingredientes_gluten")

    bar_chart(
        df_gluten.head(15).set_index("tag")["n_produtos"],
        "Top 15 ingredientes contendo gluten (PT)",
        "Numero de produtos",
        "04_ingredientes_gluten_top15",
        color="#d62728",
    )

    # ---------------- 5. Ingredientes ambiguos ----------------
    section("5. INGREDIENTES AMBIGUOS")
    amb_rows = []
    for tag in AMBIGUOUS_TAGS:
        n = int(ing_counts.get(tag, 0))
        if n > 0:
            amb_rows.append({"tag": tag, "n_produtos": n})
    df_amb = pd.DataFrame(amb_rows).sort_values("n_produtos", ascending=False)
    print(f"Tags ambiguas conhecidas: {len(AMBIGUOUS_TAGS)}  |  detectadas no dataset: {len(df_amb)}")
    print(df_amb.head(20).to_string(index=False))
    save_table(df_amb, "05_ingredientes_ambiguos")

    bar_chart(
        df_amb.head(15).set_index("tag")["n_produtos"],
        "Top 15 ingredientes ambiguos (origem nao declarada)",
        "Numero de produtos",
        "05_ingredientes_ambiguos_top15",
        color="#ff7f0e",
    )

    # ---------------- 6. Classificacao por estado de gluten ----------------
    section("6. ESTADO RELATIVO AO GLUTEN")
    df["gluten_status"] = df.apply(classify_gluten_status, axis=1)
    status_counts = df["gluten_status"].value_counts()
    status_pct = (status_counts / n_total * 100).round(2)
    df_status = pd.DataFrame({"n_produtos": status_counts, "pct": status_pct})
    df_status = df_status.reindex(["sem", "contem", "suspeito", "desconhecido"]).fillna(0).astype({"n_produtos": int})
    print(df_status.to_string())
    save_table(df_status.rename_axis("estado").reset_index(), "06_gluten_status")

    pie_chart(df_status["n_produtos"], "Distribuicao do estado de gluten (n={:,})".format(n_total), "06_gluten_status_pie")

    # ---------------- 7. Nutri-score ----------------
    section("7. DISTRIBUICAO NUTRI-SCORE")
    ns = df["nutriscore_grade"].dropna().str.lower()
    ns_valid = ns[ns.isin(list("abcde"))]
    ns_counts = ns_valid.value_counts().reindex(list("abcde")).fillna(0).astype(int)
    print(f"Produtos com nutri-score valido (a-e): {ns_valid.size:,} / {n_total:,}")
    print(ns_counts.to_string())
    save_table(ns_counts.rename_axis("grade").reset_index(name="n"), "07_nutriscore")

    fig, ax = plt.subplots(figsize=(7, 4))
    ns_colors = ["#1a8a3f", "#7ab851", "#f4c419", "#ee7723", "#e2241b"]
    ax.bar(ns_counts.index.str.upper(), ns_counts.values, color=ns_colors)
    ax.set_title("Distribuicao Nutri-Score (produtos PT)")
    ax.set_ylabel("Numero de produtos")
    ax.grid(axis="y", linestyle=":", alpha=0.6)
    save_figure(fig, "07_nutriscore")

    # ---------------- 8. Resumo final ----------------
    section("8. RESUMO EXECUTIVO")
    sem = df_status.loc["sem", "n_produtos"]
    contem = df_status.loc["contem", "n_produtos"]
    suspeito = df_status.loc["suspeito", "n_produtos"]
    desc = df_status.loc["desconhecido", "n_produtos"]
    print(f"Total de produtos PT analisados ......... {n_total:,}")
    print(f"Numero de categorias alimentares ........ {cat_counts.size:,}")
    print(f"Produtos com lista de ingredientes ...... {df['ingredients_tags'].notna().sum():,}  ({df['ingredients_tags'].notna().mean()*100:.1f}%)")
    print(f"Produtos com alergenios declarados ...... {df['allergens'].notna().sum():,}  ({df['allergens'].notna().mean()*100:.1f}%)")
    print()
    print("Estado relativo ao gluten:")
    print(f"  Sem gluten ...........  {sem:>6,}  ({sem/n_total*100:5.1f}%)")
    print(f"  Contem gluten ........  {contem:>6,}  ({contem/n_total*100:5.1f}%)")
    print(f"  Suspeito (ambiguos)... {suspeito:>6,}  ({suspeito/n_total*100:5.1f}%)")
    print(f"  Desconhecido .........  {desc:>6,}  ({desc/n_total*100:5.1f}%)")
    print()
    print(f"Saidas:")
    print(f"  Tabelas CSV: {STATS_DIR.relative_to(ROOT)}/")
    print(f"  Graficos PNG: {FIG_DIR.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
