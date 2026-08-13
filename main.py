from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
import sqlite3
import os
from twilio.rest import Client

app = FastAPI(title="Centro Auto Sofisticar")

# 🔒 Palavra-passe do Painel de Gestão
PIN_ACESSO = "1234"

# 💾 Base de Dados
DB_FILE = "oficina.db"

# 📱 CONFIGURAÇÃO DO TWILIO (SMS)
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "")

def limpar_dados_antigos():
    """Apaga automaticamente os agendamentos criados há mais de 30 dias (Conformidade RGPD)"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM agendamentos WHERE criado_em < datetime('now', '-30 days')")
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"❌ Erro ao limpar dados antigos: {e}")

def enviar_sms_status(numero_destino: str, nome_cliente: str, novo_estado: str):
    """Envia SMS de atualização de estado ao cliente"""
    if not (TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_PHONE_NUMBER):
        return

    try:
        numero_limpo = "".join(filter(str.isdigit, numero_destino))
        if not numero_limpo.startswith("351") and len(numero_limpo) == 9:
            numero_formatado = f"+351{numero_limpo}"
        else:
            numero_formatado = f"+{numero_limpo}"

        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        mensagens = {
            "Confirmado": f"Ola {nome_cliente}! O seu agendamento no Centro Auto Sofisticar foi CONFIRMADO. Aguardamos por si!",
            "Em Oficina": f"Ola {nome_cliente}! A sua viatura ja se encontra em trabalhos na nossa oficina.",
            "Pronto a Levantar": f"Ola {nome_cliente}! A sua viatura esta PRONTA a levantar no Centro Auto Sofisticar. Ate ja!"
        }

        if novo_estado in mensagens:
            client.messages.create(
                body=mensagens[novo_estado],
                from_=TWILIO_PHONE_NUMBER,
                to=numero_formatado
            )
    except Exception as e:
        print(f"❌ Erro ao enviar SMS: {e}")

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
            criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_db()

SERVICOS = {
    "Mecânica Geral": {"preco": "Sob Avaliação", "tempo": "1 a 2 dias"},
    "Elétrica Auto & Diagnóstico": {"preco": "Desde 35€", "tempo": "1 a 3 horas"},
    "Ar Condicionado (Carregamento)": {"preco": "Desde 50€", "tempo": "45 minutos"},
    "Polimento e Detalhe": {"preco": "Desde 80€", "tempo": "1 dia"},
    "Lavagem Completa (Interior + Exterior)": {"preco": "Desde 25€", "tempo": "1 hora"},
    "Higienização de Estofos": {"preco": "Desde 45€", "tempo": "3 horas"}
}

# 🌐 PÁGINA INICIAL DO CLIENTE
@app.get("/", response_class=HTMLResponse)
@app.get("/cliente", response_class=HTMLResponse)
def pagina_cliente(sucesso: bool = False):
    limpar_dados_antigos()
    opcoes = "".join([f'<option value="{s}">{s}</option>' for s in SERVICOS.keys()])
    
    msg_sucesso = ""
    if sucesso:
        msg_sucesso = """
        <div style="background: #1e3a29; border: 1px solid #28a745; color: #2ea44f; padding: 15px; border-radius: 8px; text-align: center; margin-bottom: 20px; font-weight: bold;">
            ✅ Agendamento submetido com sucesso! Entraremos em contacto brevemente.
        </div>
        """

    html = f"""
    <!DOCTYPE html>
    <html lang="pt">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Centro Auto Sofisticar</title>
        <style>
            body {{ font-family: 'Segoe UI', Roboto, sans-serif; background-color: #121212; color: #e0e0e0; margin: 0; padding: 20px; }}
            .container {{ max-width: 650px; margin: 0 auto; background: #1e1e1e; padding: 30px; border-radius: 12px; border-top: 5px solid #d4af37; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }}
            h1 {{ text-align: center; color: #fff; margin-bottom: 5px; font-size: 26px; letter-spacing: 1px; }}
            .sub {{ text-align: center; color: #d4af37; font-weight: bold; margin-bottom: 25px; text-transform: uppercase; font-size: 13px; }}
            .nav-btn {{ display: block; text-align: center; background: #2a2a2a; color: #d4af37; text-decoration: none; padding: 10px; border-radius: 6px; margin-bottom: 25px; border: 1px solid #333; font-weight: bold; transition: 0.3s; }}
            .nav-btn:hover {{ background: #d4af37; color: #121212; }}
            label {{ font-size: 14px; font-weight: bold; display: block; margin-top: 15px; margin-bottom: 5px; color: #bbb; }}
            input, select, textarea {{ width: 100%; padding: 12px; background: #2a2a2a; border: 1px solid #444; border-radius: 6px; color: #fff; box-sizing: border-box; font-size: 15px; }}
            input:focus, select:focus {{ border-color: #d4af37; outline: none; }}
            .info-box {{ background: #262626; padding: 12px; border-left: 4px solid #d4af37; margin-top: 10px; border-radius: 4px; font-size: 14px; display: none; }}
            button {{ width: 100%; background: #d4af37; color: #121212; border: none; padding: 15px; border-radius: 6px; font-size: 16px; font-weight: bold; margin-top: 25px; cursor: pointer; transition: 0.3s; }}
            button:hover {{ background: #f3c63f; }}
        </style>
        <script>
            const infoServicos = {SERVICOS};
            function atualizarInfo() {{
                const select = document.getElementById("servico");
                const val = select.value;
                const box = document.getElementById("info-box");
                if (val && infoServicos[val]) {{
                    box.style.display = "block";
                    box.innerHTML = "<b>Estimativa:</b> " + infoServicos[val].preco + " | <b>Tempo médio:</b> " + infoServicos[val].tempo;
                }} else {{
                    box.style.display = "none";
                }}
            }}
        </script>
    </head>
    <body>
        <div class="container">
            <h1>CENTRO AUTO SOFISTICAR</h1>
            <div class="sub">Serviço Automóvel Personalizado</div>
            
            <a href="/estado" class="nav-btn">🔍 Já agendou? Acompanhe o estado da sua viatura aqui</a>
            
            {msg_sucesso}

            <form action="/agendar" method="post">
                <label>Nome Completo:</label>
                <input type="text" name="cliente" required placeholder="Ex: João Silva">

                <label>Telemóvel:</label>
                <input type="tel" name="contacto" required placeholder="Ex: 912345678">

                <label>Matrícula:</label>
                <input type="text" name="matricula" required placeholder="Ex: AA-00-AA" style="text-transform: uppercase;">

                <label>Serviço Pretendido:</label>
                <select id="servico" name="servico" onchange="atualizarInfo()" required>
                    <option value="">-- Selecione o Serviço --</option>
                    {opcoes}
                </select>

                <div id="info-box" class="info-box"></div>

                <div style="display: flex; gap: 10px;">
                    <div style="flex: 1;">
                        <label>Data Pretendida:</label>
                        <input type="date" name="data" required>
                    </div>
                    <div style="flex: 1;">
                        <label>Hora Pretendida:</label>
                        <input type="time" name="hora" required>
                    </div>
                </div>

                <label>Observações / Detalhes:</label>
                <textarea name="observacoes" rows="3" placeholder="Ex: Ruído na travagem, estofos em pele..."></textarea>

                <button type="submit">SUBMETER AGENDAMENTO</button>
            </form>
        </div>
    </body>
    </html>
    """
    return html

# 🔍 PÁGINA DE ACOMPANHAMENTO DO CLIENTE
@app.get("/estado", response_class=HTMLResponse)
def acompanhar_estado(matricula: str = ""):
    limpar_dados_antigos()
    resultado_html = ""
    if matricula:
        mat_limpa = matricula.strip().upper()
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT cliente, servico, data, hora, estado FROM agendamentos WHERE UPPER(matricula) = ? ORDER BY id DESC LIMIT 1", (mat_limpa,))
        registo = cursor.fetchone()
        conn.close()

        if registo:
            cliente, servico, data, hora, estado = registo
            cores = {
                "Pendente": "#ffc107",
                "Confirmado": "#17a2b8",
                "Em Oficina": "#fd7e14",
                "Pronto a Levantar": "#28a745",
                "Concluído": "#6c757d"
            }
            cor = cores.get(estado, "#ffffff")
            resultado_html = f"""
            <div style="background: #262626; padding: 20px; border-radius: 8px; margin-top: 20px; text-align: center; border: 1px solid #444;">
                <h3 style="margin-top:0; color: #d4af37;">Viatura: {mat_limpa}</h3>
                <p><b>Cliente:</b> {cliente}</p>
                <p><b>Serviço:</b> {servico}</p>
                <p><b>Agendado para:</b> {data} às {hora}</p>
                <div style="margin-top: 15px; padding: 12px; background: {cor}; color: #000; font-weight: bold; border-radius: 6px; font-size: 18px;">
                    Estado Atual: {estado.upper()}
                </div>
            </div>
            """
        else:
            resultado_html = '<p style="color: #ff6b6b; text-align: center; margin-top: 20px;">❌ Nenhuma viatura encontrada com essa matrícula (ou o registo já expirou).</p>'

    return f"""
    <!DOCTYPE html>
    <html lang="pt">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Estado do Veículo - Centro Auto Sofisticar</title>
        <style>
            body {{ font-family: sans-serif; background: #121212; color: #fff; padding: 20px; display: flex; justify-content: center; }}
            .card {{ background: #1e1e1e; padding: 30px; border-radius: 12px; width: 100%; max-width: 500px; border-top: 5px solid #d4af37; box-shadow: 0 4px 20px rgba(0,0,0,0.5); }}
            input {{ width: 100%; padding: 12px; background: #2a2a2a; border: 1px solid #444; color: #fff; border-radius: 6px; box-sizing: border-box; text-align: center; font-size: 18px; text-transform: uppercase; margin-bottom: 15px; }}
            button {{ width: 100%; background: #d4af37; color: #121212; border: none; padding: 12px; border-radius: 6px; font-weight: bold; font-size: 16px; cursor: pointer; }}
            a {{ color: #888; text-decoration: none; display: block; text-align: center; margin-top: 20px; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h2 style="text-align: center; color: #d4af37; margin-top:0;">🔍 Consultar Estado</h2>
            <form action="/estado" method="get">
                <input type="text" name="matricula" placeholder="Digite a Matrícula" value="{matricula}" required autofocus>
                <button type="submit">PROCURAR</button>
            </form>
            {resultado_html}
            <a href="/cliente">← Voltar ao Formulário de Agendamento</a>
        </div>
    </body>
    </html>
    """

# 📩 SUBMETER
@app.post("/agendar")
def processar_agendamento(
    cliente: str = Form(...),
    contacto: str = Form(...),
    matricula: str = Form(...),
    servico: str = Form(...),
    data: str = Form(...),
    hora: str = Form(...),
    observacoes: str = Form("")
):
    limpar_dados_antigos()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO agendamentos (cliente, contacto, matricula, servico, data, hora, observacoes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (cliente, contacto, matricula.upper(), servico, data, hora, observacoes))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/cliente?sucesso=True", status_code=303)

# 🔄 ALTERAR ESTADO E ENVIAR SMS
@app.post("/alterar_estado")
def alterar_estado(id_agendamento: int = Form(...), novo_estado: str = Form(...), pin: str = Form(...)):
    limpar_dados_antigos()
    if pin == PIN_ACESSO:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute("SELECT cliente, contacto FROM agendamentos WHERE id = ?", (id_agendamento,))
        agendamento = cursor.fetchone()
        
        cursor.execute("UPDATE agendamentos SET estado = ? WHERE id = ?", (novo_estado, id_agendamento))
        conn.commit()
        conn.close()

        if agendamento:
            nome_cliente, contacto = agendamento
            enviar_sms_status(contacto, nome_cliente, novo_estado)

    return RedirectResponse(url=f"/painel?pin={pin}", status_code=303)

# 📊 PAINEL DE GESTÃO DA OFICINA
@app.get("/painel", response_class=HTMLResponse)
def pagina_painel(pin: str = ""):
    limpar_dados_antigos()
    if pin != PIN_ACESSO:
        return f"""
        <!DOCTYPE html>
        <html>
        <head><title>Acesso Restrito</title></head>
        <body style="background:#121212; color:#fff; font-family:sans-serif; display:flex; justify-content:center; align-items:center; height:100vh;">
            <form action="/painel" method="get" style="background:#1e1e1e; padding:30px; border-radius:10px; border-top:4px solid #d4af37; text-align:center;">
                <h3>🛠️ Painel do Gestor</h3>
                <input type="password" name="pin" placeholder="PIN" style="padding:10px; text-align:center; border-radius:5px; border:1px solid #444; background:#2a2a2a; color:#fff; font-size:18px;" required autofocus><br><br>
                <button style="padding:10px 20px; background:#d4af37; border:none; border-radius:5px; font-weight:bold; cursor:pointer;">ENTRAR</button>
            </form>
        </body>
        </html>
        """

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, cliente, contacto, matricula, servico, data, hora, observacoes, estado FROM agendamentos ORDER BY id DESC")
    registos = cursor.fetchall()
    conn.close()

    linhas = ""
    for r in registos:
        id_i, cli, cnt, mat, srv, dt, hr, obs, est = r
        
        opcoes_estado = ""
        estados = ["Pendente", "Confirmado", "Em Oficina", "Pronto a Levantar", "Concluído"]
        for e in estados:
            sel = "selected" if est == e else ""
            opcoes_estado += f'<option value="{e}" {sel}>{e}</option>'

        linhas += f"""
        <tr style="border-bottom: 1px solid #333;">
            <td style="padding:12px;">#{id_i}</td>
            <td style="padding:12px;"><b>{cli}</b><br><small style="color:#aaa">{cnt}</small></td>
            <td style="padding:12px;"><span style="background:#333; padding:4px 8px; border-radius:4px; font-weight:bold; color:#d4af37;">{mat}</span></td>
            <td style="padding:12px;">{srv}</td>
            <td style="padding:12px;">{dt} às {hr}</td>
            <td style="padding:12px; color:#aaa;"><i>{obs or '-'}</i></td>
            <td style="padding:12px;">
                <form action="/alterar_estado" method="post" style="margin:0;">
                    <input type="hidden" name="id_agendamento" value="{id_i}">
                    <input type="hidden" name="pin" value="{pin}">
                    <select name="novo_estado" onchange="this.form.submit()" style="padding:6px; background:#2a2a2a; color:#fff; border:1px solid #555; border-radius:4px;">
                        {opcoes_estado}
                    </select>
                </form>
            </td>
        </tr>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Painel Gestor - Centro Auto Sofisticar</title>
        <style>
            body {{ font-family: sans-serif; background:#121212; color:#fff; padding:20px; }}
            table {{ width:100%; border-collapse:collapse; background:#1e1e1e; border-radius:8px; overflow:hidden; }}
            th {{ background:#252525; padding:12px; text-align:left; color:#d4af37; }}
        </style>
    </head>
    <body>
        <h2>🛠️ Gestão de Agendamentos ({len(registos)})</h2>
        <p style="color:#888; font-size:13px;">🔒 Política de Privacidade RGPD: Os dados são eliminados automaticamente 30 dias após a criação.</p>
        <table>
            <thead>
                <tr>
                    <th>ID</th><th>Cliente</th><th>Matrícula</th><th>Serviço</th><th>Data/Hora</th><th>Notas</th><th>Estado (Notifica SMS)</th>
                </tr>
            </thead>
            <tbody>
                {linhas if linhas else '<tr><td colspan="7" style="padding:20px; text-align:center;">Sem registos.</td></tr>'}
            </tbody>
        </table>
    </body>
    </html>
    """

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
