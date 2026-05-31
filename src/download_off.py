"""Download the Open Food Facts CSV dump (gzipped).

Streams the file to disk with progress reporting so it can be safely
interrupted/resumed manually.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import requests

DUMP_URL = "https://static.openfoodfacts.org/data/en.openfoodfacts.org.products.csv.gz"
USER_AGENT = "TrabalhoIIA-UFP/0.1 (academic project)"

OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
OUT_FILE = OUT_DIR / "openfoodfacts-products.csv.gz"

CHUNK = 1024 * 1024  # 1 MiB


def human(n: float) -> str:
    for unit in ("B", "KiB", "MiB", "GiB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TiB"


def download() -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    headers = {"User-Agent": USER_AGENT}

    with requests.get(DUMP_URL, headers=headers, stream=True, timeout=60) as r:
        r.raise_for_status()
        total = int(r.headers.get("Content-Length", 0))
        print(f"Downloading {DUMP_URL}")
        print(f"Expected size: {human(total)}")

        downloaded = 0
        start = time.time()
        last_print = 0.0
        with OUT_FILE.open("wb") as f:
            for chunk in r.iter_content(chunk_size=CHUNK):
                if not chunk:
                    continue
                f.write(chunk)
                downloaded += len(chunk)
                now = time.time()
                if now - last_print >= 2.0:
                    elapsed = now - start
                    speed = downloaded / elapsed if elapsed > 0 else 0
                    pct = (downloaded / total * 100) if total else 0
                    print(
                        f"  {human(downloaded)} / {human(total)} "
                        f"({pct:.1f}%) @ {human(speed)}/s",
                        flush=True,
                    )
                    last_print = now

    elapsed = time.time() - start
    print(f"\nDone in {elapsed:.0f}s -> {OUT_FILE}")
    return OUT_FILE


if __name__ == "__main__":
    try:
        download()
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        sys.exit(130)
