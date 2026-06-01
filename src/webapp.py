"""App web (Flask) para analise de rotulos alimentares.

Interface simples para o pipeline completo da Fase 7: o utilizador cola o
texto dos ingredientes OU carrega a fotografia de um rotulo, e recebe o
relatorio (veredicto, tabela por ingrediente com cores, alergenios e
recomendacoes). E a concretizacao da "aplicacao" referida no enunciado.

Executar:
    pip install flask
    python src/webapp.py
    # abrir http://127.0.0.1:5000

A analise por imagem requer o Tesseract instalado (ver README). A analise
por texto funciona sem dependencias de sistema.
"""
from __future__ import annotations

import html
import tempfile
from pathlib import Path

from flask import Flask, request

from classifier_rules import (
    ALTO_RISCO,
    BAIXO_RISCO,
    CONTEM_GLUTEN,
    MEDIO_RISCO,
    SEM_GLUTEN,
)
from explain import SYM_AMBIG, SYM_GLUTEN, SYM_SAFE
from report import Report, report_from_image, report_from_text

app = Flask(__name__)

# cores por grau de risco e por simbolo
_GRADE_COLOR = {
    CONTEM_GLUTEN: "#d62728",
    ALTO_RISCO: "#e8590c",
    MEDIO_RISCO: "#f08c00",
    BAIXO_RISCO: "#f6c343",
    SEM_GLUTEN: "#2ca02c",
}
_SYM_BADGE = {
    SYM_GLUTEN: ("#d62728", "❌"),
    SYM_AMBIG: ("#f08c00", "⚠️"),
    SYM_SAFE: ("#2ca02c", "✅"),
}

PAGE = """<!doctype html>
<html lang="pt"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Análise de Rótulos — Glúten e Alergénios</title>
<style>
  :root {{ font-family: system-ui, Segoe UI, Roboto, sans-serif; }}
  body {{ max-width: 820px; margin: 1.5rem auto; padding: 0 1rem; color: #222; }}
  h1 {{ font-size: 1.5rem; }}
  textarea {{ width: 100%; min-height: 130px; font-size: 1rem; padding: .6rem;
            box-sizing: border-box; border: 1px solid #ccc; border-radius: 8px; }}
  .row {{ display: flex; gap: 1rem; flex-wrap: wrap; align-items: center;
          margin: .8rem 0; }}
  button {{ background: #3b7dd8; color: #fff; border: 0; border-radius: 8px;
           padding: .6rem 1.2rem; font-size: 1rem; cursor: pointer; }}
  .card {{ border: 1px solid #e3e3e3; border-radius: 12px; padding: 1rem 1.2rem;
          margin: 1rem 0; box-shadow: 0 1px 3px rgba(0,0,0,.05); }}
  .verdict {{ font-size: 1.2rem; font-weight: 600; color: #fff; padding: .4rem .9rem;
             border-radius: 999px; display: inline-block; }}
  table {{ border-collapse: collapse; width: 100%; margin-top: .5rem; }}
  th, td {{ text-align: left; padding: .45rem .6rem; border-bottom: 1px solid #eee; }}
  th {{ background: #fafafa; }}
  .badge {{ font-weight: 700; }}
  .muted {{ color: #777; font-size: .9rem; }}
  ul {{ margin: .3rem 0; }}
  .err {{ color: #d62728; }}
</style></head>
<body>
<h1>🥫 Análise de rótulos — glúten e alergénios</h1>
<p class="muted">Cole a lista de ingredientes ou carregue a foto de um rótulo.
A análise é explicável: cada ingrediente é justificado.</p>
<form method="post" enctype="multipart/form-data">
  <textarea name="texto" placeholder="Ingredientes: farinha de trigo, água, sal, amido modificado, leite. Pode conter traços de soja.">{texto}</textarea>
  <div class="row">
    <label>…ou imagem do rótulo: <input type="file" name="imagem" accept="image/*"></label>
    <button type="submit">Analisar</button>
  </div>
</form>
{result}
</body></html>"""


def _esc(s) -> str:
    return html.escape(str(s))


def render_result_html(rep: Report) -> str:
    a = rep.explanation.assessment
    grade_color = _GRADE_COLOR.get(rep.gluten_grade, "#555")

    rows = []
    for r in rep.explanation.rows:
        color, emoji = _SYM_BADGE[r.symbol]
        rows.append(
            f"<tr><td>{_esc(r.ingredient)}</td>"
            f"<td class='badge' style='color:{color}'>{emoji}</td>"
            f"<td>{_esc(r.observation)}</td></tr>"
        )
    table = "\n".join(rows) or "<tr><td colspan='3' class='muted'>Nenhum ingrediente reconhecido.</td></tr>"

    if a.allergens:
        allerg = "<ul>" + "".join(
            f"<li>{_esc(k)} <span class='muted'>({_esc(v)})</span></li>"
            for k, v in a.allergens.items()) + "</ul>"
    else:
        allerg = "<p class='muted'>Nenhum dos 14 alergénios obrigatórios detetado.</p>"

    recs = "<ul>" + "".join(f"<li>{_esc(x)}</li>" for x in rep.recommendations) + "</ul>"

    unknown = ""
    if rep.explanation.n_unknown:
        unknown = (f"<p class='muted'>{rep.explanation.n_unknown} segmento(s) de "
                   "texto não reconhecido(s) (ver limitações de OCR).</p>")

    return f"""
<div class="card">
  <h2>Resumo</h2>
  <p><span class="verdict" style="background:{grade_color}">{_esc(rep.gluten_grade)}</span>
     &nbsp; Alergénios: <strong>{_esc(a.allergen_status)}</strong></p>
</div>
<div class="card">
  <h2>Análise dos ingredientes</h2>
  <table><tr><th>Ingrediente</th><th>Estado</th><th>Observação</th></tr>
  {table}
  </table>
  {unknown}
</div>
<div class="card">
  <h2>Alergénios detetados</h2>
  {allerg}
</div>
<div class="card">
  <h2>Recomendações</h2>
  {recs}
</div>"""


@app.route("/", methods=["GET", "POST"])
def index():
    texto = ""
    result = ""
    if request.method == "POST":
        file = request.files.get("imagem")
        texto = (request.form.get("texto") or "").strip()
        try:
            if file and file.filename:
                suffix = Path(file.filename).suffix or ".jpg"
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    file.save(tmp.name)
                    tmp_path = tmp.name
                rep = report_from_image(tmp_path)
                Path(tmp_path).unlink(missing_ok=True)
                result = render_result_html(rep)
                texto = ""
            elif texto:
                result = render_result_html(report_from_text(texto))
            else:
                result = "<p class='err'>Forneça texto ou uma imagem.</p>"
        except Exception as exc:  # noqa: BLE001
            result = (f"<p class='err'>Erro ao analisar: {_esc(exc)}<br>"
                      "<span class='muted'>A análise por imagem requer o Tesseract "
                      "instalado (ver README).</span></p>")

    return PAGE.format(texto=_esc(texto), result=result)


def main() -> None:
    app.run(host="127.0.0.1", port=5000, debug=False)


if __name__ == "__main__":
    main()
