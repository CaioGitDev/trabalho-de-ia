"""Pipeline OCR end-to-end: ficheiro de imagem -> texto limpo de ingredientes.

Combina os modulos do package:
    ocr_preprocess -> ocr_engine -> ocr_clean

Uso CLI:
    python src/ocr_pipeline.py <imagem.jpg>           # imprime texto
    python src/ocr_pipeline.py <imagem.jpg> --debug   # grava etapas intermedias
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

from ocr_clean import clean_ocr_text, extract_ingredients_section
from ocr_engine import ocr_with_confidence
from ocr_preprocess import (
    load_image,
    preprocess_pipeline,
    save_debug_steps,
)


@dataclass
class OCRResult:
    raw_text: str
    cleaned_text: str
    ingredients_only: str
    mean_confidence: float

    def __str__(self) -> str:
        return (
            f"OCRResult(conf={self.mean_confidence:.1f}%, "
            f"chars={len(self.cleaned_text)}, "
            f"ingredients_chars={len(self.ingredients_only)})"
        )


def run(image_path: str | Path, lang: str = "por+eng", psm: int = 6) -> OCRResult:
    img = load_image(image_path)
    processed = preprocess_pipeline(img)
    raw, conf = ocr_with_confidence(processed, lang=lang, psm=psm)
    cleaned = clean_ocr_text(raw)
    ingredients = extract_ingredients_section(cleaned)
    return OCRResult(
        raw_text=raw,
        cleaned_text=cleaned,
        ingredients_only=ingredients,
        mean_confidence=conf,
    )


def main() -> int:
    p = argparse.ArgumentParser(description="OCR de rotulos alimentares")
    p.add_argument("image", help="Caminho para a imagem do rotulo")
    p.add_argument("--lang", default="por+eng")
    p.add_argument("--psm", type=int, default=6)
    p.add_argument("--debug", action="store_true",
                   help="Grava as etapas intermedias em data/interim/")
    args = p.parse_args()

    img_path = Path(args.image)
    if not img_path.exists():
        print(f"Imagem nao encontrada: {img_path}", file=sys.stderr)
        return 2

    if args.debug:
        debug_dir = Path(__file__).resolve().parent.parent / "data" / "interim" / "ocr_debug"
        saved = save_debug_steps(img_path, debug_dir)
        print("Etapas intermedias gravadas:")
        for k, v in saved.items():
            print(f"  {k}: {v}")
        print()

    result = run(img_path, lang=args.lang, psm=args.psm)
    print(f"=== Confianca media: {result.mean_confidence:.1f}% ===")
    print("\n--- TEXTO LIMPO ---")
    print(result.cleaned_text)
    print("\n--- SECCAO INGREDIENTES (heuristica) ---")
    print(result.ingredients_only or "(nao detectada)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
