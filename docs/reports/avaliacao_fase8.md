# Fase 8 - Avaliacao e validacao do sistema

## A) Modelo supervisionado (Random Forest) - conjunto de teste

Amostras de teste: 2193
Exatidao=88.69%  macro-F1=88.13%  macro-P=87.87%  macro-R=88.61%

Matriz de confusao (linhas=real, colunas=previsto):
```
	contem	sem	suspeito	
contem	558	15	14	
sem	3	977	131	
suspeito	5	80	410
```
- contem: P=98.6%  R=95.1%  F1=96.8%
- sem: P=91.1%  R=87.9%  F1=89.5%
- suspeito: P=73.9%  R=82.8%  F1=78.1%

## B) Pipeline NLP+regras sobre texto livre vs. rotulo independente

Ground-truth: campo `allergens` da OFF contem `en:gluten` (sim/nao).
O pipeline so le `ingredients_text` -> avaliacao nao circular.

Produtos avaliados: 1500
Exatidao=91.20%  macro-F1=90.44%  macro-P=90.05%  macro-R=90.91%

Matriz de confusao (linhas=real, colunas=previsto):
```
	contem	sem	
contem	473	53	
sem	79	895
```
- contem: P=85.7%  R=89.9%  F1=87.8%
- sem: P=94.4%  R=91.9%  F1=93.1%

Exemplos de FALSOS NEGATIVOS (allergens diz gluten, pipeline nao detetou):
  - Papa Infantil multicereais e banana: "Farinhas (88%) (farinha de milho*, farinha de arroz*, farinha de _aveia*_), flocos de bana"
  - Special K Classic: "Arroz (47%), trigo integral (37%), azúcar, cebada (5%), harina de malta de cebada, sal, ex"
  - Lindor Latte: "Zucchero, grasso vegetale (cocco, palmisti), burro di cacao, pasta di cacao, _latte_ inter"

Exemplos de FALSOS POSITIVOS (pipeline detetou gluten, allergens nao lista):
  - Almôndegas de Bovino: "Carne de bovino (60%), proteína de soja hidratada (19%), água, pão ralado (farinha de trig"
  - 4 Queijos: "Recheio 58%: queijo ricotta 50% (soro de leite, leite, sal), queijo Parmigiano Reggiano DO"
  - Massa De Pescada Com Molho Chimichurri: "Massa cozida (42%) (água, sêmola de trigo-duro, ovo inteiro em pó, sal), pescada-do-Cabo ("

## C) Impacto do OCR (5 imagens reais)

| Produto | Conf. OCR | Veredicto (referencia) | Veredicto (OCR) |
| --- | --- | --- | --- |
| Greek White panetto | 48% | Medio Risco | Medio Risco |
| Ranch | 39% | Medio Risco | Baixo Risco |
| Puré de Batata em pó | 58% | Medio Risco | Medio Risco |
| Crunchy Muesli Fruta | 47% | Contem Gluten | Medio Risco |
| Pizza Fresca Fiambre e Queij | 47% | Contem Gluten | Baixo Risco |

## Limitacoes e discussao

- **OCR e a maior fonte de erro.** Em fotografias reais (confianca media ~48%)
  grande parte do texto nao e recuperada, pelo que o veredicto a partir da
  imagem e frequentemente menos grave do que o real (ver seccao C). O sistema
  funciona muito melhor sobre texto de ingredientes limpo.
- **Lingua do texto.** O lexico cobre PT + EN + FR (juntar EN/FR subiu a
  exatidao da avaliacao B de ~88% para ~91% e o recall de gluten de 80% para
  ~90%). Os falsos negativos remanescentes sao sobretudo texto em italiano
  ("latte", "cebada") e espanhol; extensao natural: juntar IT/ES ou usar a
  coluna normalizada `ingredients_tags` quando disponivel.
- **Ground-truth ruidoso (seccao B).** O campo `allergens` da OFF e preenchido
  por contribuidores e tem falsos negativos (produtos com gluten sem o declarar).
  Varios "falsos positivos" do pipeline sao, na verdade, deteccoes CORRETAS que
  o rotulo OFF omitiu (ex.: "pao ralado (farinha de trigo)", "semola de trigo-
  duro") -- ou seja, a precisao real e superior a medida.
- **Mojibake do dump OFF.** Alguns textos trazem caracteres corrompidos
  (ex.: "prote�na", "�gua"), o que tambem prejudica o reconhecimento; por isso
  a Fase 2 preferiu a coluna normalizada `ingredients_tags` para a estatistica.
- **Supervisao fraca (Fase 5).** Os classificadores foram treinados com rotulos
  gerados pelas proprias regras; medem sobretudo a capacidade de reproduzir a
  logica de regras a partir do "bag-of-tags", nao um juizo humano independente.
- **Matching difuso favorece o recall.** Ha falsos positivos por semelhanca
  (ex.: "lactone" ~ "lactose"). E uma escolha deliberada (mais seguro sobre-
  assinalar risco), mas reduz a precisao.
- **Cobertura do lexico PT.** Ingredientes fora do lexico ficam por classificar;
  a aveia e tratada como gluten por precaucao (contaminacao cruzada frequente).
