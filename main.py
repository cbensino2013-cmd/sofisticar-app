from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
import sqlite3
import os

app = FastAPI(title="Centro Auto Sofisticar")

PIN_ACESSO = "1234"
DB_FILE = "oficina.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agendamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT NOT NULL,
            contacto TEXT NOT NULL,
            matricula TEXT NOT NULL,
            servico TEXT NOT NULL,
            data TEXT NOT NULL,
            hora TEXT NOT NULL,
            estado TEXT DEFAULT 'Pendente',
            observacoes TEXT,
            preco TEXT DEFAULT 'Sob Consulta'
        )
    """)
    conn.commit()
    conn.close()

init_db()

# 🔄 ROTA QUE ATUALIZA O ESTADO NA BASE DE DADOS
@app.post("/alterar_estado")
def alterar_estado(id_agendamento: int = Form(...), novo_estado: str = Form(...), pin: str = Form(...)):
    if pin == PIN_ACESSO:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("UPDATE agendamentos SET estado = ? WHERE id = ?", (novo_estado, id_agendamento))
        conn.commit()
        conn.close()
    return RedirectResponse(url=f"/painel?pin={pin}", status_code=303)

# 📊 PAINEL DE GESTÃO COM O MENU DINÂMICO
@app.get("/painel", response_class=HTMLResponse)
def pagina_painel(pin: str = ""):
    if pin != PIN_ACESSO:
        return """
        <form action="/painel" method="get" style="text-align:center; margin-top:50px;">
            <h3>🛠️ Área do Gestor</h3>
            <input type="password" name="pin" placeholder="PIN" required>
            <button type="submit">Entrar</button>
        </form>
        """

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, cliente, contacto, matricula, servico, data, hora, observacoes, estado FROM agendamentos ORDER BY id DESC")
    registos = cursor.fetchall()
    conn.close()

    linhas_tabela = ""
    for item in registos:
        id_item, cliente, contacto, matricula, servico, data, hora, observacoes, estado = item
        
        # Define a cor do badge
        cor_badge = "#ffc107" if estado == "Pendente" else ("#17a2b8" if estado == "Confirmado" else "#28a745")

        linhas_tabela += f"""
        <tr>
            <td>#{id_item}</td>
            <td><b>{cliente}</b><br><small>{contacto}</small></td>
            <td><span style="background: #333; color: white; padding: 3px 8px; border-radius: 4px;">{matricula}</span></td>
            <td><b>{servico}</b></td>
            <td>{data} às {hora}</td>
            <td><i>{observacoes or '-'}</i></td>
            <td>
                <!-- MENU CLICÁVEL PARA MUDAR O ESTADO -->
                <form action="/alterar_estado" method="post" style="margin: 0;">
                    <input type="hidden" name="id_agendamento" value="{id_item}">
                    <input type="hidden" name="pin" value="{pin}">
                    <select name="novo_estado" onchange="this.form.submit()" style="background-color: {cor_badge}; font-weight: bold; padding: 5px; border-radius: 5px; cursor: pointer;">
                        <option value="Pendente" {'selected' if estado == 'Pendente' else ''}>🟡 Pendente</option>
                        <option value="Confirmado" {'selected' if estado == 'Confirmado' else ''}>🔵 Confirmado</option>
                        <option value="Concluído" {'selected' if estado == 'Concluído' else ''}>🟢 Concluído</option>
                    </select>
                </form>
            </td>
        </tr>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Painel Gestão</title>
        <style>
            body {{ font-family: sans-serif; padding: 20px; background: #f4f4f4; }}
            table {{ width: 100%; border-collapse: collapse; background: white; }}
            th, td {{ padding: 12px; border: 1px solid #ddd; text-align: left; }}
            th {{ background: #1a1a1a; color: white; }}
        </style>
    </head>
    <body>
        <h2>🛠️ Painel de Gestão - Centro Auto Sofisticar</h2>
        <table>
            <thead>
                <tr>
                    <th>ID</th><th>Cliente</th><th>Matrícula</th><th>Serviço</th><th>Data & Hora</th><th>Obs</th><th>Estado</th>
                </tr>
            </thead>
            <tbody>
                {linhas_tabela}
            </tbody>
        </table>
    </body>
    </html>
    """
