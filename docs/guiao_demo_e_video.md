# Guião de demo (app Flask) + Guia do vídeo-relatório

---

# PARTE 1 — Demo passo-a-passo da app Flask

> Objetivo: mostrar o pipeline completo ao vivo, sem surpresas. Ensaia 1x antes.

## A. Antes de começar (preparação — fazer ANTES da apresentação)

1. Abrir o terminal (PowerShell) na pasta do projeto:
   ```powershell
   cd D:\Users\160173003\Desktop\trabalho-de-ia
   ```
2. Garantir que o Flask está instalado:
   ```powershell
   pip install flask
   ```
3. **Arrancar a app:**
   ```powershell
   python src\webapp.py
   ```
   Deve aparecer `Running on http://127.0.0.1:5000`.
4. Abrir o browser em **http://127.0.0.1:5000** e confirmar que a página carrega.
5. Deixar o terminal a correr num canto do ecrã (mostra que está vivo).

> ⚠️ **Plano B:** se a app não arrancar ao vivo, tens screenshots/o vídeo como
> recurso. Nunca deixes a demo bloquear a apresentação.

## B. Demo 1 — análise por TEXTO (a mais segura, NÃO precisa de Tesseract)

> Começa SEMPRE por texto: é instantânea e fiável. Faz primeiro um caso "mau"
> (com glúten) e depois um "bom" (sem glúten) para mostrar o contraste.

**Passo 1 — caso COM glúten + vestígios.** Cola na caixa de texto:

```
Flocos de aveia, malte de cevada, farinha de trigo, açúcar, óleo de girassol, sal. Pode conter vestígios de frutos de casca rija.
```

Clica **Analisar**. Aponta para o ecrã e explica o que aparece:
- **Resumo:** crachá vermelho **"Contém Gluten"** + alergénios "Possui alergénios".
- **Tabela por ingrediente:** ❌ na aveia/cevada/trigo, ✅ no açúcar/óleo/sal,
  ⚠️ nos frutos de casca rija (só declarados como possível traço).
  → *"Repare que cada veredicto é justificado linha a linha — é a explicabilidade."*
- **Alergénios detetados** e **Recomendações** ("INADEQUADO para celíacos…").

**Passo 2 — caso SEM glúten.** Limpa e cola:

```
Água, puré de tomate, cenoura, cebola, azeite, sal, manjericão.
```

Clica **Analisar** → crachá **verde "Sem Glúten"**.
→ *"O mesmo motor, resultado oposto — não está a adivinhar, está a aplicar regras sobre os ingredientes reconhecidos."*

**Passo 3 (opcional) — caso AMBÍGUO.** Mostra a classe "suspeito":

```
Amido modificado, aroma natural, dextrose, lecitina, proteína vegetal hidrolisada.
```

→ Veredicto intermédio (⚠️) — *"ingredientes ambíguos que podem ou não conter glúten conforme a origem; o sistema sinaliza em vez de assumir."*

## C. Demo 2 — análise por IMAGEM (só se o Tesseract estiver OK)

> Mostra o OCR a funcionar, mas **avisa que é a maior fonte de erro** (~48% em fotos reais).

1. No campo **"…ou imagem do rótulo"**, carrega uma imagem de:
   `data\sample_labels\` (ex.: `4056489872054.jpg` — Crunchy Muesli, dá "Contém/Médio").
2. Clica **Analisar**.
3. Explica: *"Aqui corre o pipeline todo — pré-processamento OpenCV → Tesseract →
   limpeza → NLP → regras → relatório. Em fotos reais a confiança ronda os 48%, por
   isso o veredicto pode sair menos grave que o real; é uma limitação que documentámos."*

> Se a imagem falhar, a própria app mostra a mensagem a dizer que precisa do
> Tesseract — assume com naturalidade e volta ao modo texto.

## D. Frase de fecho da demo

*"Em resumo: a app concretiza o que o enunciado pedia — recebe um rótulo (texto ou
foto), devolve o veredicto de glúten, os 14 alergénios da UE, e uma justificação
ingrediente a ingrediente. É explicável de ponta a ponta."*

## E. Checklist rápida (lê 2 min antes)

- [ ] `python src\webapp.py` a correr e browser aberto na página
- [ ] Os 3 textos de exemplo copiados para um bloco de notas (cola rápida)
- [ ] 1 imagem de `data\sample_labels\` localizada
- [ ] Terminal visível (prova que está vivo)
- [ ] Screenshots de reserva caso algo falhe

---

# PARTE 2 — Guia para criar o vídeo-relatório

> Um vídeo-relatório é a apresentação narrada e gravada do trabalho. Objetivo:
> claro, curto e que mostra o sistema a funcionar. **Alvo: 5–8 minutos.**

## A. Estrutura sugerida (guião do vídeo, com tempos)

| # | Secção | Duração | O que dizer / mostrar |
|---|---|---|---|
| 1 | **Abertura** | 0:00–0:30 | Nome do trabalho, disciplina, nomes do grupo (3). O problema: "ler um rótulo e saber se tem glúten/alergénios é difícil para quem tem restrições". |
| 2 | **Objetivo** | 0:30–1:15 | O *pitch*: foto → glúten + 14 alergénios UE + ingredientes ambíguos + grau de risco + **justificação explicável**. |
| 3 | **Arquitetura** | 1:15–2:30 | Mostra o **diagrama do pipeline** (já existe em `docs/`): OCR → NLP → regras+ML → explicação → relatório → avaliação. Diz porque **não** um LLM (reutilizar conceitos das aulas + explicabilidade). |
| 4 | **Demo ao vivo (gravada)** | 2:30–4:30 | Grava o ecrã da app Flask: caso com glúten, caso sem glúten, (opcional) imagem. É a parte mais importante — **mostra, não contes**. |
| 5 | **Resultados / avaliação** | 4:30–6:00 | Os números: RF 88,7%; avaliação **B não-circular 91,2%**, recall glúten 89,9%; OCR ~48%. Explica a diferença A vs B. |
| 6 | **Limitações + conclusão** | 6:00–7:00 | OCR é o gargalo; supervisão fraca; ground-truth ruidoso. Conclusão: objetivos cumpridos, app funcional, sistema explicável. |

## B. Preparar o material (antes de gravar)

1. **Slides** (poucos, limpos): 1 título · 1 problema/objetivo · 1 diagrama do
   pipeline · 1 tabela de resultados · 1 limitações/conclusão. (Reaproveita figuras
   de `docs/figures/` e o diagrama do pipeline já existente.)
2. **Escreve o guião falado** — frase a frase. Lê em voz alta e cronometra.
3. **Ensaia a demo** uma vez (ver Parte 1) para gravar sem hesitações.
4. **Prepara os textos de exemplo** copiados, para colar de imediato no vídeo.

## C. Gravação do ecrã (Windows — sem instalar nada)

**Opção rápida — Xbox Game Bar (já vem no Windows 11):**
1. Carrega `Win + G` → abre a barra de jogo.
2. No widget **Captura**, clica no botão de gravar (ou `Win + Alt + R` para começar/parar).
3. Grava o ecrã com a app + a tua narração pelo microfone.
4. O vídeo fica em `Vídeos\Capturas`.

**Opção com mais controlo (recomendada):** **OBS Studio** (gratuito)
- *Display Capture* para o ecrã + *Audio Input* para o microfone.
- Permite gravar slides e app na mesma sessão e tem melhor qualidade.

> Dica: grava em **1080p**, fala devagar, e mostra sempre o cursor a apontar para
> o que estás a explicar.

## D. Sugestão de fluxo de gravação (para editar pouco)

1. Grava os **slides 1–3** (abertura, objetivo, arquitetura) a falar por cima.
2. Pára. Muda para a app e grava a **demo (secção 4)** de uma só vez.
3. Volta aos **slides 5–6** (resultados, limitações, conclusão).
4. **Edita:** junta os 3 blocos pela ordem certa. Editor simples gratuito:
   **Clipchamp** (já vem no Windows 11) ou o editor do *Fotos*.
5. Corta silêncios/erros, adiciona um título inicial com os nomes do grupo.
6. **Exporta em MP4 1080p.** Confirma que o áudio se ouve bem e que o texto da app
   é legível.

## E. Erros comuns a evitar

- ❌ Vídeo demasiado longo → mantém-te nos 5–8 min, corta o que é repetido.
- ❌ Ler slides cheios de texto → slides com poucas palavras, explicação na voz.
- ❌ Demo a falhar na gravação → ensaia antes; se a imagem/OCR der erro, usa só texto.
- ❌ Áudio baixo/ruidoso → grava num sítio silencioso, testa o microfone primeiro.
- ❌ Esquecer os nomes do grupo e a disciplina no início.

## F. Checklist final do vídeo

- [ ] Abertura com nomes do grupo + disciplina
- [ ] Diagrama do pipeline aparece e é explicado
- [ ] Demo ao vivo (texto com glúten + sem glúten) gravada e legível
- [ ] Números de avaliação corretos (88,7% / 91,2% / recall 89,9% / OCR ~48%)
- [ ] Limitações assumidas
- [ ] Duração 5–8 min · MP4 1080p · áudio audível
