from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
import sqlite3
import os
from datetime import datetime

app = FastAPI()
DB_FILE = "oficina.db"

# Configuração de Vagas
MAX_VAGAS_POR_HORA = 1 # Alterar para 2 se quiseres permitir dois carros à mesma hora
HORARIOS = ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"]

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agendamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT,
            data TEXT,
            hora TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

@app.get("/", response_class=HTMLResponse)
def index():
    return """
    <!DOCTYPE html>
    <html lang="pt">
    <head>
        <meta charset="UTF-8">
        <title>Centro Auto Sofisticar - Agendamento</title>
        <!-- Carregar Calendário Flatpickr -->
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/flatpickr/dist/flatpickr.min.css">
        <script src="https://cdn.jsdelivr.net/npm/flatpickr"></script>
        <style>
            body { font-family: sans-serif; background: #121212; color: #fff; padding: 20px; }
            .container { max-width: 400px; margin: auto; background: #1e1e1e; padding: 20px; border-radius: 10px; }
            .hora-btn { display: block; width: 100%; padding: 10px; margin: 5px 0; border: none; border-radius: 5px; background: #333; color: #fff; cursor: pointer; }
            .hora-btn:hover { background: #d4af37; color: #000; }
            .disponivel { background: #28a745; }
            .ocupado { background: #555; cursor: not-allowed; opacity: 0.5; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Agendar Serviço</h2>
            <input type="text" id="data_picker" placeholder="Escolha a data..." style="width:100%; padding:10px;">
            <div id="lista_horas" style="margin-top:20px;"></div>
        </div>

        <script>
            flatpickr("#data_picker", {
                dateFormat: "Y-m-d",
                minDate: "today",
                onChange: function(selectedDates, dateStr) {
                    fetchVagas(dateStr);
                }
            });

            async function fetchVagas(data) {
                const res = await fetch('/api/vagas?data=' + data);
                const data_res = await res.json();
                const div = document.getElementById('lista_horas');
                div.innerHTML = "<h4>Horários disponíveis:</h4>";
                
                data_res.forEach(item => {
                    const btn = document.createElement('button');
                    btn.className = 'hora-btn ' + (item.livre ? 'disponivel' : 'ocupado');
                    btn.innerText = item.hora + (item.livre ? ' (Disponível)' : ' (Cheio)');
                    btn.disabled = !item.livre;
                    div.appendChild(btn);
                });
            }
        </script>
    </body>
    </html>
    """

@app.get("/api/vagas")
def get_vagas(data: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # Conta quantos agendamentos existem para cada hora naquele dia
    cursor.execute("SELECT hora, COUNT(*) FROM agendamentos WHERE data = ? GROUP BY hora", (data,))
    ocupacao = dict(cursor.fetchall())
    conn.close()

    resultado = []
    for h in HORARIOS:
        ja_ocupado = ocupacao.get(h, 0)
        resultado.append({
            "hora": h,
            "livre": ja_ocupado < MAX_VAGAS_POR_HORA
        })
    return resultado

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
