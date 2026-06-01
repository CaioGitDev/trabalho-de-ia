# Deteção de Glúten e Alergénios em Rótulos Alimentares

Projeto académico de **Introdução à Inteligência Artificial** (Universidade
Fernando Pessoa). Sistema em Python que recebe a **fotografia de um rótulo
alimentar** e produz uma análise automática, explicável e justificada dos
ingredientes, classificando o risco relativo ao **glúten** e aos **14
alergénios de declaração obrigatória** da União Europeia (Reg. UE 1169/2011).

> O sistema foi construído para **demonstrar a aplicação prática dos conceitos
> lecionados** (Teorema de Bayes, métricas de distância, KNN/Naive Bayes,
> árvores de decisão, validação cruzada, matriz de confusão), e não como uma
> solução isolada. Por isso reutiliza diretamente material das aulas (ver a
> secção [Reutilização dos conceitos](#reutilização-dos-conceitos-das-aulas)).

---

## Objetivo

A partir de uma imagem (ou de texto de ingredientes), o sistema indica:

- presença de **glúten** (5 graus: Sem Glúten, Baixo, Médio, Alto Risco, Contém);
- presença de **alergénios** (ingrediente, traços ou ausência);
- **ingredientes ambíguos** (origem não declarada → risco potencial);
- **recomendações** para o consumidor;
- uma **justificação por ingrediente** (a explicabilidade é obrigatória).

---

## Arquitetura — pipeline em 8 fases

```
  Imagem do rótulo
        │
   [3] OCR ............ pré-processamento (OpenCV) → Tesseract (por+eng) → limpeza
        │  texto
   [4] NLP ............ normalização + tokenização + correspondência difusa
        │  AnalysisResult        (Levenshtein/Jaccard) contra um léxico PT
   [5] Classificação .. regras especializadas  +  modelos supervisionados
        │  RiskAssessment          (Naive Bayes / Árvore de Decisão / Random Forest)
   [6] Explicabilidade  tabela por ingrediente  ❌ / ✅ / ⚠️  + observação
        │  Explanation
   [7] Relatório ...... RESUMO · ANÁLISE · ALERGÉNIOS · RECOMENDAÇÕES
        │
   [8] Avaliação ...... Accuracy / Precision / Recall / F1 (não circular)
```

As fases 1 (investigação) e 2 (dataset + estatística) suportam todo o resto:
o **Open Food Facts** é a fonte de dados e a base de conhecimento
(`knowledge_base.py`) lista as tags de glúten, ambíguas e os 14 alergénios.

---

## Estrutura do projeto

| Módulo (`src/`) | Fase | Papel |
| --- | :---: | --- |
| `download_off.py` · `filter_portugal.py` | 2 | Descarga do dump OFF e filtragem dos produtos de Portugal |
| `analyze_dataset.py` | 2 | Análise estatística (tabelas + gráficos em `docs/figures/`) |
| `knowledge_base.py` | 1–2 | Tags de glúten, ambíguas e os 14 alergénios da UE |
| `ocr_preprocess.py` · `ocr_engine.py` · `ocr_clean.py` · `ocr_pipeline.py` | 3 | Pipeline OCR (imagem → texto de ingredientes) |
| `nlp_distances.py` | 4 | Distâncias Levenshtein/Jaccard/Hamming (Python puro) |
| `lexicon_pt.py` | 4 | Léxico PT-PT → tags `en:` (ponte para a base de conhecimento) |
| `nlp_ingredients.py` | 4 | Normalização, tokenização e correspondência difusa |
| `classifier_rules.py` | 5 | Regras especializadas (grau de glúten + alergénios) |
| `features.py` | 5 | Dataset rotulado + features *bag-of-tags* |
| `naive_bayes.py` | 5 | Naive Bayes de Bernoulli implementado de raiz |
| `eval_metrics.py` | 5–8 | Avaliação que reutiliza a `confusion_matrix2.py` do professor |
| `train_compare.py` | 5 | Treino e comparação dos três classificadores |
| `explain.py` | 6 | Motor de explicabilidade (tabela por ingrediente) |
| `report.py` | 7 | Relatório automático (4 secções) e pipeline completo |
| `evaluate_system.py` | 8 | Avaliação e validação do sistema |

Saídas: `docs/figures/` (gráficos), `docs/reports/` (relatórios de exemplo e
avaliação). Os dados volumosos (`data/raw/`, `data/processed/`) não são
versionados.

---

## Requisitos e instalação

- **Python 3.13** (Windows 11; também funciona noutros sistemas).
- Dependências Python:

  ```bash
  pip install -r requirements.txt
  ```

- **Tesseract OCR** (apenas necessário para analisar imagens — a fase 3):

  ```powershell
  winget install UB-Mannheim.TesseractOCR
  ```

  Os pacotes de idioma (`por`, `eng`, `osd`) estão em `data/tessdata/`. Em
  Windows, definir a variável de ambiente `TESSDATA_PREFIX` a apontar para essa
  pasta (não usar `--tessdata-dir`).

---

## Como executar

### Análise de um rótulo (pipeline completo)

A partir de **texto** de ingredientes:

```bash
python src/report.py --text "Farinha de trigo, água, sal, amido modificado, leite. Pode conter traços de soja."
```

A partir de uma **imagem** (requer Tesseract), gravando o relatório em markdown:

```bash
python src/report.py --image data/sample_labels/5601009935185.jpg --md docs/reports/exemplo.md
```

Sem argumentos, corre sobre os rótulos de exemplo incluídos.

### Reproduzir cada fase

```bash
# Fase 2 — estatística do dataset (requer o CSV filtrado)
python src/analyze_dataset.py

# Fase 3 — OCR de uma imagem
python src/ocr_pipeline.py data/sample_labels/5601009935185.jpg

# Fase 4 — NLP sobre amostras / texto
python src/nlp_demo.py
python src/nlp_demo.py --text "Amido modificado, aroma, sal."

# Fase 5 — treino e comparação dos classificadores
python src/train_compare.py

# Fase 6 — explicabilidade
python src/explain.py

# Fase 8 — avaliação do sistema
python src/evaluate_system.py            # amostra (rápido)
python src/evaluate_system.py --full     # todos os produtos elegíveis
```

> Para reconstruir o dataset de origem: `python src/download_off.py` seguido de
> `python src/filter_portugal.py` (descarrega ~9 GiB e filtra os produtos de
> Portugal).

---

## Resultados

### Comparação de classificadores (Fase 5)

Tarefa: classificar o estado de glúten (`sem` / `contém` / `suspeito`) a partir
do *bag-of-tags* de ingredientes. 8770 amostras, 968 features, validação por
*train/test split* + K-Fold(5) estratificado.

| Modelo | K-Fold (exatidão) | Teste (exatidão) | Macro-F1 |
| --- | :---: | :---: | :---: |
| Naive Bayes (de raiz) | 81.3 % | 82.0 % | 80.8 % |
| Árvore de Decisão | 87.8 % | 87.9 % | 87.0 % |
| **Random Forest** | **89.5 %** | **88.7 %** | **88.1 %** |

A classe `suspeito` (ingredientes ambíguos) é a mais difícil para todos os
modelos. O Naive Bayes implementado de raiz coincide a **100 %** com o
`BernoulliNB` do scikit-learn, validando a implementação.

### Validação do sistema (Fase 8)

Avaliação **não circular**: o pipeline NLP+regras lê apenas o texto livre de
ingredientes e é comparado com um rótulo **independente** (o campo `allergens`
do Open Food Facts, que o pipeline nunca consulta).

| Avaliação | Resultado |
| --- | --- |
| Random Forest (teste retido) | Exatidão 88.7 %, macro-F1 88.1 % |
| Pipeline NLP+regras vs rótulo independente (1500 produtos) | Exatidão **91.2 %**; deteção de glúten **P=85.7 % / R=89.9 %** |

> O léxico cobre **PT + EN + FR**: incluir os termos EN/FR subiu a exatidão da
> avaliação B de ~88 % para ~91 % e o *recall* de glúten de 80 % para ~90 %.

Detalhe completo em [`docs/reports/avaliacao_fase8.md`](docs/reports/avaliacao_fase8.md).

---

## Reutilização dos conceitos das aulas

| Conceito lecionado | Onde é usado |
| --- | --- |
| Teorema de Bayes / Naive Bayes | `naive_bayes.py` (implementado de raiz) |
| Distâncias Levenshtein, Jaccard, Hamming | `nlp_distances.py` (correspondência difusa de OCR) |
| `train_test_split`, `fit`, `predict` | `train_compare.py` |
| Validação cruzada K-Fold estratificada | `train_compare.py` |
| Árvore de Decisão e Random Forest | `train_compare.py` (scikit-learn) |
| Matriz de confusão + Accuracy/Precision/Recall/F1 | `eval_metrics.py` (reutiliza a `confusion_matrix2.py` do professor) |

A proposta inicial de "construir um LLM de raiz" foi rejeitada após
reavaliação técnica: a abordagem **OCR + NLP + regras + classificadores
supervisionados** é mais adequada ao contexto académico (dados, tempo de treino
e recursos) e alinha-se com o que foi efetivamente lecionado.

---

## Limitações

- O **OCR** é a maior fonte de erro: em fotografias reais (confiança média
  ~48 %) parte do texto não é recuperada e o veredicto tende a ser menos grave
  do que o real.
- O **léxico cobre PT/EN/FR**; rótulos noutras línguas (italiano, espanhol)
  ainda geram falsos negativos — extensão natural: juntar IT/ES ou usar a
  coluna normalizada `ingredients_tags` quando disponível.
- A **correspondência difusa favorece o *recall*** (mais seguro sobre-assinalar
  risco), o que introduz alguns falsos positivos (ex.: "lactone" ≈ "lactose").
- Os classificadores supervisionados usam **rótulos gerados pelas próprias
  regras** (supervisão fraca): medem a capacidade de reproduzir as regras, não
  um juízo humano independente.
- O dump do Open Food Facts contém **mojibake** em alguns textos, pelo que a
  análise estatística privilegia a coluna normalizada `ingredients_tags`.

---

## Equipa

- Caio Rosa (160173003)
- Lucélia Ferreira (240001227)
- Nadine Jeremias (240001501)

Universidade Fernando Pessoa — Introdução à Inteligência Artificial, 2026.
