from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime
import json, os, tempfile
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Flask app
app = Flask(__name__)
app.secret_key = "change-me"  # Trocar em produção

# Google Sheets
SHEET_NAME = "Inscricoes Padel"
CREDS_FILE = "credentials.json"
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

def enviar_para_google_sheets(dados):
    creds_dict = json.loads(os.environ["GOOGLE_CREDS_JSON"])
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as tmp:
        json.dump(creds_dict, tmp)
        tmp.flush()
        creds = ServiceAccountCredentials.from_json_keyfile_name(tmp.name, SCOPE)
        client = gspread.authorize(creds)
        sheet = client.open(SHEET_NAME).sheet1
        sheet.append_row(dados, value_input_option="USER_ENTERED")

# Rota principal
@app.route("/", methods=["GET", "POST"])
def formulario():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip()
        contacto = request.form.get("contacto", "").strip()
        treinos_semana = request.form.get("treinos_semana", "")
        tipo_treino = request.form.get("tipo_treino", "")
        genero_turma = request.form.get("genero_turma", "Indiferente")

        disponibilidade = {}
        for dia in ("2a", "3a", "4a", "5a", "6a"):
            blocos = []
            inicios = request.form.getlist(f"{dia}_inicio")
            fins = request.form.getlist(f"{dia}_fim")
            for ini, fim in zip(inicios, fins):
                if ini and fim:
                    try:
                        t_ini = datetime.strptime(ini, "%H:%M")
                        t_fim = datetime.strptime(fim, "%H:%M")
                    except ValueError:
                        flash("Formato de hora inválido.", "danger")
                        return redirect(url_for("formulario"))
                    if t_ini >= t_fim:
                        flash("A hora inicial deve ser menor que a final.", "danger")
                        return redirect(url_for("formulario"))
                    blocos.append([ini, fim])
            if blocos:
                disponibilidade[dia] = blocos

        # Validações
        if not nome or not email or not contacto:
            flash("Preenche todos os campos obrigatórios.", "danger")
            return redirect(url_for("formulario"))
        if not disponibilidade:
            flash("Seleciona pelo menos um intervalo de disponibilidade.", "danger")
            return redirect(url_for("formulario"))

        dados = [nome, email, contacto, treinos_semana, tipo_treino, genero_turma, json.dumps(disponibilidade, ensure_ascii=False)]
        try:
            enviar_para_google_sheets(dados)
            flash("Inscrição submetida com sucesso!", "success")
        except Exception as e:
            flash(f"Erro ao guardar dados: {e}", "danger")

        return redirect(url_for("formulario"))

    return render_template("formulario.html")

# Execução
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=5000, type=int)
    args = parser.parse_args()

    app.run(host=args.host, port=args.port, debug=True)





