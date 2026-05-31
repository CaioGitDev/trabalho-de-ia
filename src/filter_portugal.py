"""Stream-filter the Open Food Facts CSV dump for products sold in Portugal.

Reads the gzipped dump directly (never materialises the full 9 GiB CSV).
Keeps only the columns relevant to the gluten/allergen detection task and
writes a clean UTF-8 CSV ready for analysis.
"""
from __future__ import annotations

import csv
import gzip
import sys
import time
from pathlib import Path

# Some OFF rows have very long concatenated text fields (>128 KiB default).
csv.field_size_limit(2**31 - 1)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
IN_FILE = DATA_DIR / "raw" / "openfoodfacts-products.csv.gz"
OUT_FILE = DATA_DIR / "processed" / "products_portugal.csv"

# Columns we want to keep from the dump (subset of ~200 available).
# Names follow the OFF CSV header.
KEEP_COLUMNS = [
    "code",
    "url",
    "product_name",
    "brands",
    "categories",
    "categories_tags",
    "categories_en",
    "ingredients_text",
    "ingredients_tags",
    "allergens",
    "allergens_en",
    "traces",
    "traces_tags",
    "traces_en",
    "labels",
    "labels_tags",
    "labels_en",
    "nutriscore_grade",
    "nutrition_grade_fr",
    "countries",
    "countries_tags",
    "countries_en",
    "main_category",
    "main_category_en",
]

# Country match: OFF stores countries as a comma-separated list of tags like
# "en:portugal,en:france". We match if any token is portugal-related.
PORTUGAL_MARKERS = (
    "en:portugal",
    "pt:portugal",
    "portugal",
    "portugais",
    "portugues",
)


def is_portugal(row: dict) -> bool:
    tags = (row.get("countries_tags") or "").lower()
    if "en:portugal" in tags:
        return True
    # Fallback to the free-text "countries" field for older records.
    countries = (row.get("countries") or "").lower()
    return any(marker in countries for marker in PORTUGAL_MARKERS)


def human(n: float) -> str:
    for unit in ("B", "KiB", "MiB", "GiB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TiB"


def filter_dump() -> Path:
    if not IN_FILE.exists():
        sys.exit(f"Input not found: {IN_FILE}. Run download_off.py first.")

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    in_size = IN_FILE.stat().st_size
    print(f"Reading {IN_FILE} ({human(in_size)} compressed)")
    print(f"Writing {OUT_FILE}")

    rows_in = 0
    rows_out = 0
    start = time.time()
    last_print = 0.0

    # OFF dump uses TAB as delimiter, not comma, despite the .csv extension.
    with gzip.open(IN_FILE, "rt", encoding="utf-8", errors="replace", newline="") as fin, \
         OUT_FILE.open("w", encoding="utf-8", newline="") as fout:
        reader = csv.DictReader(fin, delimiter="\t")
        available = [c for c in KEEP_COLUMNS if c in (reader.fieldnames or [])]
        missing = [c for c in KEEP_COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            print(f"Note: columns not found in dump and skipped: {missing}")

        writer = csv.DictWriter(fout, fieldnames=available, extrasaction="ignore")
        writer.writeheader()

        for row in reader:
            rows_in += 1
            if is_portugal(row):
                writer.writerow({k: row.get(k, "") for k in available})
                rows_out += 1

            now = time.time()
            if now - last_print >= 5.0:
                rate = rows_in / (now - start) if now > start else 0
                print(
                    f"  read {rows_in:>9,}  kept {rows_out:>7,}  "
                    f"({rate:,.0f} rows/s)",
                    flush=True,
                )
                last_print = now

    elapsed = time.time() - start
    print(
        f"\nDone in {elapsed:.0f}s. Read {rows_in:,} rows, kept {rows_out:,} "
        f"Portugal products."
    )
    print(f"Output: {OUT_FILE} ({human(OUT_FILE.stat().st_size)})")
    return OUT_FILE


if __name__ == "__main__":
    filter_dump()
