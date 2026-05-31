"""Metricas de distancia e semelhanca textual (implementacao em plain Python).

Reutiliza conceitos lecionados nas aulas de Estilometria / NLP
(ver `exemplos-de-aulas/sumarios-de-aulas.txt`, semanas de 2026-03-17 e
2026-03-24): distancias de Levenshtein/Hamming e indices de conjunto
(Jaccard, coeficiente de sobreposicao).

No projeto sao usadas para *matching difuso* entre os tokens que saem do
OCR (frequentemente com erros: "Batato", "centeo", "glicno") e os termos
canonicos do lexico de ingredientes. Implementadas sem dependencias
externas para manter o codigo proximo do que foi demonstrado em aula.
"""
from __future__ import annotations


def levenshtein(a: str, b: str) -> int:
    """Distancia de edicao (Levenshtein): numero minimo de insercoes,
    remocoes ou substituicoes para transformar `a` em `b`.

    Implementacao classica por programacao dinamica com duas linhas
    (espaco O(min(len)), tempo O(len_a * len_b)).
    """
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)

    # Garante que `b` e a string mais curta para minimizar memoria.
    if len(b) > len(a):
        a, b = b, a

    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        current = [i]
        for j, cb in enumerate(b, start=1):
            cost = 0 if ca == cb else 1
            current.append(min(
                previous[j] + 1,        # remocao
                current[j - 1] + 1,     # insercao
                previous[j - 1] + cost,  # substituicao
            ))
        previous = current
    return previous[-1]


def levenshtein_ratio(a: str, b: str) -> float:
    """Semelhanca normalizada em [0, 1] derivada da distancia de Levenshtein.

    1.0 = strings iguais; 0.0 = nada em comum. Usada como score de
    confianca do matching difuso de tokens OCR.
    """
    if not a and not b:
        return 1.0
    dist = levenshtein(a, b)
    return 1.0 - dist / max(len(a), len(b))


def hamming(a: str, b: str) -> int:
    """Distancia de Hamming: nº de posicoes diferentes (strings de igual
    comprimento). Levanta ValueError caso contrario.
    """
    if len(a) != len(b):
        raise ValueError("Hamming exige strings do mesmo comprimento")
    return sum(c1 != c2 for c1, c2 in zip(a, b))


def _as_set(x) -> set:
    return x if isinstance(x, set) else set(x)


def jaccard_index(a, b) -> float:
    """Indice de Jaccard entre dois conjuntos: |A ∩ B| / |A ∪ B|.

    Aceita conjuntos ou iteraveis (ex.: conjuntos de tokens/n-gramas).
    """
    sa, sb = _as_set(a), _as_set(b)
    if not sa and not sb:
        return 1.0
    union = sa | sb
    if not union:
        return 0.0
    return len(sa & sb) / len(union)


def jaccard_distance(a, b) -> float:
    """Distancia de Jaccard = 1 - indice de Jaccard."""
    return 1.0 - jaccard_index(a, b)


def overlap_coefficient(a, b) -> float:
    """Coeficiente de sobreposicao: |A ∩ B| / min(|A|, |B|)."""
    sa, sb = _as_set(a), _as_set(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / min(len(sa), len(sb))


def char_ngrams(text: str, n: int = 2) -> set[str]:
    """Conjunto de n-gramas de caracteres (uteis para Jaccard textual)."""
    text = text.replace(" ", "")
    if len(text) < n:
        return {text} if text else set()
    return {text[i:i + n] for i in range(len(text) - n + 1)}
