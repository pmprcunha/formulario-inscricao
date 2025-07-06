"""
Scheduler & Interface
=====================

Este ficheiro Python oferece **dois modos**:

1. **Wizard/Resumo CLI** – cria ou lê `alunos.csv`
2. **Interface web moderna** – app Streamlit para marcar preferências

Modo simplificado: se nenhum ficheiro for indicado, será usado `alunos.csv` por defeito.

Execute com:
```bash
# Wizard ou resumo
python scheduler.py --wizard             # abre o wizard
python scheduler.py                      # mostra resumo

# Interface web
streamlit run scheduler.py -- --app
```

Dependências:
    pip install streamlit pandas python-dateutil ortools
"""

# SECTION 0 ────────────── CSV Wizard ─────────────────────────

import csv
from pathlib import Path
from typing import Dict, List, Set, Tuple
from datetime import datetime, timedelta
import sys

CSV_FIELDS = [
    "id", "nome", "nivel", "preferencias", "dias", "slots_por_dia", "aulas_semanais"
]
DEFAULT_CSV = Path("alunos.csv")


def run_wizard(csv_path: Path) -> None:
    file_exists = csv_path.exists()
    mode = "a" if file_exists else "w"

    with csv_path.open(mode, newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        if not file_exists:
            writer.writeheader()

        while True:
            print("\n──── Novo aluno (ENTER em ID para terminar) ────")
            sid = input("ID: ").strip()
            if not sid:
                break
            nome = input("Nome: ").strip()
            nivel = input("Nível (Iniciante/Intermédio/Avançado): ").strip()
            pref = input("Preferência geral (manhã; almoço; tarde; noite): ").strip()
            dias = input("Dias (ex: 2ª 3ª 5ª): ").strip()
            slots = input("Slots por dia (ex: m1 m2 a1): ").strip()
            aulas = input("Aulas por semana (número): ").strip()

            writer.writerow({
                "id": sid,
                "nome": nome,
                "nivel": nivel,
                "preferencias": pref,
                "dias": dias,
                "slots_por_dia": slots,
                "aulas_semanais": aulas,
            })
            print("✔ Adicionado! (ENTER para continuar, Ctrl-C para sair)")
            input()

    print(f"\n✅ Ficheiro CSV guardado em: {csv_path.resolve()}")

# SECTION 1 ────────────── Data ingestion helpers ────────────

CAPACITY: int = 4


def read_students(csv_path: Path) -> Tuple[List[str], Dict[str, Set[str]], Dict[str, int]]:
    students: List[str] = []
    prefs: Dict[str, Set[str]] = {}
    weekly_load: Dict[str, int] = {}

    with csv_path.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            sid = row["id"].strip()
            students.append(sid)

            days = row["dias"].split()
            day_slots = row["slots_por_dia"].split()
            prefs[sid] = {
                f"{day}-{slot}" for day in days for slot in day_slots
            }
            weekly_load[sid] = int(row["aulas_semanais"].strip())

    return students, prefs, weekly_load


def build_slot_universe(prefs: Dict[str, Set[str]]) -> List[str]:
    return sorted({slot for slot_set in prefs.values() for slot in slot_set})

# SECTION 2 ────────────── Web interface (Streamlit) ─────────

def run_app(csv_path: Path):
    import streamlit as st
    import pandas as pd
    import numpy as np

    st.set_page_config(page_title="Preferências de Horário", layout="wide")
    st.title("🗓️ Preferências de Horário (2ª-6ª, 08:00-22:00, 30 min)")

    with st.form("identificacao", clear_on_submit=False):
        col1, col2 = st.columns(2)
        sid = col1.text_input("ID do aluno")
        nome = col2.text_input("Nome completo")
        nivel = st.selectbox("Nível", ["Iniciante", "Intermédio", "Avançado"])
        aulas_semanais = st.number_input("Aulas por semana", 1, 5, step=1, value=1)
        submitted_id = st.form_submit_button("Avançar para horário ➡")

    if submitted_id and not sid:
        st.warning("⚠️ Por favor indique um ID.")
        st.stop()

    if sid:
        st.header("Selecione os slots desejados ⬇")

        days_pt = ["2ª", "3ª", "4ª", "5ª", "6ª"]
        start_t = datetime.strptime("08:00", "%H:%M")
        end_t = datetime.strptime("22:00", "%H:%M")
        delta = timedelta(minutes=30)
        times = []
        tt = start_t
        while tt < end_t:
            times.append(tt.strftime("%H:%M"))
            tt += delta

        df = pd.DataFrame(
            data=np.full((len(times), len(days_pt)), False),
            index=times,
            columns=days_pt,
        )

        edited = st.data_editor(
            df,
            num_rows="fixed",
            use_container_width=True,
            hide_index=False,
            column_config={d: st.column_config.CheckboxColumn(required=False) for d in days_pt},
        )

        if st.button("💾 Guardar preferências"):
            selecionados: List[str] = []
            for day in days_pt:
                for time_str in times:
                    if edited.at[time_str, day]:
                        selecionados.append(f"{day}-{time_str}")
            row = {
                "id": sid,
                "nome": nome,
                "nivel": nivel,
                "preferencias": "; ".join(sorted({s.split("-")[1][:2] for s in selecionados})),
                "dias": " ".join(sorted({s.split("-")[0] for s in selecionados})),
                "slots_por_dia": " ".join(sorted({s.split("-")[1] for s in selecionados})),
                "aulas_semanais": str(aulas_semanais),
            }
            rows: List[Dict[str, str]] = []
            if csv_path.exists():
                with csv_path.open(newline="", encoding="utf-8") as fh:
                    reader = csv.DictReader(fh)
                    for r in reader:
                        if r["id"] != sid:
                            rows.append(r)
            rows.append(row)
            with csv_path.open("w", newline="", encoding="utf-8") as fh:
                writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
                writer.writeheader()
                writer.writerows(rows)
            st.success("✅ Preferências guardadas! Pode fechar a página.")

# SECTION 3 ────────────── CLI helper ─────────────────────────

if __name__ == "__main__":
    import argparse
    import pprint

    parser = argparse.ArgumentParser(
        description="Wizard, resumo ou interface web para recolher preferências.",
        epilog=(
            "Exemplos:\n"
            "  python scheduler.py --wizard\n"
            "  python scheduler.py\n"
            "  streamlit run scheduler.py -- --app\n"
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("csv", type=Path, nargs="?", default=DEFAULT_CSV, help="Ficheiro CSV (opcional, default: alunos.csv)")
    parser.add_argument("--wizard", action="store_true", help="Arranca wizard interativo no terminal")
    parser.add_argument("--app", action="store_true", help="Lança interface Streamlit")
    args = parser.parse_args()

    if args.app:
        run_app(args.csv)
        sys.exit(0)

    if args.wizard or not args.csv.exists():
        print("\n=== Modo Wizard ===")
        run_wizard(args.csv)
        if not input("\nProsseguir para resumo? (ENTER=sim, q=não) ").lower().startswith("q"):
            pass
        else:
            sys.exit(0)

    print("\n=== Resumo dos dados lidos ===")
    students, prefs, weekly_load = read_students(args.csv)
    slots = build_slot_universe(prefs)

    print("\n• IDs:")
    pprint.pprint(students)
    print("\n• Aulas/semana por aluno:")
    pprint.pprint(weekly_load)
    print("\n• Universo de slots:")
    pprint.pprint(slots)


