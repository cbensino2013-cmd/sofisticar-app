from fastapi import FastAPI, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse, Response
import sqlite3
import os
import csv
import io
from datetime import datetime
from twilio.rest import Client

app = FastAPI(title="Centro Auto Sofisticar")

# 🔒 Palavra-passe do Painel de Gestão (pode ser definida no Render via GESTOR_PIN)
PIN_ACESSO = os.getenv("GESTOR_PIN", "1234")

# 💾 Base de Dados
DB_FILE = "oficina.db"

# 📱 CONFIGURAÇÃO DO TWILIO (SMS)
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "")
GESTOR_PHONE_NUMBER = os.getenv("GESTOR_PHONE_NUMBER", "") # Telemóvel do Gestor para alertas

# Horários disponíveis para marcação
HORARIOS_DISPONIVEIS = ["08:00", "09:00", "10:00", "11:00", "13:00", "14:00", "15:00", "16:00", "17:00"]
MAX_AGENDAMENTOS_POR_SLOT = 2  # Máximo de carros por hora

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

def enviar_sms(numero_destino: str, mensagem: str):
    """Função genérica de envio de SMS via Twilio"""
    if not (TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_PHONE_NUMBER and numero_destino):
        return

    try:
        numero_limpo = "".join(filter(str.isdigit, numero_destino))
        if not numero_limpo.startswith("351") and len(numero_limpo) == 9:
            numero_formatado = f"+351{numero_limpo}"
        else:
            numero_formatado = f"+{numero_limpo}"

        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=mensagem,
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

# API para verificar horas vagas numa data escolhida pelo cliente
@app.get("/api/vagas")
def obter_vagas(data: str):
    limpar_dados_antigos()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT hora, COUNT(*) FROM agendamentos WHERE data = ? GROUP BY hora", (data,))
    ocupacao = dict(cursor.fetchall())
    conn.close()

    vagas = []
    for h in HORARIOS_DISPONIVEIS:
        count = ocupacao.get(h, 0)
        if count < MAX_AGENDAMENTOS_POR_SLOT:
            vagas.append({"hora": h, "disponivel": True, "vagas_restantes": MAX_AGENDAMENTOS_POR_SLOT - count})
        else:
            vagas.append({"hora": h, "disponivel": False, "vagas_restantes": 0})
            
    return {"data": data, "horarios": vagas}

# 🌐 PÁGINA INICIAL DO CLIENTE
@app.get("/", response_class=HTMLResponse)
@app.get("/cliente", response_class=HTMLResponse)
def pagina_cliente(sucesso: bool = False, id_agendamento: int = 0):
    limpar_dados_antigos()
    opcoes_servicos = "".join([f'<option value="{s}">{s}</option>' for s in SERVICOS.keys()])
    
    msg_sucesso = ""
    if sucesso:
        msg_sucesso = f"""
        <div style="background: #1e3a29; border: 1px solid #28a745; color: #2ea44f; padding: 15px; border-radius: 8px; text-align: center; margin-bottom: 20px;">
            <p style="margin: 0 0 10px 0; font-weight: bold; font-size: 16px;">✅ Agendamento submetido com sucesso!</p>
            <a href="/comprovativo?id={id_agendamento}" target="_blank" style="display: inline-block; background: #28a745; color: #fff; padding: 8px 15px; border-radius: 4px; text-decoration: none; font-weight: bold; font-size: 13px;">📄 Descarregar / Imprimir Comprovativo</a>
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
            .rgpd-notice {{ font-size: 12px; color: #888; text-align: center; margin-top: 15px; line-height: 1.4; }}
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

            async function carregarHorarios() {{
                const dataInput = document.getElementById("data_input").value;
                const horaSelect = document.getElementById("hora_select");
                if (!dataInput) return;

                horaSelect.innerHTML = "<option>A carregar vagas...</option>";
                const response = await fetch('/api/vagas?data=' + dataInput);
                const res = await response.json();
                
                horaSelect.innerHTML = '<option value="">-- Selecione o Horário --</option>';
                res.horarios.forEach(h => {{
                    if (h.disponivel) {{
                        horaSelect.innerHTML += `<option value="${{h.hora}}">${{h.hora}} (${{h.vagas_restantes}} vaga(s))</option>`;
                    }} else {{
                        horaSelect.innerHTML += `<option value="" disabled style="color: #ff6b6b;">${{h.hora}} (Esgotado)</option>`;
                    }}
                }});
            }}
        </script>
    </head>
    <body>
        <div class="container">
            <h1>CENTRO AUTO SOFISTICAR</h1>
            <div class="sub">Serviço Automóvel Personalizado</div>
            
            <a href="/estado" class="nav-btn">🔍 Acompanhar Estado da Viatura</a>
            
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
                    {opcoes_servicos}
                </select>

                <div id="info-box" class="info-box"></div>

                <div style="display: flex; gap: 10px;">
                    <div style="flex: 1;">
                        <label>Data Pretendida:</label>
                        <input type="date" id="data_input" name="data" onchange="carregarHorarios()" required>
                    </div>
                    <div style="flex: 1;">
                        <label>Hora Pretendida:</label>
                        <select id="hora_select" name="hora" required>
                            <option value="">-- Escolha a Data Primeiro --</option>
                        </select>
                    </div>
                </div>

                <label>Observações / Detalhes:</label>
                <textarea name="observacoes" rows="3" placeholder="Ex: Ruído na travagem, estofos em pele..."></textarea>

                <button type="submit">SUBMETER AGENDAMENTO</button>

                <div class="rgpd-notice">
                    🔒 <b>Proteção de Dados:</b> Em conformidade com o RGPD, os seus dados são recolhidos apenas para a gestão do agendamento e serão automaticamente eliminados do nosso sistema após 30 dias.
                </div>
            </form>
        </div>
    </body>
    </html>
    """
    return html

# 📄 GERAR COMPROVATIVO EM PDF/IMPRESSÃO
@app.get("/comprovativo", response_class=HTMLResponse)
def emitir_comprovativo(id: int):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, cliente, contacto, matricula, servico, data, hora, estado, criado_em FROM agendamentos WHERE id = ?", (id,))
    reg = cursor.fetchone()
    conn.close()

    if not reg:
        return "<h3>Comprovativo não encontrado ou já expirado.</h3>"

    id_i, cli, cnt, mat, srv, dt, hr, est, criado = reg

    return f"""
    <!DOCTYPE html>
    <html lang="pt">
    <head>
        <meta charset="UTF-8">
        <title>Comprovativo #{id_i} - Centro Auto Sofisticar</title>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 40px; background: #fff; color: #000; max-width: 600px; margin: 0 auto; border: 2px solid #d4af37; border-radius: 8px; }}
            h1 {{ color: #121212; border-bottom: 2px solid #d4af37; padding-bottom: 10px; margin-bottom: 5px; }}
            .sub {{ color: #888; font-size: 14px; text-transform: uppercase; margin-bottom: 30px; }}
            .field {{ margin-bottom: 15px; font-size: 16px; }}
            .field label {{ font-weight: bold; color: #555; display: inline-block; width: 140px; }}
            .footer {{ margin-top: 40px; font-size: 12px; color: #777; border-top: 1px dashed #ccc; padding-top: 15px; text-align: center; }}
            .btn-print {{ background: #d4af37; border: none; padding: 10px 20px; font-weight: bold; cursor: pointer; border-radius: 5px; margin-bottom: 20px; }}
            @media print {{ .btn-print {{ display: none; }} body {{ border: none; padding: 0; }} }}
        </style>
    </head>
    <body>
        <button onclick="window.print()" class="btn-print">🖨️ Imprimir ou Guardar em PDF</button>
        <h1>CENTRO AUTO SOFISTICAR</h1>
        <div class="sub">Comprovativo de Agendamento de Serviço</div>

        <div class="field"><label>Nº Agendamento:</label> #{id_i}</div>
        <div class="field"><label>Cliente:</label> {cli}</div>
        <div class="field"><label>Contacto:</label> {cnt}</div>
        <div class="field"><label>Matrícula:</label> <b>{mat}</b></div>
        <div class="field"><label>Serviço:</label> {srv}</div>
        <div class="field"><label>Data Agendada:</label> {dt} às {hr}</div>
        <div class="field"><label>Estado Atual:</label> {est}</div>
        <div class="field"><label>Emitido em:</label> {criado}</div>

        <div class="footer">
            🔒 Centro Auto Sofisticar • Proteção de Dados: Este registo expira automaticamente em 30 dias.
        </div>
    </body>
    </html>
    """

# 🔍 PÁGINA DE ACOMPANHAMENTO DO CLIENTE
@app.get("/estado", response_class=HTMLResponse)
def acompanhar_estado(matricula: str = ""):
    limpar_dados_antigos()
    resultado_html = ""
    if matricula:
        mat_limpa = matricula.strip().upper()
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT id, cliente, servico, data, hora, estado FROM agendamentos WHERE UPPER(matricula) = ? ORDER BY id DESC LIMIT 1", (mat_limpa,))
        registo = cursor.fetchone()
        conn.close()

        if registo:
            id_i, cliente, servico, data, hora, estado = registo
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
                <div style="margin-top: 15px;">
                    <a href="/comprovativo?id={id_i}" target="_blank" style="color: #d4af37; text-decoration: underline; font-size: 14px;">📄 Ver / Imprimir Comprovativo</a>
                </div>
            </div>
            """
        else:
            resultado_html = '<p style="color: #ff6b6b; text-align: center; margin-top: 20px;">❌ Nenhuma viatura encontrada com essa matrícula (ou o registo expirou após 30 dias).</p>'

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

# 📩 SUBMETER NOVO AGENDAMENTO
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
    
    # Inserir agendamento
    cursor.execute("""
        INSERT INTO agendamentos (cliente, contacto, matricula, servico, data, hora, observacoes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (cliente, contacto, matricula.upper(), servico, data, hora, observacoes))
    novo_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # 🔔 NOTIFICAÇÃO POR SMS PARA O GESTOR
    if GESTOR_PHONE_NUMBER:
        msg_gestor = f"🚨 Novo Agendamento #{novo_id}!\nCliente: {cliente}\nMatrícula: {matricula.upper()}\nServiço: {servico}\nData: {data} às {hora}"
        enviar_sms(GESTOR_PHONE_NUMBER, msg_gestor)

    return RedirectResponse(url=f"/cliente?sucesso=True&id_agendamento={novo_id}", status_code=303)

# 🔄 ALTERAR ESTADO E NOTIFICAR CLIENTE
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
            mensagens = {
                "Confirmado": f"Ola {nome_cliente}! O seu agendamento no Centro Auto Sofisticar foi CONFIRMADO. Aguardamos por si!",
                "Em Oficina": f"Ola {nome_cliente}! A sua viatura ja se encontra em trabalhos na nossa oficina.",
                "Pronto a Levantar": f"Ola {nome_cliente}! A sua viatura esta PRONTA a levantar no Centro Auto Sofisticar. Ate ja!"
            }
            if novo_estado in mensagens:
                enviar_sms(contacto, mensagens[novo_estado])

    return RedirectResponse(url=f"/painel?pin={pin}", status_code=303)

# 📲 ENVIAR LEMBRETE MANUAL POR SMS
@app.post("/enviar_lembrete")
def enviar_lembrete(id_agendamento: int = Form(...), pin: str = Form(...)):
    if pin == PIN_ACESSO:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT cliente, contacto, data, hora FROM agendamentos WHERE id = ?", (id_agendamento,))
        reg = cursor.fetchone()
        conn.close()

        if reg:
            cli, cnt, dt, hr = reg
            msg = f"Lembrete Centro Auto Sofisticar: Ola {cli}, lembramos do seu agendamento agendado para {dt} as {hr}. Contamos consigo!"
            enviar_sms(cnt, msg)

    return RedirectResponse(url=f"/painel?pin={pin}", status_code=303)

# 📥 EXPORTAR DADOS EM EXCEL / CSV
@app.get("/exportar_csv")
def exportar_csv(pin: str = ""):
    if pin != PIN_ACESSO:
        return Response(content="Acesso negado", status_code=403)

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, cliente, contacto, matricula, servico, data, hora, estado, observacoes, criado_em FROM agendamentos ORDER BY id DESC")
    registos = cursor.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Cliente", "Contacto", "Matricula", "Servico", "Data", "Hora", "Estado", "Observacoes", "Criado Em"])
    
    for row in registos:
        writer.writerow(row)

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=agendamentos_centro_auto.csv"}
    )

# 📊 PAINEL DE GESTÃO DA OFICINA
@app.get("/painel", response_class=HTMLResponse)
def pagina_painel(pin: str = "", busca: str = "", vista: str = "tabela"):
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

    if busca:
        q = f"%{busca}%"
        cursor.execute("SELECT id, cliente, contacto, matricula, servico, data, hora, observacoes, estado FROM agendamentos WHERE cliente LIKE ? OR matricula LIKE ? OR servico LIKE ? ORDER BY id DESC", (q, q, q))
    else:
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
                <form action="/alterar_estado" method="post" style="margin:0; display:inline-block;">
                    <input type="hidden" name="id_agendamento" value="{id_i}">
                    <input type="hidden" name="pin" value="{pin}">
                    <select name="novo_estado" onchange="this.form.submit()" style="padding:6px; background:#2a2a2a; color:#fff; border:1px solid #555; border-radius:4px;">
                        {opcoes_estado}
                    </select>
                </form>
                <form action="/enviar_lembrete" method="post" style="margin:0; display:inline-block; margin-left: 5px;">
                    <input type="hidden" name="id_agendamento" value="{id_i}">
                    <input type="hidden" name="pin" value="{pin}">
                    <button title="Enviar Lembrete por SMS" style="background: #2a2a2a; border: 1px solid #555; color: #d4af37; padding: 5px 8px; border-radius: 4px; cursor: pointer;">🔔 SMS</button>
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
            .header-bar {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 10px; }}
            table {{ width:100%; border-collapse:collapse; background:#1e1e1e; border-radius:8px; overflow:hidden; }}
            th {{ background:#252525; padding:12px; text-align:left; color:#d4af37; }}
            .btn {{ background: #2a2a2a; color: #d4af37; border: 1px solid #444; padding: 8px 15px; border-radius: 5px; text-decoration: none; font-weight: bold; font-size: 14px; display: inline-block; }}
            .btn:hover {{ background: #d4af37; color: #121212; }}
            input[type="text"] {{ padding: 8px 12px; background: #2a2a2a; border: 1px solid #444; color: #fff; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <div class="header-bar">
            <h2>🛠️ Gestão de Agendamentos ({len(registos)})</h2>
            <div>
                <a href="/exportar_csv?pin={pin}" class="btn">📥 Exportar Excel/CSV</a>
            </div>
        </div>

        <form action="/painel" method="get" style="margin-bottom: 20px; display: flex; gap: 10px;">
            <input type="hidden" name="pin" value="{pin}">
            <input type="text" name="busca" placeholder="Pesquisar cliente, matrícula..." value="{busca}" style="flex: 1;">
            <button type="submit" class="btn">🔍 Pesquisar</button>
        </form>

        <p style="color:#888; font-size:13px;">🔒 Política de Privacidade RGPD: Os dados são eliminados automaticamente 30 dias após a criação.</p>

        <table>
            <thead>
                <tr>
                    <th>ID</th><th>Cliente</th><th>Matrícula</th><th>Serviço</th><th>Data/Hora</th><th>Notas</th><th>Ações / SMS</th>
                </tr>
            </thead>
            <tbody>
                {linhas if linhas else '<tr><td colspan="7" style="padding:20px; text-align:center;">Nenhum registo encontrado.</td></tr>'}
            </tbody>
        </table>
    </body>
    </html>
    """

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
