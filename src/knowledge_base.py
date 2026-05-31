"""Base de conhecimento alimentar para detecao de gluten e alergenios.

Os identificadores usam a taxonomia normalizada do Open Food Facts
(prefixo `en:`). E essa taxonomia que o campo `ingredients_tags` ja
contem, pelo que as comparacoes sao exact-match (rapidas e robustas
ao mojibake do dump).

Categorias:
- GLUTEN_TAGS:  cereais e derivados que contem gluten por natureza.
- AMBIGUOUS_TAGS: ingredientes cuja origem nao e clara (podem ou nao
  conter gluten). O sistema deve assinalar risco quando aparecem.
- EU_ALLERGEN_TAGS: os 14 alergenios de declaracao obrigatoria pela
  regulamentacao europeia (Reg. 1169/2011), com a chave canonica usada
  pela OFF no campo `allergens`.

Referencia: https://wiki.openfoodfacts.org/Ingredients_taxonomy
"""
from __future__ import annotations


GLUTEN_TAGS: set[str] = {
    # Trigo e variantes
    "en:wheat",
    "en:wheat-flour",
    "en:wheat-starch",
    "en:wheat-bran",
    "en:wheat-germ",
    "en:wheat-gluten",
    "en:wheat-protein",
    "en:wheat-fibre",
    "en:wheat-semolina",
    "en:whole-wheat",
    "en:whole-wheat-flour",
    "en:soft-wheat",
    "en:soft-wheat-flour",
    "en:hard-wheat",
    "en:durum-wheat",
    "en:durum-wheat-semolina",
    "en:durum-wheat-flour",
    # Centeio
    "en:rye",
    "en:rye-flour",
    "en:whole-rye-flour",
    # Cevada e malte
    "en:barley",
    "en:barley-flour",
    "en:barley-malt",
    "en:barley-malt-extract",
    "en:malt",
    "en:malt-extract",
    "en:malted-barley",
    "en:malted-wheat",
    "en:malted-barley-flour",
    # Espelta, kamut, triticale, einkorn
    "en:spelt",
    "en:spelt-flour",
    "en:kamut",
    "en:khorasan-wheat",
    "en:triticale",
    "en:einkorn",
    "en:emmer",
    # Aveia (frequentemente contaminada; classificada como gluten salvo
    # mencao explicita de "aveia sem gluten")
    "en:oat",
    "en:oats",
    "en:oat-flour",
    "en:oat-bran",
    "en:rolled-oats",
    # Derivados de massa de cereais
    "en:semolina",
    "en:couscous",
    "en:bulgur",
    "en:bulghur",
    "en:seitan",
    "en:breadcrumbs",
    # Marcacao directa
    "en:gluten",
    "en:gluten-containing-cereals",
}


AMBIGUOUS_TAGS: set[str] = {
    # Amidos sem origem declarada
    "en:starch",
    "en:modified-starch",
    "en:native-starch",
    "en:pregelatinised-starch",
    "en:oxidised-starch",
    # Farinha generica
    "en:flour",
    "en:cereal-flour",
    "en:cereals",
    "en:cereal",
    # Proteina vegetal generica
    "en:vegetable-protein",
    "en:plant-protein",
    "en:hydrolysed-vegetable-protein",
    "en:textured-vegetable-protein",
    # Maltodextrinas / dextrinas (origem cereal possivel)
    "en:maltodextrin",
    "en:maltodextrins",
    "en:dextrin",
    "en:dextrins",
    "en:dextrose",
    "en:glucose-syrup",
    # Aromas e extratos
    "en:flavouring",
    "en:natural-flavouring",
    "en:flavour",
    "en:flavours",
    "en:aroma",
    "en:cereal-extract",
    # Caramelo (frequentemente sobre base de cereal)
    "en:caramel",
    "en:caramel-colour",
    "en:e150",
    "en:e150a",
    "en:e150b",
    "en:e150c",
    "en:e150d",
    # Espessantes / estabilizadores que podem ter origem cereal
    "en:thickener",
    "en:stabiliser",
    # Fibras genericas
    "en:vegetable-fibre",
    "en:fibre",
}


# Os 14 alergenios de declaracao obrigatoria (Anexo II do Reg. UE 1169/2011)
EU_ALLERGEN_TAGS: dict[str, str] = {
    "en:gluten":                            "Cereais com gluten",
    "en:milk":                              "Leite",
    "en:eggs":                              "Ovos",
    "en:soybeans":                          "Soja",
    "en:peanuts":                           "Amendoim",
    "en:nuts":                              "Frutos de casca rija",
    "en:fish":                              "Peixe",
    "en:crustaceans":                       "Crustaceos",
    "en:molluscs":                          "Moluscos",
    "en:celery":                            "Aipo",
    "en:mustard":                           "Mostarda",
    "en:sesame-seeds":                      "Sementes de sesamo",
    "en:lupin":                             "Tremoco",
    "en:sulphur-dioxide-and-sulphites":     "Sulfitos",
}


# Etiquetas (campo `labels_tags`) que indicam ausencia certificada de gluten.
GLUTEN_FREE_LABEL_TAGS: set[str] = {
    "en:no-gluten",
    "en:gluten-free",
    "en:sem-gluten",
    "en:without-gluten",
    "en:certified-gluten-free",
    "en:glutenfree",
}
