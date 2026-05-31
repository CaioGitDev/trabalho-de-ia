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
Exatidao=87.93%  macro-F1=86.58%  macro-P=87.12%  macro-R=86.12%

Matriz de confusao (linhas=real, colunas=previsto):
```
	contem	sem	
contem	421	105	
sem	76	898
```
- contem: P=84.7%  R=80.0%  F1=82.3%
- sem: P=89.5%  R=92.2%  F1=90.8%

Exemplos de FALSOS NEGATIVOS (allergens diz gluten, pipeline nao detetou):
  - Twix: "Sugar, glucose syrup, _wheat_ flour, palm fat, skimmed _milk_ powder, cocoa butter, cocoa "
  - Crunchy Granola - Meusli Croustillant: "Flocons d'avoine complets (71,6 %), sucre, raisins 7,5% (sultana, huile de tournesol et de"
  - Bolachas fruit & shape frutos silvestres: "WHEAT FLOUR, RAISINS (19,2%), FOREST FRUIT FILLING (12,8%) (GLUCOSE SYRUP, DEXTROSE, HUMEC"

Exemplos de FALSOS POSITIVOS (pipeline detetou gluten, allergens nao lista):
  - Almôndegas de Bovino: "Carne de bovino (60%), proteína de soja hidratada (19%), água, pão ralado (farinha de trig"
  - 4 Queijos: "Recheio 58%: queijo ricotta 50% (soro de leite, leite, sal), queijo Parmigiano Reggiano DO"
  - Massa De Pescada Com Molho Chimichurri: "Massa cozida (42%) (água, sêmola de trigo-duro, ovo inteiro em pó, sal), pescada-do-Cabo ("

## C) Impacto do OCR (5 imagens reais)

| Produto | Conf. OCR | Veredicto (referencia) | Veredicto (OCR) |
| --- | --- | --- | --- |
| Greek White panetto | 48% | Baixo Risco | Medio Risco |
| Ranch | 39% | Medio Risco | Baixo Risco |
| Puré de Batata em pó | 58% | Medio Risco | Medio Risco |
| Crunchy Muesli Fruta | 47% | Contem Gluten | Medio Risco |
| Pizza Fresca Fiambre e Queij | 47% | Contem Gluten | Baixo Risco |

## Limitacoes e discussao

- **OCR e a maior fonte de erro.** Em fotografias reais (confianca media ~48%)
  grande parte do texto nao e recuperada, pelo que o veredicto a partir da
  imagem e frequentemente menos grave do que o real (ver seccao C). O sistema
  funciona muito melhor sobre texto de ingredientes limpo.
- **Ground-truth ruidoso (seccao B).** O campo `allergens` da OFF e preenchido
  por contribuidores e tem falsos negativos (produtos com gluten sem o declarar).
  Parte dos "falsos positivos" do pipeline sao, na verdade, deteccoes corretas
  que o rotulo OFF omitiu.
- **Supervisao fraca (Fase 5).** Os classificadores foram treinados com rotulos
  gerados pelas proprias regras; medem sobretudo a capacidade de reproduzir a
  logica de regras a partir do "bag-of-tags", nao um juizo humano independente.
- **Matching difuso favorece o recall.** Ha falsos positivos por semelhanca
  (ex.: "lactone" ~ "lactose"). E uma escolha deliberada (mais seguro sobre-
  assinalar risco), mas reduz a precisao.
- **Cobertura do lexico PT.** Ingredientes fora do lexico ficam por classificar;
  a aveia e tratada como gluten por precaucao (contaminacao cruzada frequente).
