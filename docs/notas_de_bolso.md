# Notas de bolso — apresentação do trabalho

> Suporte rápido para perguntas do professor. Lê na diagonal; cada bloco é uma resposta pronta.

---

## 0. Pitch de 30 segundos (decorar)

Sistema em Python que recebe a **foto de um rótulo alimentar** e produz:
deteção de **glúten** + **14 alergénios da UE** (Reg. 1169/2011), identificação de
**ingredientes ambíguos**, um **grau de risco**, e — o ponto-chave — uma
**justificação explicável ingrediente a ingrediente**. Não é uma "caixa preta":
qualquer veredicto é rastreável até ao ingrediente que o causou.

Pipeline: **OCR → NLP → regras + classificadores ML → explicação → relatório → avaliação.**

---

## 1. Números para ter na ponta da língua

| Métrica | Valor |
|---|---|
| Produtos no dataset (Portugal, Open Food Facts) | **21 262** |
| Amostras de treino p/ ML | 8 770 · 968 *features* (MIN_DF=10) · 3 classes |
| **Melhor modelo ML** | Random Forest |
| RF — exatidão / macro-F1 (teste, 2193 amostras) | **88,7% / 88,1%** |
| Ordem dos modelos | RF (88,7) > Árvore Decisão (87,9) > Naive Bayes (82,0) |
| **Avaliação B** (pipeline NLP+regras, não circular, 1500 produtos) | **91,2% exatidão**, macro-F1 90,4% |
| Recall do glúten na aval. B | **89,9%** (subiu de 80% ao juntar EN/FR ao léxico) |
| Confiança média do OCR em fotos reais | **~48%** |
| Limiar de *fuzzy matching* | **0,84** |

Classe mais difícil para **todos** os modelos: **"suspeito"** (ambíguo) — F1 ~78%.

---

## 2. Perguntas prováveis e respostas curtas

**"Porque não usaram um LLM / ChatGPT / rede neuronal grande?"**
Porque o objetivo era **reutilizar os conceitos das aulas** (KNN, Naive Bayes,
árvores, MLP, métricas de distância, matriz de confusão) e ter **explicabilidade
total** e custo computacional baixo. Um LLM seria caixa-preta e impossível de
justificar ingrediente a ingrediente — exatamente o requisito central do trabalho.

**"Os 88% de ML não são circular, já que as regras é que criaram os rótulos?"** *(a pergunta difícil)*
Boa observação — e é por isso que temos **duas avaliações**. A **A** (RF, 88,7%) mede
se o modelo reproduz a lógica das regras a partir do *bag-of-tags* (supervisão fraca).
A **B** é **não circular**: o pipeline só lê o `ingredients_text`, e comparamos contra
o campo **independente `allergens`** da OFF, que o pipeline nunca vê → **91,2%**.

**"Porque não é 100% no modelo, se as regras geraram os rótulos?"**
Porque (1) o `MIN_DF=10` deixa cair *tags* de glúten raras, e (2) o rótulo também
depende de campos de alergénios/etiqueta que **não estão nas *features***. Logo há
aprendizagem genuína, não cópia trivial.

**"Qual é a maior fonte de erro?"**
O **OCR**. Em fotos reais a confiança é ~48%, perde-se texto, e o veredicto a partir
da imagem tende a ser **menos grave** do que o real. Sobre texto limpo o sistema é
muito melhor (daí a app aceitar também texto colado).

**"E os falsos positivos? Não é mau detetar glúten a mais?"**
É **deliberado**: preferimos sobre-assinalar risco (mais seguro para o consumidor).
Além disso, vários "falsos positivos" da aval. B são na verdade **deteções corretas**
que o rótulo da OFF **omitiu** (ex.: "pão ralado (farinha de trigo)", "sêmola de
trigo-duro") → a precisão real é **superior** à medida. O *ground-truth* é ruidoso.

**"Porque a aveia conta como glúten?"**
Por **precaução** — a aveia em si não tem glúten, mas há contaminação cruzada
frequente no processamento. Escolha conservadora a favor da segurança.

**"Em que línguas funciona?"**
Léxico cobre **PT + EN + FR**. Juntar EN/FR subiu a aval. B de ~88% → 91,2%.
Os falsos negativos que sobram são sobretudo **italiano** ("latte", "cebada"=ES) e
espanhol; extensão natural: juntar IT/ES ou usar a coluna normalizada `ingredients_tags`.

---

## 3. Decisões técnicas (se pedirem detalhe)

- **OCR: Tesseract 5.4** (via `pytesseract`), não EasyOCR. ~80 MB vs ~800 MB de
  PyTorch, rápido em CPU, bom pack PT, e combina com o pré-processamento OpenCV
  (espelha o exemplo de PIL do professor). Pré-processa → Tesseract `por+eng` →
  limpa → extrai a secção de ingredientes.
- **Dataset: usamos `ingredients_tags`** (taxonomia normalizada `en:wheat`, `en:gluten`)
  e **não** o texto livre, porque o dump CSV da OFF tem **mojibake** (codificação
  mista Latin-1/UTF-8). As *tags* são ASCII puro → imunes ao problema.
- **NLP de raiz:** Levenshtein e Jaccard em Python puro (`nlp_distances.py`), sem
  bibliotecas externas — como nas aulas. *Fuzzy match* a 0,84 + marcadores
  "contém"/"traços"/"sem glúten" (e equivalentes EN/FR).
- **Naive Bayes feito de raiz** (Bernoulli) — bate o do sklearn a 100%.
- **Matriz de confusão:** reutilizamos **literalmente** o `confusion_matrix2.py` do
  professor (em `eval_metrics.py`).
- **Validação:** `train_test_split` + **StratifiedKFold(5)**.

---

## 4. Mapa dos ficheiros (se perguntarem "onde está X?")

| Fase | Ficheiro | O quê |
|---|---|---|
| 2 Dataset | `download_off.py`, `filter_portugal.py`, `knowledge_base.py` | 21k produtos PT + KB glúten/alergénios |
| 3 OCR | `ocr_preprocess.py`, `ocr_engine.py`, `ocr_pipeline.py` | imagem → texto |
| 4 NLP | `nlp_distances.py`, `lexicon_pt.py`, `nlp_ingredients.py` | texto → `AnalysisResult` |
| 5 ML | `classifier_rules.py`, `features.py`, `naive_bayes.py`, `train_compare.py` | regras + 3 modelos comparados |
| 6 Explicação | `explain.py` | `IngredientMatch` → linha ❌/✅/⚠️ + justificação |
| 7 Relatório | `report.py` | 4 secções: resumo / ingredientes / alergénios / recomendações |
| 8 Avaliação | `evaluate_system.py`, `eval_metrics.py` | A, B, C + análise de erros |
| App | `webapp.py` (Flask) | `python src/webapp.py` → http://127.0.0.1:5000 |

**Fluxo:** `ocr_pipeline` → `nlp_ingredients` → `classifier_rules.assess` → `explain` → `report`.

---

## 5. Graus de risco (o que o sistema devolve)

- **Glúten:** 5 graus → *Sem · Baixo · Médio · Alto · Contém*.
- **Alergénios:** 3 estados (presente / vestígios / ausente) sobre os **14 da UE**.
- Cada veredicto vem com **lista de razões** (que ingrediente, que *tag* `en:`, símbolo).

---

## 6. Limitações (assumir com confiança, mostra maturidade)

1. **OCR** é o gargalo (~48% em fotos reais).
2. **Supervisão fraca** na Fase 5: ML aprende a lógica das regras, não um juízo humano.
3. *Ground-truth* da OFF **ruidoso** (preenchido por voluntários, omite alergénios).
4. *Fuzzy matching* gera alguns FP por semelhança (ex.: "lactone"~"lactose") — troca consciente recall↑/precisão↓.
5. Línguas além de PT/EN/FR ainda por cobrir (IT/ES).

> Regra de ouro na defesa: se não souberes um número exato, dá o **intervalo** e
> diz **onde está** ("está no `avaliacao_fase8.md`"). Assumir uma limitação vale
> mais pontos do que inventar uma resposta.
