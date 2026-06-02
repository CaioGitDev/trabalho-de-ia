# Glossário — abreviaturas e termos do trabalho

> Explicações em linguagem simples. Se o professor usar um destes termos, tens aqui a tradução rápida.

---

## Siglas e abreviaturas

| Sigla | Significa | O que é, em simples |
|---|---|---|
| **IA / AI** | Inteligência Artificial | Programas que tomam decisões "inteligentes" a partir de dados. |
| **OCR** | *Optical Character Recognition* (Reconhecimento Ótico de Carateres) | Transforma a **imagem** de texto (foto do rótulo) em **texto editável**. |
| **NLP** | *Natural Language Processing* (Processamento de Linguagem Natural) | Faz o computador "perceber" texto humano: separar palavras, normalizar, comparar. |
| **ML** | *Machine Learning* (Aprendizagem Automática) | O sistema **aprende padrões a partir de exemplos**, em vez de ser programado regra a regra. |
| **OFF** | *Open Food Facts* | Base de dados pública e gratuita de produtos alimentares — a nossa fonte de dados. |
| **UE / EU** | União Europeia | Aqui refere-se aos **14 alergénios obrigatórios** da legislação europeia. |
| **Reg. 1169/2011** | Regulamento (UE) nº 1169/2011 | Lei europeia que obriga a declarar os 14 alergénios nos rótulos. |
| **CSV** | *Comma-Separated Values* | Ficheiro de tabela em texto (valores separados por vírgulas), como uma folha de Excel simples. |
| **KB** | *Knowledge Base* (Base de Conhecimento) | A nossa lista curada de ingredientes com glúten / ambíguos / alergénios. |
| **RF** | *Random Forest* (Floresta Aleatória) | Modelo de ML: junta **muitas árvores de decisão** e vota — foi o nosso melhor. |
| **NB** | *Naive Bayes* | Modelo de ML baseado em **probabilidades** (teorema de Bayes). |
| **DT** | *Decision Tree* (Árvore de Decisão) | Modelo de ML em forma de "fluxograma" de perguntas sim/não. |
| **KNN** | *k-Nearest Neighbors* | Classifica um caso olhando para os **k exemplos mais parecidos** (dado nas aulas). |
| **ANN / MLP** | *Artificial Neural Network* / *Multi-Layer Perceptron* | Rede neuronal artificial (dada nas aulas; nós **não** a usámos no final). |

---

## Métricas de avaliação (as mais importantes)

| Termo | O que mede | Em simples |
|---|---|---|
| **Exatidão** (*Accuracy*) | % de previsões certas no total | De 100 produtos, quantos acertámos. |
| **Precisão** (*Precision*) | Dos que dissemos "tem glúten", quantos têm mesmo | Mede os **falsos alarmes**. Alta precisão = poucos falsos positivos. |
| **Recall** (Sensibilidade) | Dos que **têm** glúten, quantos apanhámos | Mede o que **escapa**. Alto recall = poucos falsos negativos. |
| **F1** | Média equilibrada de precisão e recall | Um número único que junta as duas (quanto mais alto, melhor). |
| **macro-F1 / macro-P / macro-R** | A mesma métrica, **média entre as classes** | "macro" = trata cada classe (sem/contém/suspeito) com igual peso. |
| **Falso Positivo (FP)** | Dissemos "tem glúten" mas **não** tem | Alarme a mais (no nosso caso, é o erro "mais seguro"). |
| **Falso Negativo (FN)** | Dissemos "não tem" mas **tem** | O erro perigoso — deixa passar glúten não detetado. |
| **Matriz de confusão** | Tabela real × previsto | Mostra exatamente **onde** o modelo acerta e erra. |

---

## Conceitos do nosso método

| Termo | Explicação simples |
|---|---|
| **Pipeline** | A "linha de montagem": cada etapa recebe o resultado da anterior (OCR → NLP → … → relatório). |
| **Léxico** (*lexicon*) | O nosso **dicionário** de termos de ingredientes (em PT, EN e FR) usado para reconhecer glúten/alergénios. |
| **Taxonomia / tags** | Etiquetas normalizadas da OFF, tipo `en:wheat` (trigo), `en:gluten`. Sempre em inglês e sem acentos → fáceis de processar. |
| **Tokenização** | Partir o texto em **palavras/pedaços** ("farinha de trigo" → "farinha", "de", "trigo"). |
| **Normalização** | Pôr o texto num formato uniforme (minúsculas, sem acentos) para comparar bem. |
| **Distância de Levenshtein** | Quão diferentes são duas palavras = **nº mínimo de letras a mudar** para passar de uma à outra. Usada para apanhar erros de escrita/OCR. |
| **Índice de Jaccard** | Semelhança entre dois conjuntos = **partes em comum ÷ total**. Usado para comparar listas de palavras. |
| ***Fuzzy matching*** (correspondência difusa) | Reconhecer um ingrediente **mesmo com pequenos erros** (ex.: "trgio" ≈ "trigo"). O nosso limiar é 0,84. |
| **Bag-of-tags / bag-of-words** | Representar um produto pela **lista de etiquetas que tem**, ignorando a ordem. É o "input" dos modelos de ML. |
| ***Multi-hot*** | Vetor de 0s e 1s: 1 onde a etiqueta está presente, 0 onde não. Forma de dar as tags ao modelo. |
| **MIN_DF** | *Minimum Document Frequency*: ignorar etiquetas **demasiado raras** (aparecem em menos de 10 produtos), para o modelo não decorar ruído. |
| **Supervisão fraca** (*weak supervision*) | Treinar o ML com rótulos **gerados pelas regras** (e não por humanos). Mais rápido, mas é uma limitação que assumimos. |
| **Ground-truth** ("verdade de referência") | A resposta considerada **correta** com que comparamos as previsões. No nosso caso B, o campo `allergens` da OFF. |
| **Avaliação circular vs. não circular** | **Circular**: testar com dados ligados ao treino (avaliação A). **Não circular**: testar contra uma fonte independente (avaliação B, mais honesta). |
| **k-fold / StratifiedKFold** | Validação que **divide os dados em k partes (5)** e roda treino/teste, mantendo a proporção das classes. Dá uma medida mais fiável. |
| ***Train/test split*** | Separar os dados em **treino** (para aprender) e **teste** (para avaliar com dados nunca vistos). |
| **Explicabilidade** (*explainability*) | A capacidade de o sistema **dizer porquê** decidiu — o coração do nosso trabalho. |
| **Mojibake** | Texto **corrompido** por erro de codificação (ex.: "açúcar" → "a��car"). Por isso usámos as tags ASCII em vez do texto livre. |
| **Codificação / encoding (UTF-8, Latin-1)** | A forma como letras e acentos são guardados em bytes. Misturar codificações causa mojibake. |

---

## Ferramentas e tecnologias

| Nome | O que é |
|---|---|
| **Python** | A linguagem de programação de todo o projeto. |
| **Tesseract** | Motor de OCR (gratuito, da Google) que usámos para ler a imagem. |
| **OpenCV** | Biblioteca de **processamento de imagem** (melhora a foto antes do OCR: contraste, etc.). |
| **pytesseract** | "Ponte" de Python para o Tesseract. |
| **scikit-learn (sklearn)** | Biblioteca de ML (modelos, métricas, divisão treino/teste). |
| **Flask** | Micro-framework para fazer a **aplicação web** (`src/webapp.py`). |
| **Git** | Sistema de controlo de versões (histórico dos commits do trabalho). |
| **Taxonomia da OFF** | O esquema de etiquetas normalizadas da Open Food Facts. |

---

## Os 14 alergénios da UE (para referência)

Cereais com glúten · Crustáceos · Ovos · Peixe · Amendoins · Soja · Leite ·
Frutos de casca rija (nozes, amêndoas…) · Aipo · Mostarda · Sésamo ·
Dióxido de enxofre e sulfitos · Tremoço · Moluscos.

> **Dica de defesa:** se não souberes um termo na hora, não inventes — diz
> "está no nosso glossário/relatório" e descreve a ideia geral. Demonstrar que
> percebes o conceito vale mais do que a palavra exata.
