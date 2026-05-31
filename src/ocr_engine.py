"""Wrapper Tesseract via pytesseract com configuracao do projeto.

Encapsula:
- localizacao do binario tesseract.exe (Windows);
- pasta tessdata local (`data/tessdata/`) com os packs pt+eng;
- escolha de PSM (Page Segmentation Mode) adequada para listas de
  ingredientes (geralmente PSM 6 - "uniform block of text").
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path

import numpy as np
import pytesseract
from PIL import Image


ROOT = Path(__file__).resolve().parent.parent
TESSDATA_DIR = ROOT / "data" / "tessdata"

# Localizacoes habituais do binario no Windows
_WINDOWS_CANDIDATES = [
    Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
    Path(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"),
    Path.home() / "AppData/Local/Programs/Tesseract-OCR/tesseract.exe",
]


def _locate_tesseract() -> str:
    """Encontra o executavel; configura pytesseract.tesseract_cmd."""
    found = shutil.which("tesseract")
    if found:
        return found
    for candidate in _WINDOWS_CANDIDATES:
        if candidate.exists():
            return str(candidate)
    raise RuntimeError(
        "Tesseract nao encontrado. Instale com:\n"
        "  winget install UB-Mannheim.TesseractOCR"
    )


_BIN = _locate_tesseract()
pytesseract.pytesseract.tesseract_cmd = _BIN

# Aponta tessdata para a pasta local do projeto. Usamos a env var em vez
# de --tessdata-dir porque shlex/pytesseract estraga paths Windows com
# espacos quando os passa pela linha de comandos.
os.environ["TESSDATA_PREFIX"] = str(TESSDATA_DIR)


def list_available_langs() -> list[str]:
    """Listas idiomas disponiveis na pasta tessdata local."""
    if not TESSDATA_DIR.exists():
        return []
    return sorted(p.stem for p in TESSDATA_DIR.glob("*.traineddata"))


def ocr(
    image: Image.Image | np.ndarray,
    lang: str = "por+eng",
    psm: int = 6,
    oem: int = 3,
    extra_config: str = "",
) -> str:
    """Executa OCR. Argumentos:

    - lang: idioma(s) separados por '+'. Default 'por+eng' (PT primario).
    - psm: Page Segmentation Mode. 6 = bloco uniforme de texto, ideal
      para listas de ingredientes. Outros uteis:
        3 = automatico (default Tesseract)
        4 = coluna unica de texto de tamanhos variaveis
        7 = linha unica
        11 = texto disperso
    - oem: OCR Engine Mode. 3 = default (LSTM + legacy).
    """
    if isinstance(image, np.ndarray):
        image = Image.fromarray(image)
    config = f"--psm {psm} --oem {oem} {extra_config}".strip()
    return pytesseract.image_to_string(image, lang=lang, config=config)


def ocr_with_confidence(
    image: Image.Image | np.ndarray,
    lang: str = "por+eng",
    psm: int = 6,
) -> tuple[str, float]:
    """Devolve (texto, confianca_media). Util para descartar OCRs duvidosos."""
    if isinstance(image, np.ndarray):
        image = Image.fromarray(image)
    config = f"--psm {psm}"
    data = pytesseract.image_to_data(
        image, lang=lang, config=config, output_type=pytesseract.Output.DICT
    )
    words: list[str] = []
    confs: list[int] = []
    for word, conf in zip(data["text"], data["conf"]):
        if word and word.strip():
            try:
                c = int(conf)
            except (ValueError, TypeError):
                continue
            if c >= 0:
                words.append(word)
                confs.append(c)
    text = " ".join(words)
    mean_conf = sum(confs) / len(confs) if confs else 0.0
    return text, mean_conf
