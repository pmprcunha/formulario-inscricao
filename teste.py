# ------------------------------
#  Flask Application Structure
# ------------------------------
# project/
# ├─ app.py
# ├─ alunos.csv  (auto‑created on first submission)
# ├─ templates/
# │    └─ formulario.html
# └─ static/
#      └─ style.css
#
# 1. Place this app.py at project root.
# 2. Put "formulario.html" inside a folder named templates.
# 3. Put "style.css" inside a folder named static.
# 4. Install Flask:  pip install Flask
# 5. Run locally for testing:  python app.py  (opens on http://127.0.0.1:5000)
# 6. For LAN sharing:  python app.py --host 0.0.0.0
# 7. Deploy to Render / PythonAnywhere / VPS as preferred.
#
# ------------------ app.py ------------------
from pathlib import Path
import csv
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = "change-me"  # Needed for flash messages
CSV_PATH = Path("alunos.csv")

# ------------------------------------------------------------
# Helper: ensure CSV header present
# ------------------------------------------------------------
def write_row(row):
    need_header = not CSV_PATH.exists()
    with CSV_PATH.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if need_header:
            writer.writerow(["Nome", "Treinos/Semana", "Tipo Treino", "Género Turma", "Disponibilidade"])
        writer.writerow(row)

# ------------------------------------------------------------
# Routes
# ------------------------------------------------------------
@app.route("/", methods=["GET", "POST"])
def formulario():
    if request.method == "POST":
        # --- Basic fields ---
        nome = request.form.get("nome", "").strip()
        treinos_semana = request.form.get("treinos_semana", "")
        tipo_treino = request.form.get("tipo_treino", "1h")
        genero_turma = request.form.get("genero_turma", "Indiferente")

        # --- Disponibilidade ---
        disponibilidade = {}
        for dia in ("2a", "3a", "4a", "5a", "6a"):
            blocos = []
            inicios = request.form.getlist(f"{dia}_inicio")
            fins    = request.form.getlist(f"{dia}_fim")
            for ini, fim in zip(inicios, fins):
                if ini and fim:
                    try:
                        t_ini = datetime.strptime(ini, "%H:%M")
                        t_fim = datetime.strptime(fim, "%H:%M")
                    except ValueError:
                        flash("Formato de hora inválido.", "danger")
                        return redirect(url_for("formulario"))
                    if t_ini >= t_fim:
                        flash("Em cada intervalo a hora inicial deve ser menor que a final.", "danger")
                        return redirect(url_for("formulario"))
                    blocos.append([ini, fim])
            if blocos:
                disponibilidade[dia] = blocos

        # --- Validation ---
        if not nome:
            flash("O nome é obrigatório.", "danger")
            return redirect(url_for("formulario"))
        if not disponibilidade:
            flash("Seleciona pelo menos um intervalo de disponibilidade.", "danger")
            return redirect(url_for("formulario"))

        # --- Persist ---
        write_row([
            nome,
            treinos_semana,
            tipo_treino,
            genero_turma,
            json.dumps(disponibilidade, ensure_ascii=False)
        ])

        flash("Dados submetidos com sucesso!", "success")
        return redirect(url_for("formulario"))

    # GET
    return render_template("formulario.html")

# ------------------------------------------------------------
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=5000, type=int)
    args = parser.parse_args()

    app.run(host=args.host, port=args.port, debug=True)

# ------------------ templates/formulario.html ------------------
# (Coloca este conteúdo em templates/formulario.html)
"""
<!DOCTYPE html>
<html lang="pt">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Inscrição de Aluno</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <link href="{{ url_for('static', filename='style.css') }}" rel="stylesheet" />
</head>
<body class="bg-light">
<div class="container py-5">
  <div class="col-lg-8 mx-auto bg-white p-4 shadow-sm rounded-3">
    <h2 class="mb-4 text-center">Formulário de Inscrição</h2>

    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}
        {% for category, msg in messages %}
          <div class="alert alert-{{category}}">{{ msg }}</div>
        {% endfor %}
      {% endif %}
    {% endwith %}

    <form method="post" novalidate>
      <!-- Nome -->
      <div class="mb-3">
        <label class="form-label">Nome completo</label>
        <input type="text" name="nome" class="form-control" required />
      </div>

      <!-- Treinos / semana -->
      <div class="mb-3">
        <label class="form-label">Número de treinos por semana</label>
        <input type="number" name="treinos_semana" class="form-control" min="1" max="7" value="2" />
      </div>

      <!-- Tipo de treino -->
      <div class="mb-3">
        <label class="form-label d-block">Tipo de treino preferido</label>
        <div class="form-check form-check-inline">
          <input class="form-check-input" type="radio" name="tipo_treino" value="1h" checked />
          <label class="form-check-label">1h</label>
        </div>
        <div class="form-check form-check-inline">
          <input class="form-check-input" type="radio" name="tipo_treino" value="1h30" />
          <label class="form-check-label">Competição (1h30)</label>
        </div>
      </div>

      <!-- Género -->
      <div class="mb-3">
        <label class="form-label">Tipo de turma preferido</label>
        <select name="genero_turma" class="form-select">
          <option>Masculina</option>
          <option>Feminina</option>
          <option>Mista</option>
          <option selected>Indiferente</option>
        </select>
      </div>

      <!-- Tabs Dias -->
      <ul class="nav nav-tabs mb-3" id="diaTabs" role="tablist">
        {% for idx, dia in enumerate(['2a','3a','4a','5a','6a']) %}
        <li class="nav-item" role="presentation">
          <button class="nav-link {% if idx==0 %}active{% endif %}" id="tab-{{dia}}" data-bs-toggle="tab" data-bs-target="#pane-{{dia}}" type="button" role="tab">{{ dia[:-1] }}ª feira</button>
        </li>
        {% endfor %}
      </ul>
      <div class="tab-content">
        {% for idx, dia in enumerate(['2a','3a','4a','5a','6a']) %}
        <div class="tab-pane fade {% if idx==0 %}show active{% endif %}" id="pane-{{dia}}" role="tabpanel">
          <div id="rows-{{dia}}"></div>
          <button type="button" class="btn btn-outline-primary btn-sm mt-2" onclick="addRow('{{dia}}')">+ Adicionar intervalo</button>
        </div>
        {% endfor %}
      </div>

      <div class="text-center mt-4">
        <button type="submit" class="btn btn-success px-5">Submeter</button>
      </div>
    </form>
  </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
<script>
  const dias = ['2a','3a','4a','5a','6a'];

  // Adiciona linha default por dia
  dias.forEach(d => addRow(d));

  function addRow(dia) {
    const container = document.getElementById("rows-"+dia);
    const div = document.createElement("div");
    div.className = "row g-2 align-items-center mb-1";
    div.innerHTML = `
      <div class="col-auto">
        <input type="time" name="${dia}_inicio" class="form-control" step="1800" required>
      </div>
      <div class="col-auto">&#8594;</div>
      <div class="col-auto">
        <input type="time" name="${dia}_fim" class="form-control" step="1800" required>
      </div>
      <div class="col-auto">
        <button type="button" class="btn btn-danger btn-sm" onclick="this.parentNode.remove()">&times;</button>
      </div>`;
    container.appendChild(div);
  }
</script>
</body>
</html>
"""

# ------------------ static/style.css ------------------
# (Coloca este conteúdo em static/style.css)
"""
body {
  font-family: "Helvetica Neue", Arial, sans-serif;
}
.nav-tabs .nav-link {
  font-weight: 500;
}
"""




