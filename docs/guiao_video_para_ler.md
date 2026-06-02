# Guião do vídeo-relatório — para ler em voz alta

> **Como usar:** lê apenas as linhas normais. As linhas entre `(parêntesis e em
> itálico)` são indicações de ecrã — **não se leem**. Fala devagar e com pausas
> nos pontos finais. Alvo: 6–7 minutos.
>
> Substitui `[Nome 1]`, `[Nome 2]`, `[Nome 3]` pelos nomes do grupo e `[disciplina]`
> pelo nome da cadeira antes de gravar.

---

## 1. Abertura  ·  ~0:00–0:30

*(No ecrã: slide de título com o nome do trabalho e os nomes do grupo.)*

Olá. Este é o nosso trabalho de [disciplina], desenvolvido por [Nome 1], [Nome 2] e [Nome 3].

O nosso projeto responde a um problema do dia a dia: para uma pessoa celíaca, ou com alergias alimentares, ler o rótulo de um produto e perceber se o pode comer é difícil e demorado.

Os ingredientes têm nomes técnicos, estão em letras pequenas, e muitas vezes em várias línguas.

A nossa proposta é um sistema de inteligência artificial que faz esse trabalho automaticamente, a partir de uma simples fotografia do rótulo.

---

## 2. Objetivo  ·  ~0:30–1:15

*(No ecrã: slide com a lista de objetivos.)*

O objetivo é o seguinte: o sistema recebe a foto de um rótulo, ou o texto dos ingredientes, e devolve quatro coisas.

Primeiro, deteta a presença de glúten.

Segundo, identifica quais dos catorze alergénios obrigatórios da União Europeia estão presentes — os que constam do Regulamento mil cento e sessenta e nove de dois mil e onze.

Terceiro, assinala os ingredientes ambíguos, aqueles que podem ou não conter glúten consoante a sua origem.

E quarto, atribui um grau de risco para o consumidor.

Mas o ponto mais importante — e que distingue o nosso trabalho — é que o resultado é explicável. O sistema não dá apenas um veredicto: justifica-o, ingrediente a ingrediente.

---

## 3. Arquitetura  ·  ~1:15–2:45

*(No ecrã: o diagrama do pipeline.)*

Para isso construímos um pipeline com seis etapas, que reutiliza os conceitos dados nas aulas.

A primeira etapa é o reconhecimento ótico de carateres — o OCR — que converte a imagem do rótulo em texto, usando o Tesseract com pré-processamento de imagem em OpenCV.

A segunda é o processamento de linguagem natural, que limpa o texto, separa os ingredientes e faz correspondência com o nosso léxico, usando distâncias entre palavras como Levenshtein e Jaccard, implementadas de raiz.

A terceira etapa é a classificação. Aqui combinamos duas abordagens: um sistema de regras, e modelos de aprendizagem automática supervisionada que comparámos entre si — Naive Bayes, Árvores de Decisão e Random Forest.

A quarta etapa é o motor de explicação, que transforma cada ingrediente numa linha justificada.

A quinta gera o relatório final, com resumo, tabela de ingredientes, alergénios e recomendações.

E a sexta é a avaliação, onde medimos o desempenho do sistema.

*(Pausa breve.)*

Uma pergunta natural é: porque não usámos um modelo de linguagem grande, como o ChatGPT?

Por duas razões. Primeiro, porque o objetivo do trabalho era aplicar os conceitos das aulas. E segundo, porque um modelo desses seria uma caixa preta — não conseguiríamos justificar cada decisão, que é precisamente o requisito central do projeto.

---

## 4. Demonstração  ·  ~2:45–4:45

*(No ecrã: mudar para o browser, com a aplicação web aberta.)*

Vamos ver o sistema a funcionar na nossa aplicação web.

*(Colar o primeiro texto na caixa.)*

Começo por colar a lista de ingredientes de um produto com glúten: flocos de aveia, malte de cevada, farinha de trigo, açúcar, óleo, sal, e que pode conter vestígios de frutos de casca rija.

*(Clicar em "Analisar".)*

O resultado é imediato. No topo, o veredicto: "Contém Glúten", a vermelho.

Em baixo, a tabela explicável. Reparem: a aveia, a cevada e o trigo estão marcadas com uma cruz vermelha, e cada uma diz porquê — "contém glúten, cereal ou derivado".

O açúcar, o óleo e o sal estão a verde, sem glúten conhecido.

E os frutos de casca rija aparecem a amarelo, porque são apenas um possível vestígio.

No fim, o sistema lista os alergénios e dá recomendações claras: produto inadequado para celíacos.

*(Limpar e colar o segundo texto.)*

Agora um produto seguro: água, puré de tomate, cenoura, cebola, azeite, sal, manjericão.

*(Clicar em "Analisar".)*

O veredicto muda para "Sem Glúten", a verde. É o mesmo motor — não está a adivinhar, está a aplicar regras sobre os ingredientes que reconhece.

*(Opcional: colar o terceiro texto, ou carregar uma imagem de data\sample_labels.)*

E quando os ingredientes são ambíguos — como amido modificado ou proteína vegetal hidrolisada — o sistema atribui um risco médio e sinaliza a dúvida, em vez de assumir.

A aplicação também aceita uma fotografia do rótulo, correndo o pipeline completo desde o OCR. Nesse caso a precisão depende da qualidade da imagem, como veremos a seguir.

---

## 5. Resultados e avaliação  ·  ~4:45–6:00

*(No ecrã: slide com a tabela de resultados.)*

Avaliámos o sistema de duas formas.

Na primeira, comparámos os modelos de aprendizagem automática. O melhor foi o Random Forest, com oitenta e oito vírgula sete por cento de exatidão no conjunto de teste.

Mas esta avaliação tem uma limitação: como os rótulos de treino foram gerados pelas próprias regras, mede sobretudo a capacidade de reproduzir essa lógica.

Por isso fizemos uma segunda avaliação, independente e não circular.

Aqui, o pipeline lê apenas o texto dos ingredientes, e comparamos o resultado com o campo de alergénios da base de dados Open Food Facts — um campo que o sistema nunca consulta.

Nesta avaliação, mais honesta, obtivemos noventa e um vírgula dois por cento de exatidão, com uma taxa de deteção de glúten de quase noventa por cento.

Este valor subiu de oitenta para noventa por cento quando alargámos o léxico ao inglês e ao francês.

---

## 6. Limitações e conclusão  ·  ~6:00–7:00

*(No ecrã: slide de limitações e conclusão.)*

Quanto às limitações, somos transparentes.

A maior fonte de erro é o OCR: em fotografias reais a confiança ronda os quarenta e oito por cento, e parte do texto perde-se. Por isso o sistema funciona melhor sobre texto limpo.

A base de dados também tem ruído — alguns produtos com glúten não o declaram — o que significa que a precisão real do nosso sistema é, em alguns casos, superior à que medimos.

E, por opção, preferimos assinalar risco a mais do que a menos: é a escolha mais segura para o consumidor.

*(Pausa.)*

Em conclusão: cumprimos todos os objetivos do enunciado. Construímos um sistema completo, da imagem ao relatório, que deteta glúten e alergénios, atribui um grau de risco e — acima de tudo — justifica cada decisão de forma explicável.

Obrigado pela atenção.

*(No ecrã: slide final com os nomes do grupo.)*
