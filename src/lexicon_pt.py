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
# (variantes incluem termos EN/FR: rotulos OFF aparecem em varios idiomas)
# ----------------------------------------------------------------------
_GLUTEN_ENTRIES = [
    LexEntry("farinha de trigo", GLUTEN, "en:gluten", "en:wheat-flour",
             variants=("farinha de trigo integral", "farinha trigo",
                       "wheat flour", "farine de ble")),
    LexEntry("trigo", GLUTEN, "en:gluten", "en:wheat",
             variants=("trigo duro", "trigo mole", "trigo rijo",
                       "wheat", "durum wheat", "whole wheat", "ble", "froment")),
    LexEntry("amido de trigo", GLUTEN, "en:gluten", "en:wheat-starch",
             variants=("wheat starch", "amidon de ble")),
    LexEntry("semola de trigo", GLUTEN, "en:gluten", "en:durum-wheat-semolina",
             variants=("semola", "semolina", "semoule", "semoule de ble")),
    LexEntry("gluten de trigo", GLUTEN, "en:gluten", "en:wheat-gluten",
             variants=("wheat gluten", "gluten de ble")),
    LexEntry("gluten", GLUTEN, "en:gluten", "en:gluten"),
    LexEntry("centeio", GLUTEN, "en:gluten", "en:rye",
             variants=("farinha de centeio", "rye", "rye flour", "seigle")),
    LexEntry("cevada", GLUTEN, "en:gluten", "en:barley",
             variants=("farinha de cevada", "barley", "orge")),
    LexEntry("malte de cevada", GLUTEN, "en:gluten", "en:barley-malt",
             variants=("extrato de malte de cevada", "extrato de malte",
                       "malte", "malt", "barley malt", "malt extract",
                       "malte d orge", "extrait de malt")),
    LexEntry("espelta", GLUTEN, "en:gluten", "en:spelt",
             variants=("spelt", "epeautre")),
    LexEntry("kamut", GLUTEN, "en:gluten", "en:kamut"),
    LexEntry("triticale", GLUTEN, "en:gluten", "en:triticale"),
    LexEntry("aveia", GLUTEN, "en:gluten", "en:oats",
             variants=("flocos de aveia", "farinha de aveia",
                       "farelo de aveia", "fibra de aveia",
                       "oat", "oats", "rolled oats", "avoine",
                       "flocons d avoine")),
    LexEntry("couscous", GLUTEN, "en:gluten", "en:couscous",
             variants=("cuscuz",)),
    LexEntry("bulgur", GLUTEN, "en:gluten", "en:bulgur"),
    LexEntry("seitan", GLUTEN, "en:gluten", "en:seitan"),
    LexEntry("pao ralado", GLUTEN, "en:gluten", "en:breadcrumbs",
             variants=("breadcrumbs", "chapelure")),
]

# ----------------------------------------------------------------------
# AMBIGUOS: origem nao declarada -> assinalar risco potencial
# ----------------------------------------------------------------------
_AMBIGUOUS_ENTRIES = [
    LexEntry("amido modificado", AMBIGUOUS, None, "en:modified-starch",
             variants=("modified starch", "amidon modifie")),
    LexEntry("amido", AMBIGUOUS, None, "en:starch",
             variants=("fecula", "starch", "amidon")),
    LexEntry("farinha", AMBIGUOUS, None, "en:flour",
             variants=("flour", "farine")),
    LexEntry("cereais", AMBIGUOUS, None, "en:cereals",
             variants=("cereal", "extrato de cereais", "cereals",
                       "cereales", "cereal extract")),
    LexEntry("proteina vegetal", AMBIGUOUS, None, "en:vegetable-protein",
             variants=("proteina vegetal hidrolisada",
                       "proteina vegetal texturizada", "proteina vegetal texturada",
                       "vegetable protein", "hydrolysed vegetable protein",
                       "proteine vegetale")),
    LexEntry("maltodextrina", AMBIGUOUS, None, "en:maltodextrin",
             variants=("maltodextrinas", "maltodextrin", "maltodextrine")),
    LexEntry("dextrina", AMBIGUOUS, None, "en:dextrin",
             variants=("dextrinas", "dextrin", "dextrine")),
    LexEntry("xarope de glucose", AMBIGUOUS, None, "en:glucose-syrup",
             variants=("glucose syrup", "sirop de glucose")),
    LexEntry("aroma", AMBIGUOUS, None, "en:flavouring",
             variants=("aromas", "aroma natural", "aromas naturais",
                       "flavouring", "flavour", "natural flavouring",
                       "arome", "arome naturel")),
    LexEntry("caramelo", AMBIGUOUS, None, "en:caramel",
             variants=("corante caramelo", "cor de caramelo", "caramel")),
    LexEntry("espessante", AMBIGUOUS, None, "en:thickener",
             variants=("thickener", "epaississant")),
    LexEntry("estabilizador", AMBIGUOUS, None, "en:stabiliser",
             variants=("estabilizante", "stabiliser", "stabilizer", "stabilisant")),
    LexEntry("fibra vegetal", AMBIGUOUS, None, "en:vegetable-fibre",
             variants=("fibra", "fibre", "vegetable fibre")),
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
                       "mozzarella", "fermentos lacticos",
                       # EN/FR
                       "milk", "milk powder", "whole milk", "skimmed milk",
                       "whey", "whey powder", "casein", "butter", "cream",
                       "cheese", "lait", "lactoserum", "beurre", "creme",
                       "fromage")),
    # Ovos
    LexEntry("ovo", SAFE, "en:eggs", "en:eggs",
             variants=("ovos", "gema de ovo", "clara de ovo", "gema",
                       "clara", "ovalbumina", "ovo em po",
                       "egg", "eggs", "egg white", "egg yolk", "whole egg",
                       "oeuf", "oeufs", "blanc d oeuf", "jaune d oeuf")),
    # Soja
    LexEntry("soja", SAFE, "en:soybeans", "en:soybeans",
             variants=("lecitina de soja", "proteina de soja",
                       "oleo de soja", "molho de soja",
                       "soy", "soya", "soybean", "soybeans", "soy lecithin",
                       "soja lecithin", "lecithine de soja")),
    # Amendoim
    LexEntry("amendoim", SAFE, "en:peanuts", "en:peanuts",
             variants=("oleo de amendoim", "manteiga de amendoim",
                       "peanut", "peanuts", "arachide", "cacahuete")),
    # Frutos de casca rija
    LexEntry("frutos de casca rija", SAFE, "en:nuts", "en:nuts",
             variants=("frutos secos", "amendoa", "amendoas", "avela",
                       "avelas", "noz", "nozes", "caju", "castanha de caju",
                       "pistacio", "pistacios", "noz pecan", "macadamia",
                       "castanha",
                       # EN/FR
                       "almond", "almonds", "hazelnut", "hazelnuts", "walnut",
                       "walnuts", "cashew", "pistachio", "pecan", "tree nuts",
                       "nut", "nuts", "amande", "noisette", "noix",
                       "fruits a coque")),
    # Peixe
    LexEntry("peixe", SAFE, "en:fish", "en:fish",
             variants=("atum", "bacalhau", "salmao", "anchova", "sardinha",
                       "fish", "tuna", "salmon", "cod", "anchovy", "poisson",
                       "thon", "saumon")),
    # Crustaceos
    LexEntry("crustaceos", SAFE, "en:crustaceans", "en:crustaceans",
             variants=("camarao", "gambas", "lagosta", "caranguejo",
                       "lavagante",
                       "crustaceans", "shrimp", "prawn", "prawns", "lobster",
                       "crab", "crustaces", "crevette")),
    # Moluscos
    LexEntry("moluscos", SAFE, "en:molluscs", "en:molluscs",
             variants=("mexilhao", "ameijoa", "lula", "polvo", "berbigao",
                       "vieira",
                       "molluscs", "mollusks", "mussel", "mussels", "squid",
                       "octopus", "clam", "mollusques", "moule")),
    # Aipo
    LexEntry("aipo", SAFE, "en:celery", "en:celery",
             variants=("celery", "celeri")),
    # Mostarda
    LexEntry("mostarda", SAFE, "en:mustard", "en:mustard",
             variants=("mustard", "moutarde")),
    # Sesamo
    LexEntry("sesamo", SAFE, "en:sesame-seeds", "en:sesame-seeds",
             variants=("sementes de sesamo", "tahini",
                       "sesame", "sesame seeds", "graines de sesame")),
    # Tremoco
    LexEntry("tremoco", SAFE, "en:lupin", "en:lupin",
             variants=("farinha de tremoco", "lupin", "lupine")),
    # Sulfitos / dioxido de enxofre
    LexEntry("sulfitos", SAFE, "en:sulphur-dioxide-and-sulphites",
             "en:sulphur-dioxide-and-sulphites",
             variants=("dioxido de enxofre", "anidrido sulfuroso",
                       "metabissulfito", "sulfito",
                       "sulphites", "sulfites", "sulphur dioxide",
                       "sulfur dioxide", "sulfite", "anhydride sulfureux")),
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
