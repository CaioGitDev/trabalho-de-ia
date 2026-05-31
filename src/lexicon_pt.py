"""Lexico de ingredientes em portugues -> categorias de risco.

A `knowledge_base.py` trabalha com a taxonomia normalizada do Open Food
Facts (tags `en:`), ideal para o dataset estruturado (campo
`ingredients_tags`). Mas o texto que sai do OCR vem em portugues corrido
("farinha de trigo", "amido modificado", "contem sulfitos"). Este modulo
e a *ponte*: associa termos PT (e variantes) a:

- `gluten`: estado relativo ao gluten -> "gluten" | "ambiguous" | "safe"
- `allergen`: tag `en:` de alergenio EU (ou None) -> reutiliza as chaves
  de `EU_ALLERGEN_TAGS`
- `tag`: tag canonica `en:` correspondente em `knowledge_base` (rastreio)

Assim a Fase 4 (NLP) produz, a partir de texto livre, a mesma informacao
canonica usada pelas Fases 5 (classificacao) e 6 (explicabilidade).
"""
from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field


def fold(text: str) -> str:
    """Normaliza para matching: minusculas, sem acentos, espacos colapsados.

    "Farinha de Trigo" -> "farinha de trigo"; "Açúcar" -> "acucar".
    Mantida aqui (e nao em nlp_ingredients) porque o lexico ja e indexado
    em forma folded.
    """
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return " ".join(text.split())


# Estados possiveis relativamente ao gluten
GLUTEN = "gluten"        # contem gluten por natureza
AMBIGUOUS = "ambiguous"  # origem nao declarada -> risco potencial
SAFE = "safe"            # sem gluten conhecido


@dataclass(frozen=True)
class LexEntry:
    """Uma entrada do lexico (um ingrediente/conceito e as suas variantes)."""
    term: str                       # forma canonica para apresentacao (PT)
    gluten: str                     # GLUTEN | AMBIGUOUS | SAFE
    allergen: str | None = None     # tag en: de alergenio EU, ou None
    tag: str | None = None          # tag en: canonica (knowledge_base)
    variants: tuple[str, ...] = field(default_factory=tuple)

    def all_terms(self) -> list[str]:
        return [self.term, *self.variants]


# ----------------------------------------------------------------------
# GLUTEN: cereais e derivados que contem gluten por natureza
# ----------------------------------------------------------------------
_GLUTEN_ENTRIES = [
    LexEntry("farinha de trigo", GLUTEN, "en:gluten", "en:wheat-flour",
             variants=("farinha de trigo integral", "farinha trigo")),
    LexEntry("trigo", GLUTEN, "en:gluten", "en:wheat",
             variants=("trigo duro", "trigo mole", "trigo rijo")),
    LexEntry("amido de trigo", GLUTEN, "en:gluten", "en:wheat-starch"),
    LexEntry("semola de trigo", GLUTEN, "en:gluten", "en:durum-wheat-semolina",
             variants=("semola",)),
    LexEntry("gluten de trigo", GLUTEN, "en:gluten", "en:wheat-gluten"),
    LexEntry("gluten", GLUTEN, "en:gluten", "en:gluten"),
    LexEntry("centeio", GLUTEN, "en:gluten", "en:rye",
             variants=("farinha de centeio",)),
    LexEntry("cevada", GLUTEN, "en:gluten", "en:barley",
             variants=("farinha de cevada",)),
    LexEntry("malte de cevada", GLUTEN, "en:gluten", "en:barley-malt",
             variants=("extrato de malte de cevada", "extrato de malte",
                       "malte",)),
    LexEntry("espelta", GLUTEN, "en:gluten", "en:spelt"),
    LexEntry("kamut", GLUTEN, "en:gluten", "en:kamut"),
    LexEntry("triticale", GLUTEN, "en:gluten", "en:triticale"),
    LexEntry("aveia", GLUTEN, "en:gluten", "en:oats",
             variants=("flocos de aveia", "farinha de aveia",
                       "farelo de aveia", "fibra de aveia")),
    LexEntry("couscous", GLUTEN, "en:gluten", "en:couscous",
             variants=("cuscuz",)),
    LexEntry("bulgur", GLUTEN, "en:gluten", "en:bulgur"),
    LexEntry("seitan", GLUTEN, "en:gluten", "en:seitan"),
    LexEntry("pao ralado", GLUTEN, "en:gluten", "en:breadcrumbs"),
]

# ----------------------------------------------------------------------
# AMBIGUOS: origem nao declarada -> assinalar risco potencial
# ----------------------------------------------------------------------
_AMBIGUOUS_ENTRIES = [
    LexEntry("amido modificado", AMBIGUOUS, None, "en:modified-starch"),
    LexEntry("amido", AMBIGUOUS, None, "en:starch",
             variants=("fecula",)),
    LexEntry("farinha", AMBIGUOUS, None, "en:flour"),
    LexEntry("cereais", AMBIGUOUS, None, "en:cereals",
             variants=("cereal", "extrato de cereais")),
    LexEntry("proteina vegetal", AMBIGUOUS, None, "en:vegetable-protein",
             variants=("proteina vegetal hidrolisada",
                       "proteina vegetal texturizada", "proteina vegetal texturada")),
    LexEntry("maltodextrina", AMBIGUOUS, None, "en:maltodextrin",
             variants=("maltodextrinas",)),
    LexEntry("dextrina", AMBIGUOUS, None, "en:dextrin",
             variants=("dextrinas",)),
    LexEntry("xarope de glucose", AMBIGUOUS, None, "en:glucose-syrup"),
    LexEntry("aroma", AMBIGUOUS, None, "en:flavouring",
             variants=("aromas", "aroma natural", "aromas naturais")),
    LexEntry("caramelo", AMBIGUOUS, None, "en:caramel",
             variants=("corante caramelo", "cor de caramelo")),
    LexEntry("espessante", AMBIGUOUS, None, "en:thickener"),
    LexEntry("estabilizador", AMBIGUOUS, None, "en:stabiliser",
             variants=("estabilizante",)),
    LexEntry("fibra vegetal", AMBIGUOUS, None, "en:vegetable-fibre",
             variants=("fibra",)),
]

# ----------------------------------------------------------------------
# SAFE: ingredientes comuns claramente sem gluten (desambiguam termos
# ambiguos quando a origem ESTA declarada, ex.: "amido de milho")
# ----------------------------------------------------------------------
_SAFE_ENTRIES = [
    LexEntry("amido de milho", SAFE, None, "en:corn-starch",
             variants=("amido de batata", "fecula de batata",
                       "amido de arroz", "amido de tapioca")),
    LexEntry("milho", SAFE, None, "en:corn",
             variants=("farinha de milho", "semola de milho")),
    LexEntry("arroz", SAFE, None, "en:rice", variants=("farinha de arroz",)),
    LexEntry("batata", SAFE, None, "en:potato",
             variants=("batata desidratada", "fecula",)),
    LexEntry("acucar", SAFE, None, "en:sugar"),
    LexEntry("sal", SAFE, None, "en:salt", variants=("sal marinho",)),
    LexEntry("agua", SAFE, None, "en:water"),
    LexEntry("oleo", SAFE, None, "en:oil",
             variants=("oleo de girassol", "oleo de canola", "oleo de coco",
                       "oleo de algodao", "azeite", "oleo de palma")),
    LexEntry("tomate", SAFE, None, "en:tomato"),
    LexEntry("acido citrico", SAFE, None, "en:e330",
             variants=("regulador de acidez",)),
]

# ----------------------------------------------------------------------
# ALERGENIOS EU (Anexo II Reg. 1169/2011) -- termos PT.
# Cada um traz a tag en: usada como chave em EU_ALLERGEN_TAGS.
# O estado de gluten e atribuido em conformidade (cereais com gluten ->
# GLUTEN; os restantes alergenios sao, quanto a gluten, SAFE).
# ----------------------------------------------------------------------
_ALLERGEN_ENTRIES = [
    # Leite
    LexEntry("leite", SAFE, "en:milk", "en:milk",
             variants=("leite gordo", "leite em po", "leite gordo em po",
                       "lactose", "soro de leite", "soro de leite em po",
                       "caseina", "manteiga", "nata", "natas", "queijo",
                       "mozzarella", "fermentos lacticos")),
    # Ovos
    LexEntry("ovo", SAFE, "en:eggs", "en:eggs",
             variants=("ovos", "gema de ovo", "clara de ovo", "gema",
                       "clara", "ovalbumina", "ovo em po")),
    # Soja
    LexEntry("soja", SAFE, "en:soybeans", "en:soybeans",
             variants=("lecitina de soja", "proteina de soja",
                       "oleo de soja", "molho de soja")),
    # Amendoim
    LexEntry("amendoim", SAFE, "en:peanuts", "en:peanuts",
             variants=("oleo de amendoim", "manteiga de amendoim")),
    # Frutos de casca rija
    LexEntry("frutos de casca rija", SAFE, "en:nuts", "en:nuts",
             variants=("frutos secos", "amendoa", "amendoas", "avela",
                       "avelas", "noz", "nozes", "caju", "castanha de caju",
                       "pistacio", "pistacios", "noz pecan", "macadamia",
                       "castanha")),
    # Peixe
    LexEntry("peixe", SAFE, "en:fish", "en:fish",
             variants=("atum", "bacalhau", "salmao", "anchova", "sardinha")),
    # Crustaceos
    LexEntry("crustaceos", SAFE, "en:crustaceans", "en:crustaceans",
             variants=("camarao", "gambas", "lagosta", "caranguejo",
                       "lavagante")),
    # Moluscos
    LexEntry("moluscos", SAFE, "en:molluscs", "en:molluscs",
             variants=("mexilhao", "ameijoa", "lula", "polvo", "berbigao",
                       "vieira")),
    # Aipo
    LexEntry("aipo", SAFE, "en:celery", "en:celery"),
    # Mostarda
    LexEntry("mostarda", SAFE, "en:mustard", "en:mustard"),
    # Sesamo
    LexEntry("sesamo", SAFE, "en:sesame-seeds", "en:sesame-seeds",
             variants=("sementes de sesamo", "tahini")),
    # Tremoco
    LexEntry("tremoco", SAFE, "en:lupin", "en:lupin",
             variants=("farinha de tremoco",)),
    # Sulfitos / dioxido de enxofre
    LexEntry("sulfitos", SAFE, "en:sulphur-dioxide-and-sulphites",
             "en:sulphur-dioxide-and-sulphites",
             variants=("dioxido de enxofre", "anidrido sulfuroso",
                       "metabissulfito", "sulfito")),
]


# Lexico completo (ordem irrelevante; o matcher ordena por especificidade)
LEXICON: list[LexEntry] = (
    _GLUTEN_ENTRIES + _AMBIGUOUS_ENTRIES + _SAFE_ENTRIES + _ALLERGEN_ENTRIES
)


@dataclass(frozen=True)
class LexPhrase:
    """Uma frase pesquisavel (forma folded) ligada a sua entrada."""
    folded: str
    word_count: int
    entry: LexEntry


def build_phrase_index() -> list[LexPhrase]:
    """Expande o lexico numa lista de frases folded, ordenadas da mais
    especifica (mais palavras / mais longa) para a menos especifica.

    A ordenacao garante que "farinha de trigo" e testada antes de "trigo"
    e que "amido de milho" (SAFE) ganha a "amido" (AMBIGUOUS).
    """
    phrases: list[LexPhrase] = []
    seen: set[str] = set()
    for entry in LEXICON:
        for term in entry.all_terms():
            f = fold(term)
            if not f or f in seen:
                continue
            seen.add(f)
            phrases.append(LexPhrase(f, len(f.split()), entry))
    phrases.sort(key=lambda p: (p.word_count, len(p.folded)), reverse=True)
    return phrases


# Palavras de ligacao/ruido a ignorar na tokenizacao
STOPWORDS_PT: frozenset[str] = frozenset({
    "de", "do", "da", "dos", "das", "e", "em", "com", "ou", "a", "o",
    "as", "os", "para", "por", "no", "na", "ao", "y", "and", "of",
})
