"""Fase 4 - Processamento de Linguagem Natural sobre listas de ingredientes.

Recebe texto livre (vindo do OCR ou do campo `ingredients_text` do dataset)
e produz uma analise estruturada e canonica:

    normalizacao  ->  tokenizacao  ->  matching (exato + difuso)  ->  classificacao

Etapas (conforme objetivos da Fase 4 no `geral.md`):
- Normalizacao dos ingredientes (unicode, acentos, minusculas, espacos).
- Tokenizacao da lista (virgulas, ponto-e-virgula, parenteses, percentagens,
  separador "/" entre idiomas).
- Remocao de inconsistencias (ruido, numeros, codigos soltos).
- Identificacao de padroes alimentares (declaracoes "contem" / "pode conter
  tracos" / rotulo "sem gluten").
- Reconhecimento de ingredientes ambiguos -> assinala risco potencial.

O matching difuso usa as metricas de `nlp_distances` (Levenshtein/Jaccard),
reutilizando os conceitos de Estilometria/NLP das aulas, para tolerar os
erros tipicos do OCR ("Batato", "centeo", "emulionante").

O resultado (`AnalysisResult`) ja traz, por ingrediente, o estado de gluten
e a tag de alergenio canonica, ficando pronto para as Fases 5 (classificacao)
e 6 (explicabilidade).
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

from lexicon_pt import (
    AMBIGUOUS,
    GLUTEN,
    SAFE,
    LexEntry,
    LexPhrase,
    build_phrase_index,
    fold,
)
from nlp_distances import levenshtein_ratio
from knowledge_base import EU_ALLERGEN_TAGS


# Indice de frases construido uma vez (custo unico no import).
_PHRASES: list[LexPhrase] = build_phrase_index()

# Limiar de semelhanca para aceitar um match difuso (Levenshtein ratio).
FUZZY_THRESHOLD = 0.84
# Comprimento minimo (chars) de uma frase para ser elegivel a match difuso
# (evita que termos curtos como "ovo"/"sal" colem a ruido do OCR).
FUZZY_MIN_LEN = 5


# Marcadores de declaracao (forma folded, sem acentos)
_TRACE_MARKERS = ("pode conter", "podem conter", "pode conter tracos",
                  "tracos de", "vestigios de", "tracos", "vestigios")
_CONTAINS_MARKERS = ("contem", "contem:")
# Rotulo de ausencia certificada de gluten (texto livre)
_GLUTEN_FREE_RE = re.compile(
    r"sem\s+gluten|gluten\s*free|isento\s+de\s+gluten|0\s*%?\s*gluten|gluten\s+free"
)

# Cabecalho que marca o inicio da lista de ingredientes
_INGREDIENTS_HEADER_RE = re.compile(
    r"ingredientes?\s*:?|ingredients?\s*:?|composi[cç][aã]o\s*:?", re.IGNORECASE
)

# Declaracoes
DECL_INGREDIENT = "ingrediente"
DECL_CONTAINS = "contem"
DECL_TRACES = "tracos"


@dataclass
class IngredientMatch:
    """Um ingrediente reconhecido no texto."""
    raw: str                    # segmento original (apresentacao)
    term: str                   # termo canonico do lexico
    gluten: str                 # GLUTEN | AMBIGUOUS | SAFE
    allergen: str | None        # tag en: de alergenio EU, ou None
    allergen_label: str | None  # nome PT do alergenio, ou None
    tag: str | None             # tag canonica en: (knowledge_base)
    score: float                # confianca do match [0,1]
    method: str                 # "exato" | "difuso"
    declaration: str            # DECL_INGREDIENT | DECL_CONTAINS | DECL_TRACES


@dataclass
class AnalysisResult:
    matches: list[IngredientMatch] = field(default_factory=list)
    unknown_segments: list[str] = field(default_factory=list)
    gluten_free_label: bool = False

    # --- vistas convenientes (usadas pelas fases 5/6) ---
    @property
    def gluten_ingredients(self) -> list[IngredientMatch]:
        return [m for m in self.matches if m.gluten == GLUTEN]

    @property
    def ambiguous_ingredients(self) -> list[IngredientMatch]:
        return [m for m in self.matches if m.gluten == AMBIGUOUS]

    @property
    def allergens(self) -> dict[str, str]:
        """label de alergenio -> declaracao mais forte encontrada."""
        order = {DECL_TRACES: 0, DECL_CONTAINS: 1, DECL_INGREDIENT: 2}
        out: dict[str, str] = {}
        for m in self.matches:
            if not m.allergen_label:
                continue
            cur = out.get(m.allergen_label)
            if cur is None or order[m.declaration] > order[cur]:
                out[m.allergen_label] = m.declaration
        return out


# ----------------------------------------------------------------------
# Normalizacao
# ----------------------------------------------------------------------

def normalize_text(text: str) -> str:
    """Normalizacao de apresentacao: NFC, controla espacos, remove
    caracteres de controlo. Mantem acentos e maiusculas (para apresentacao).
    """
    text = unicodedata.normalize("NFC", text)
    text = "".join(c for c in text if c == "\n" or not unicodedata.category(c).startswith("C"))
    return text


_PERCENT_RE = re.compile(r"\(?\s*\d+[.,]?\d*\s*%\s*\)?")
_ADDITIVE_TAIL_RE = re.compile(r"[^a-zà-ÿ\s/(),;.]+", re.IGNORECASE)


# ----------------------------------------------------------------------
# Tokenizacao
# ----------------------------------------------------------------------

def _drop_header(text: str) -> str:
    """Remove o prefixo "Ingredientes:" se existir, mantendo o resto."""
    m = _INGREDIENTS_HEADER_RE.search(text)
    if m:
        return text[m.end():]
    return text


def _explode_parentheses(segment: str) -> list[str]:
    """Separa o conteudo de parenteses como sub-segmentos.

    "estabilizador (E450, E451)" -> ["estabilizador", "E450", "E451"]
    """
    parts: list[str] = []
    # conteudos entre parenteses
    inner = re.findall(r"\(([^()]*)\)", segment)
    outer = re.sub(r"\([^()]*\)", " ", segment)
    parts.append(outer)
    parts.extend(inner)
    return parts


def split_segments(text: str) -> list[str]:
    """Divide a lista de ingredientes em segmentos (um por ingrediente).

    Trata separadores de lista (',', ';', '.', quebra de linha) e o '/'
    usado entre versoes em idiomas diferentes; explode parenteses.
    """
    text = _drop_header(normalize_text(text))
    text = _PERCENT_RE.sub(" ", text)

    # separadores de topo: pontuacao de lista, "/" entre idiomas e as
    # conjuncoes "e"/"y"/"and" (que ligam ingredientes numa enumeracao).
    rough = re.split(r"[,;\n/]+|\.\s|\)\s*,?|\s+(?:e|y|and)\s+", text)
    segments: list[str] = []
    for chunk in rough:
        for sub in _explode_parentheses(chunk):
            sub = sub.strip(" .;:-*•[]")
            if sub:
                segments.append(sub)
    return segments


def _match_string(segment: str) -> str:
    """Versao folded de um segmento, limpa de numeros/codigos para matching."""
    f = fold(segment)
    f = _PERCENT_RE.sub(" ", f)
    # remove tokens puramente numericos ou aditivos (e471, b12, ...) e simbolos
    tokens = [t for t in re.split(r"[^a-z]+", f) if t and not t.isdigit()]
    tokens = [t for t in tokens if not (len(t) <= 4 and any(ch.isdigit() for ch in t))]
    return " ".join(tokens)


# ----------------------------------------------------------------------
# Matching contra o lexico
# ----------------------------------------------------------------------

def match_segment(seg_match: str) -> tuple[LexEntry, float, str] | None:
    """Devolve (entrada, score, metodo) do melhor match, ou None.

    1. Match exato (fronteira de palavra) -> escolhe a frase mais especifica
       (o indice ja vem ordenado por especificidade).
    2. Caso falhe, match difuso por janela de palavras via Levenshtein.
    """
    if not seg_match:
        return None
    padded = f" {seg_match} "

    # 1) exato (mais especifico primeiro)
    for ph in _PHRASES:
        if f" {ph.folded} " in padded:
            return ph.entry, 1.0, "exato"

    # 2) difuso
    words = seg_match.split()
    best: tuple[LexEntry, float, str] | None = None
    for ph in _PHRASES:
        if len(ph.folded) < FUZZY_MIN_LEN:
            continue
        wc = ph.word_count
        if wc > len(words):
            continue
        for i in range(len(words) - wc + 1):
            window = " ".join(words[i:i + wc])
            ratio = levenshtein_ratio(window, ph.folded)
            if ratio >= FUZZY_THRESHOLD and (best is None or ratio > best[1]):
                best = (ph.entry, ratio, "difuso")
    return best


# ----------------------------------------------------------------------
# Deteccao de declaracao (ingrediente / contem / tracos)
# ----------------------------------------------------------------------

def _declaration_for(seg_folded: str, current: str) -> str:
    """Atualiza o modo de declaracao com base em marcadores no segmento.

    Uma vez encontrado "pode conter tracos", o modo fixa-se em TRACOS para
    os segmentos seguintes (e o padrao tipico do rotulo).
    """
    if any(mk in seg_folded for mk in _TRACE_MARKERS):
        return DECL_TRACES
    if current == DECL_TRACES:
        return DECL_TRACES
    if any(mk in seg_folded for mk in _CONTAINS_MARKERS):
        return DECL_CONTAINS
    # "contem"/"tracos" sao seccoes: o modo persiste ate ao marcador seguinte
    if current == DECL_CONTAINS:
        return DECL_CONTAINS
    return DECL_INGREDIENT


# ----------------------------------------------------------------------
# Orquestracao
# ----------------------------------------------------------------------

def analyze_ingredients(text: str) -> AnalysisResult:
    """Analisa um texto de ingredientes e devolve a estrutura canonica."""
    result = AnalysisResult()
    if not text:
        return result

    result.gluten_free_label = bool(_GLUTEN_FREE_RE.search(fold(text)))

    declaration = DECL_INGREDIENT
    seen_terms: set[tuple[str, str]] = set()  # (term, declaration) p/ dedup

    for seg in split_segments(text):
        seg_folded = fold(seg)
        # segmento que e a alegacao "sem gluten" nao e um ingrediente:
        # ja foi captado em gluten_free_label e nao deve contar como gluten.
        if _GLUTEN_FREE_RE.search(seg_folded):
            continue
        declaration = _declaration_for(seg_folded, declaration)
        seg_match = _match_string(seg)

        hit = match_segment(seg_match)
        if hit is None:
            # so guardamos como "desconhecido" se tiver substancia alfabetica
            if sum(c.isalpha() for c in seg) >= 4:
                result.unknown_segments.append(seg.strip())
            continue

        entry, score, method = hit
        key = (entry.term, declaration)
        if key in seen_terms:
            continue
        seen_terms.add(key)

        result.matches.append(IngredientMatch(
            raw=seg.strip(),
            term=entry.term,
            gluten=entry.gluten,
            allergen=entry.allergen,
            allergen_label=EU_ALLERGEN_TAGS.get(entry.allergen) if entry.allergen else None,
            tag=entry.tag,
            score=score,
            method=method,
            declaration=declaration,
        ))

    return result


# Simbolos para apresentacao (reutilizados na Fase 6)
GLUTEN_SYMBOL = {GLUTEN: "X", AMBIGUOUS: "?", SAFE: "OK"}


def format_report(result: AnalysisResult) -> str:
    """Tabela legivel da analise (apoio a Fase 6/7; demo da Fase 4)."""
    lines = []
    if result.gluten_free_label:
        lines.append('Rotulo "sem gluten" detetado no texto.')
    lines.append(f"{'Ingrediente':<28} {'Gluten':<8} {'Alergenio':<22} {'Decl.':<11} Conf.")
    lines.append("-" * 78)
    for m in result.matches:
        lines.append(
            f"{m.term[:27]:<28} "
            f"{GLUTEN_SYMBOL[m.gluten]:<8} "
            f"{(m.allergen_label or '-')[:21]:<22} "
            f"{m.declaration:<11} "
            f"{m.score*100:5.0f}% ({m.method})"
        )
    if result.unknown_segments:
        lines.append("-" * 78)
        lines.append(f"Segmentos nao reconhecidos: {len(result.unknown_segments)}")
    return "\n".join(lines)
