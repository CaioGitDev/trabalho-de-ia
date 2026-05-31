"""Limpeza de texto pos-OCR.

Erros tipicos do Tesseract sobre rotulos alimentares portugueses:
- quebra de linha no meio de palavras com hifen: "trig-\\no" -> "trigo"
- confusao de digitos vs letras: 0/O, 1/l, 5/S, 8/B
- espacos a mais ou de menos a volta de pontuacao
- ruido em margens (caracteres soltos, simbolos)
- acentos perdidos quando o pack PT nao consegue resolver

A funcao `clean_ocr_text` aplica todas as etapas em sequencia. As
funcoes individuais sao exportadas para permitir testes isolados.
"""
from __future__ import annotations

import re
import unicodedata


# Caracteres que aparecem frequentemente como ruido em margens
_NOISE_CHARS = re.compile(r"[|`~^¬{}\[\]<>©®™§¶]+")

# Quebra de linha hifenizada: "trig-\ngo" -> "trigo"
_HYPHEN_LINEBREAK = re.compile(r"-\s*\n\s*")

# Multiplos espacos / linhas em branco
_MULTI_WS = re.compile(r"[ \t]+")
_MULTI_NL = re.compile(r"\n{3,}")

# Confusoes digito<->letra DENTRO de palavras alfabeticas
# (so aplicamos quando a vizinhanca e alfabetica para nao destruir
# numeros legitimos como "70% cacau")
_DIGIT_TO_LETTER = {
    "0": "o",
    "1": "l",
    "5": "s",
    "8": "b",
}


def strip_noise(text: str) -> str:
    return _NOISE_CHARS.sub(" ", text)


def fix_hyphen_linebreaks(text: str) -> str:
    return _HYPHEN_LINEBREAK.sub("", text)


def normalize_whitespace(text: str) -> str:
    text = _MULTI_WS.sub(" ", text)
    text = _MULTI_NL.sub("\n\n", text)
    # Remove espacos a volta de pontuacao
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    text = re.sub(r"([,.;:])(?=\S)", r"\1 ", text)
    return text.strip()


def fix_digit_letter_confusion(text: str) -> str:
    """Substitui digitos por letras apenas quando rodeados por letras.
    Ex.: "tr1g0" -> "trigo", mas "70%" fica "70%".
    """
    def _sub(m: re.Match) -> str:
        word = m.group(0)
        # So aplica se a palavra tem alfa em ambos lados do digito
        out_chars: list[str] = []
        for i, ch in enumerate(word):
            if ch in _DIGIT_TO_LETTER:
                left = word[i - 1] if i > 0 else ""
                right = word[i + 1] if i + 1 < len(word) else ""
                if left.isalpha() and right.isalpha():
                    out_chars.append(_DIGIT_TO_LETTER[ch])
                    continue
            out_chars.append(ch)
        return "".join(out_chars)

    # Apanha sequencias mistas de letras + digitos (palavras de pelo menos 3 chars)
    return re.sub(r"\b[a-zA-Z0-9]{3,}\b", _sub, text)


def strip_short_garbage_lines(text: str, min_alpha: int = 3) -> str:
    """Remove linhas que sao essencialmente ruido (poucos chars alfabeticos)."""
    kept = []
    for line in text.splitlines():
        alpha_count = sum(c.isalpha() for c in line)
        if alpha_count >= min_alpha or not line.strip():
            kept.append(line)
    return "\n".join(kept)


def normalize_unicode(text: str) -> str:
    """Forma NFC + remove caracteres de controlo (excepto \\n)."""
    text = unicodedata.normalize("NFC", text)
    return "".join(ch for ch in text if ch == "\n" or not unicodedata.category(ch).startswith("C"))


def clean_ocr_text(raw: str) -> str:
    """Aplica todas as etapas em sequencia."""
    text = raw
    text = normalize_unicode(text)
    text = fix_hyphen_linebreaks(text)
    text = strip_noise(text)
    text = fix_digit_letter_confusion(text)
    text = normalize_whitespace(text)
    text = strip_short_garbage_lines(text)
    return text


# ----------------------------------------------------------------------
# Heuristica de extraccao da seccao "Ingredientes"
# ----------------------------------------------------------------------

_INGREDIENT_HEADERS = re.compile(
    r"(?im)^[ \t]*(ingredientes?|ingredients?|composici[oó]n|composi[çc][aã]o)\s*[:\.]?\s*"
)
# Seccoes que tipicamente terminam a lista de ingredientes
_END_MARKERS = re.compile(
    r"(?im)^[ \t]*(informa[çc][aã]o\s+nutricional|valores?\s+nutricionais|"
    r"conserva[çc][aã]o|consumir\s+preferencialmente|val(?:idade)?\.?|"
    r"lote|produzido\s+por|origem|peso\s+l[ií]quido)"
)


def extract_ingredients_section(text: str) -> str:
    """Tenta isolar so a lista de ingredientes do texto OCR completo.

    Devolve a string original se nao encontrar marcador "Ingredientes:".
    """
    m = _INGREDIENT_HEADERS.search(text)
    if not m:
        return text
    start = m.end()
    tail = text[start:]
    end = _END_MARKERS.search(tail)
    if end:
        tail = tail[: end.start()]
    return tail.strip()
