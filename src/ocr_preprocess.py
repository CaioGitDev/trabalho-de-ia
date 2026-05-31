"""Pre-processamento de imagens para OCR de rotulos alimentares.

A qualidade do OCR depende mais do pre-processamento do que do motor.
As tecnicas usadas seguem o que foi feito nas aulas em
`exemplos-de-aulas/260505_fashion_MNIST_app/app260505_with_more_pre_processing.py`
(grayscale, contraste, normalizacao), generalizadas para fotos de
rotulos: deskew (correccao de inclinacao), binarizacao adaptativa,
remocao de ruido e upscaling para texto pequeno.

Cada funcao recebe e devolve um numpy array em greyscale, excepto
`load_image` (le ficheiro) e `to_pil` (converte para PIL no final).
"""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from PIL import Image


def load_image(path: str | Path) -> np.ndarray:
    """Le imagem do disco em greyscale (uint8 2D)."""
    img = cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(f"Imagem nao legivel: {path}")
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


def upscale_if_small(img: np.ndarray, min_height: int = 1000) -> np.ndarray:
    """Tesseract trabalha melhor com texto de pelo menos 20-30 px de altura.
    Se a imagem for pequena, aumenta proporcionalmente.
    """
    h, w = img.shape[:2]
    if h >= min_height:
        return img
    scale = min_height / h
    new_size = (int(w * scale), int(h * scale))
    return cv2.resize(img, new_size, interpolation=cv2.INTER_CUBIC)


def denoise(img: np.ndarray) -> np.ndarray:
    """Reduz ruido preservando arestas (Non-Local Means)."""
    return cv2.fastNlMeansDenoising(img, h=10, templateWindowSize=7, searchWindowSize=21)


def increase_contrast(img: np.ndarray) -> np.ndarray:
    """CLAHE: equalizacao adaptativa de histograma. Melhor que equalize_hist
    para iluminacao nao-uniforme tipica de fotos de rotulos.
    """
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(img)


def deskew(img: np.ndarray) -> np.ndarray:
    """Corrige inclinacao do texto usando o angulo do minAreaRect dos pixeis
    nao-fundo. Robust para -45 a +45 graus.
    """
    # Inverte para que o texto fique branco sobre preto antes de calcular
    inv = cv2.bitwise_not(img)
    _, bw = cv2.threshold(inv, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    coords = np.column_stack(np.where(bw > 0))
    if coords.size == 0:
        return img
    angle = cv2.minAreaRect(coords)[-1]
    # minAreaRect devolve angulo em [-90, 0); normaliza para [-45, 45]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    # Nao roda por angulos minusculos (evita borrar)
    if abs(angle) < 0.5:
        return img
    h, w = img.shape[:2]
    M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
    return cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC,
                          borderMode=cv2.BORDER_REPLICATE)


def binarize(img: np.ndarray) -> np.ndarray:
    """Threshold adaptativo + Otsu. Devolve imagem preto/branco onde o
    texto fica preto sobre fundo branco (formato que o Tesseract espera).
    """
    _, bw = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    # Se o fundo ficou maioritariamente preto, inverte (texto escuro
    # sobre fundo claro e o esperado por Tesseract)
    if bw.mean() < 127:
        bw = cv2.bitwise_not(bw)
    return bw


def preprocess_pipeline(img: np.ndarray, do_deskew: bool = True) -> np.ndarray:
    """Pipeline completa, na ordem certa: upscale -> contrast -> denoise
    -> deskew -> binarize.
    """
    out = upscale_if_small(img)
    out = increase_contrast(out)
    out = denoise(out)
    if do_deskew:
        out = deskew(out)
    out = binarize(out)
    return out


def to_pil(img: np.ndarray) -> Image.Image:
    return Image.fromarray(img)


def save_debug_steps(src_path: str | Path, out_dir: str | Path) -> dict[str, Path]:
    """Grava cada etapa intermedia como PNG (uso em debug/relatorio)."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = Path(src_path).stem
    steps: dict[str, np.ndarray] = {}
    img = load_image(src_path)
    steps["00_grey"] = img
    steps["01_upscaled"] = upscale_if_small(img)
    steps["02_contrast"] = increase_contrast(steps["01_upscaled"])
    steps["03_denoise"] = denoise(steps["02_contrast"])
    steps["04_deskew"] = deskew(steps["03_denoise"])
    steps["05_binary"] = binarize(steps["04_deskew"])
    paths: dict[str, Path] = {}
    for name, arr in steps.items():
        p = out_dir / f"{stem}__{name}.png"
        cv2.imwrite(str(p), arr)
        paths[name] = p
    return paths
