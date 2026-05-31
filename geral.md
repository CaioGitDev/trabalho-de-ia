
# Projeto Académico – Introdução à Inteligência Artificial

## Contexto

Disciplina: Introdução à Inteligência Artificial

Elementos do Grupo:

* Caio Rosa (Nº 160173003)
* Lucélia Ferreira (Nº 240001227)
* Nadine Jeremias (Nº 240001501)

## Objetivo

Pretende-se desenvolver uma solução de Inteligência Artificial capaz de analisar imagens de rótulos alimentares e identificar automaticamente:

* Presença de glúten.
* Presença de alergénios.
* Ingredientes potencialmente ambíguos.
* Grau de risco para consumidores com restrições alimentares.

O sistema deverá produzir uma análise clara, justificável e explicável para o utilizador final.

## Contexto Académico

Dentro da pasta "exemplos-de-aulas" existem:

* Exemplos de código desenvolvidos durante as aulas.
* Resumos e sumários dos conteúdos lecionados.

Antes de iniciar qualquer implementação, analisar detalhadamente todo esse material e identificar:

1. Conceitos que possam ser reutilizados.
2. Algoritmos estudados durante a disciplina.
3. Estruturas de processamento de dados já demonstradas em aula.
4. Técnicas de classificação ou aprendizagem automática que possam ser adaptadas ao projeto.

O objetivo é demonstrar aplicação prática dos conteúdos lecionados e não apenas desenvolver uma solução isolada.

---

# Reavaliação Técnica da Proposta

A proposta inicial refere a criação de um "LLM do zero".

Antes da implementação, realizar uma análise crítica sobre a viabilidade desta abordagem considerando:

* Complexidade computacional.
* Disponibilidade de dados.
* Tempo de treino.
* Recursos necessários.
* Adequação ao contexto académico.

Comparar esta solução com alternativas mais adequadas, tais como:

* OCR + NLP.
* Sistemas baseados em regras.
* Classificadores supervisionados.
* Modelos de linguagem leves treinados para domínio específico.

Apresentar vantagens e desvantagens de cada abordagem e justificar tecnicamente a arquitetura escolhida.

# Dataset Oficial do Projeto

## Fonte Principal de Dados

O projeto deverá utilizar como principal fonte de dados a base alimentar pública Open Food Facts.

Fonte:

https://world.openfoodfacts.org

A escolha desta plataforma deve-se aos seguintes fatores:

* Base de dados aberta e gratuita.
* Milhões de produtos alimentares catalogados.
* Presença significativa de produtos comercializados em Portugal e na União Europeia.
* Disponibilização de ingredientes, alergénios, categorias e informação nutricional.
* Possibilidade de acesso através de ficheiros exportados e API pública.
* Elevada relevância para o problema proposto.

---

## Objetivos da Utilização do Dataset

A base de dados deverá ser utilizada para:

* Construção do dataset de treino.
* Construção do dataset de validação.
* Extração de listas reais de ingredientes.
* Identificação de alergénios declarados.
* Criação de regras de deteção de glúten.
* Testes de desempenho do sistema.

---

## Processo de Preparação dos Dados

Antes de qualquer treino ou classificação deverá ser executado um processo de preparação dos dados que inclua:

### Limpeza

* Remoção de registos incompletos.
* Remoção de produtos sem lista de ingredientes.
* Tratamento de valores nulos.
* Eliminação de duplicados.

### Normalização

* Conversão de texto para formato uniforme.
* Normalização de acentuação.
* Correção de caracteres especiais.
* Uniformização dos nomes dos ingredientes.

### Estruturação

Para cada produto devem ser armazenados pelo menos os seguintes campos:

| Campo            | Descrição                      |
| ---------------- | ------------------------------ |
| product_name     | Nome do produto                |
| brands           | Marca                          |
| categories       | Categoria alimentar            |
| ingredients_text | Lista completa de ingredientes |
| allergens        | Alergénios declarados          |
| labels           | Etiquetas do produto           |
| nutrition_grade  | Classificação nutricional      |
| countries        | Países de comercialização      |

---

## Construção da Base de Conhecimento

A partir dos dados recolhidos deverá ser construída uma base de conhecimento especializada contendo:

### Ingredientes que Contêm Glúten

Exemplos:

* Trigo
* Centeio
* Cevada
* Espelta
* Kamut
* Triticale
* Malte de cevada
* Farinha de trigo

### Ingredientes Potencialmente Ambíguos

Exemplos:

* Amido
* Amido modificado
* Proteína vegetal
* Farinha
* Extrato de cereais
* Aromas naturais
* Maltodextrina

Estes ingredientes deverão gerar alertas quando a origem não estiver claramente identificada.

### Alergénios

A base de conhecimento deverá incluir os principais alergénios definidos pela regulamentação europeia, incluindo:

* Glúten
* Leite
* Ovos
* Soja
* Amendoim
* Frutos de casca rija
* Peixe
* Crustáceos
* Moluscos
* Aipo
* Mostarda
* Sementes de sésamo
* Tremoço
* Sulfitos

---

## Requisitos de Avaliação do Dataset

Antes da implementação final, produzir uma análise estatística contendo:

* Número total de produtos analisados.
* Número de categorias alimentares.
* Frequência dos alergénios.
* Frequência dos ingredientes associados ao glúten.
* Percentagem de produtos classificados como sem glúten.
* Percentagem de produtos com ingredientes ambíguos.

Os resultados devem ser apresentados através de tabelas e gráficos para suportar as conclusões do projeto.

---

## Expansão Opcional

Caso seja necessário aumentar a qualidade dos dados, poderão ser integradas fontes complementares, desde que devidamente documentadas e justificadas, mantendo o Open Food Facts como dataset principal do projeto.


---

# Estrutura Geral do Projeto

## Fase 1 – Estudo e Investigação

Objetivos:

* Estudar o problema da deteção de glúten e alergénios.
* Levantar regulamentação alimentar relevante.
* Identificar ingredientes que contêm glúten.
* Identificar ingredientes de risco.
* Identificar alergénios obrigatórios segundo a legislação europeia.

Entregáveis:

* Documento de investigação.
* Lista inicial de ingredientes.
* Lista de alergénios.

---

## Fase 2 – Pesquisa e Construção do Dataset

Objetivos:

Encontrar datasets adequados para treino e validação.

Dar prioridade a:

* Produtos comercializados em Portugal.
* Produtos europeus.
* Bases de dados alimentares públicas.

Investigar fontes como:

* Open Food Facts.
* Dados Abertos Europeus.
* Bases alimentares portuguesas.
* Informação pública de fabricantes.

Criar um dataset estruturado contendo:

* Nome do produto.
* Ingredientes.
* Alergénios declarados.
* Informação nutricional.
* Categoria do produto.
* Indicação de glúten.

Produzir estatísticas sobre:

* Quantidade de produtos.
* Distribuição das categorias.
* Frequência dos alergénios.

---

## Fase 3 – Extração de Texto

Objetivos:

Implementar um módulo OCR capaz de:

* Receber imagens de rótulos.
* Extrair texto dos ingredientes.
* Limpar ruído.
* Corrigir erros comuns de OCR.

Avaliar bibliotecas Python adequadas e justificar a escolha.

---

## Fase 4 – Processamento de Linguagem Natural

Objetivos:

Desenvolver mecanismos para:

* Normalização dos ingredientes.
* Tokenização.
* Remoção de inconsistências.
* Identificação de padrões alimentares.
* Reconhecimento de ingredientes ambíguos.

Exemplos de ingredientes ambíguos:

* Amido.
* Proteína vegetal.
* Farinha.
* Extrato de cereais.
* Maltodextrina.

Quando a origem não estiver claramente identificada, o sistema deverá assinalar risco potencial.

---

## Fase 5 – Sistema Inteligente de Classificação

Objetivos:

Implementar mecanismos de classificação para determinar:

### Estado relativo ao glúten

* Sem Glúten
* Baixo Risco
* Médio Risco
* Alto Risco
* Contém Glúten

### Estado relativo aos alergénios

* Sem alergénios conhecidos
* Possui alergénios
* Possui ingredientes suspeitos

Comparar diferentes abordagens:

* Regras especializadas.
* Naive Bayes.
* Árvores de decisão.
* Random Forest.
* Outros algoritmos estudados na disciplina.

Avaliar desempenho e justificar a escolha final.

---

## Fase 6 – Motor de Explicabilidade

O sistema deve justificar todas as decisões.

Exemplo:

| Ingrediente      | Estado | Observação              |
| ---------------- | ------ | ----------------------- |
| Farinha de trigo | ❌      | Contém glúten           |
| Açúcar           | ✅      | Seguro                  |
| Amido modificado | ⚠️     | Origem não especificada |

---

## Fase 7 – Relatório de Resultado

O sistema deverá gerar automaticamente:

### RESUMO

Classificação global do produto.

### ANÁLISE DOS INGREDIENTES

Tabela detalhada dos ingredientes encontrados.

### ALERGÉNIOS DETETADOS

Lista dos alergénios identificados.

### RECOMENDAÇÕES

Exemplos:

* Confirmar origem do amido utilizado.
* Contactar o fabricante.
* Produto inadequado para celíacos.
* Produto aparentemente seguro.

---

## Fase 8 – Avaliação e Validação

Objetivos:

Medir:

* Accuracy.
* Precision.
* Recall.
* F1 Score.

Realizar testes com produtos reais.

Apresentar erros encontrados.

Discutir limitações da solução.

---

# Requisitos Técnicos

* Linguagem principal: Python.
* Código modular.
* Arquitetura organizada por componentes.
* Documentação completa.
* Utilização de bibliotecas open source.
* Reutilização justificada de conceitos estudados durante as aulas.

---

# Resultado Esperado

Uma aplicação capaz de receber a fotografia de um rótulo alimentar e produzir uma análise automática dos ingredientes, classificando riscos relacionados com glúten e alergénios, apresentando explicações transparentes para todas as decisões tomadas pelo sistema.
