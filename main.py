from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, Response
import sqlite3
import os
import csv
import io
import urllib.parse
from datetime import datetime
from twilio.rest import Client

app = FastAPI(title="Centro Auto Sofisticar")

# 🔒 Palavra-passe do Painel de Gestão
PIN_ACESSO = os.getenv("GESTOR_PIN", "1234")

# 💾 Base de Dados
DB_FILE = "oficina.db"

# 📱 CONFIGURAÇÃO DO TWILIO (SMS)
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "")
GESTOR_PHONE_NUMBER = os.getenv("GESTOR_PHONE_NUMBER", "")

# Configuração de Vagas
MAX_VAGAS_POR_HORA = 1  # Altera para 2 se quiseres permitir dois carros à mesma hora
HORARIOS_DISPONIVEIS = ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"]

def limpar_dados_antigos():
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM agendamentos WHERE criado_em < datetime('now', '-30 days')")
        cursor.execute("DELETE FROM orcamentos WHERE criado_em < datetime('now', '-30 days')")
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"❌ Erro ao limpar dados antigos: {e}")

def enviar_sms(numero_destino: str, mensagem: str):
    if not (TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_PHONE_NUMBER and numero_destino):
        return
    try:
        numero_limpo = "".join(filter(str.isdigit, numero_destino))
        if not numero_limpo.startswith("351") and len(numero_limpo) == 9:
            numero_formatado = f"+351{numero_limpo}"
        else:
            numero_formatado = f"+{numero_limpo}"

        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        client.messages.create(body=mensagem, from_=TWILIO_PHONE_NUMBER, to=numero_formatado)
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
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orcamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT NOT NULL,
            contacto TEXT NOT NULL,
            matricula TEXT NOT NULL,
            detalhes TEXT NOT NULL,
            valor_estimado REAL NOT NULL,
            validade TEXT DEFAULT '15 dias',
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
        vagas.append({
            "hora": h,
            "disponivel": count < MAX_VAGAS_POR_HORA,
            "vagas_restantes": MAX_VAGAS_POR_HORA - count
        })
    return vagas

# 🌐 PÁGINA INICIAL CLIENTE COM CALENDAR FLATPICKR
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

    return f"""
    <!DOCTYPE html>
    <html lang="pt">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Centro Auto Sofisticar - Agendamento</title>
        <!-- Flatpickr CSS -->
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/flatpickr/dist/flatpickr.min.css">
        <script src="https://cdn.jsdelivr.net/npm/flatpickr"></script>
        <style>
            body {{ font-family: 'Segoe UI', Roboto, sans-serif; background-color: #121212; color: #e0e0e0; margin: 0; padding: 20px; }}
            .container {{ max-width: 650px; margin: 0 auto; background: #1e1e1e; padding: 30px; border-radius: 12px; border-top: 5px solid #d4af37; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }}
            h1 {{ text-align: center; color: #fff; margin-bottom: 5px; font-size: 26px; }}
            .sub {{ text-align: center; color: #d4af37; font-weight: bold; margin-bottom: 25px; text-transform: uppercase; font-size: 13px; }}
            .nav-btn {{ display: block; text-align: center; background: #2a2a2a; color: #d4af37; text-decoration: none; padding: 10px; border-radius: 6px; margin-bottom: 25px; border: 1px solid #333; font-weight: bold; }}
            label {{ font-size: 14px; font-weight: bold; display: block; margin-top: 15px; margin-bottom: 5px; color: #bbb; }}
            input, select, textarea {{ width: 100%; padding: 12px; background: #2a2a2a; border: 1px solid #444; border-radius: 6px; color: #fff; box-sizing: border-box; font-size: 15px; }}
            .info-box {{ background: #262626; padding: 12px; border-left: 4px solid #d4af37; margin-top: 10px; border-radius: 4px; font-size: 14px; display: none; }}
            .horarios-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(90px, 1fr)); gap: 10px; margin-top: 10px; }}
            .hora-slot {{ padding: 10px; text-align: center; border-radius: 6px; font-weight: bold; cursor: pointer; border: 1px solid #444; background: #2a2a2a; color: #fff; }}
            .hora-slot.selecionado {{ background: #d4af37; color: #121212; border-color: #d4af37; }}
            .hora-slot.esgotado {{ background: #333; color: #777; cursor: not-allowed; opacity: 0.6; }}
            button[type="submit"] {{ width: 100%; background: #d4af37; color: #121212; border: none; padding: 15px; border-radius: 6px; font-size: 16px; font-weight: bold; margin-top: 25px; cursor: pointer; }}
            .rgpd-notice {{ font-size: 12px; color: #888; text-align: center; margin-top: 15px; line-height: 1.4; }}
        </style>
        <script>
            const infoServicos = {SERVICOS};
            function atualizarInfo() {{
                const val = document.getElementById("servico").value;
                const box = document.getElementById("info-box");
                if (val && infoServicos[val]) {{
                    box.style.display = "block";
                    box.innerHTML = "<b>Estimativa:</b> " + infoServicos[val].preco + " | <b>Tempo médio:</b> " + infoServicos[val].tempo;
                }} else {{ box.style.display = "none"; }}
            }}

            async function carregarHorarios(dataStr) {{
                const container = document.getElementById("horarios_container");
                container.innerHTML = "<p style='color:#aaa;'>A carregar vagas...</p>";
                
                const response = await fetch('/api/vagas?data=' + dataStr);
                const horarios = await response.json();
                
                container.innerHTML = "";
                horarios.forEach(h => {{
                    const btn = document.createElement("div");
                    btn.className = "hora-slot " + (h.disponivel ? "" : "esgotado");
                    btn.innerText = h.hora;
                    
                    if (h.disponivel) {{
                        btn.onclick = function() {{
                            document.querySelectorAll(".hora-slot").forEach(el => el.classList.remove("selecionado"));
                            btn.classList.add("selecionado");
                            document.getElementById("hora_escolhida").value = h.hora;
                        }};
                    }} else {{
                        btn.title = "Horário esgotado";
                    }}
                    container.appendChild(btn);
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
                
                <label>Data Pretendida:</label>
                <input type="text" id="data_picker" name="data" placeholder="Clique para abrir o calendário..." required readonly style="background:#2a2a2a; cursor:pointer;">
                
                <label>Horários Disponíveis:</label>
                <input type="hidden" id="hora_escolhida" name="hora" required>
                <div id="horarios_container" style="color: #777; font-size: 14px; font-style: italic;">Selecione primeiro uma data no calendário acima.</div>
                
                <label>Observações / Detalhes:</label>
                <textarea name="observacoes" rows="3" placeholder="Ex: Ruído na travagem, pedido de orçamento..."></textarea>
                
                <button type="submit">SUBMETER AGENDAMENTO</button>
                
                <div class="rgpd-notice">
                    🔒 <b>Proteção de Dados:</b> Em conformidade com o RGPD, os seus dados são eliminados automaticamente após 30 dias.
                </div>
            </form>
        </div>

        <script>
            flatpickr("#data_picker", {{
                dateFormat: "Y-m-d",
                minDate: "today",
                locale: {{
                    firstDayOfWeek: 1,
                    weekdays: {{
                        shorthand: ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb'],
                        longhand: ['Domingo', 'Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado']
                    }},
                    months: {{
                        shorthand: ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'],
                        longhand: ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
                    }}
                }},
                onChange: function(selectedDates, dateStr) {{
                    carregarHorarios(dateStr);
                }}
            }});
        </script>
    </body>
    </html>
    """

# 📄 ORÇAMENTO DIGITAL
@app.get("/orcamento", response_class=HTMLResponse)
def ver_orcamento(id: int):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, cliente, contacto, matricula, detalhes, valor_estimado, validade, criado_em FROM orcamentos WHERE id = ?", (id,))
    reg = cursor.fetchone()
    conn.close()

    if not reg: return "<h3>Orçamento não encontrado ou expirado.</h3>"
    id_o, cli, cnt, mat, det, val, validade, criado = reg

    return f"""
    <!DOCTYPE html>
    <html lang="pt">
    <head>
        <meta charset="UTF-8">
        <title>Orçamento #{id_o} - Centro Auto Sofisticar</title>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 40px; background: #fff; color: #000; max-width: 650px; margin: 0 auto; border: 2px solid #d4af37; border-radius: 8px; }}
            h1 {{ color: #121212; border-bottom: 2px solid #d4af37; padding-bottom: 10px; margin-bottom: 5px; }}
            .sub {{ color: #888; font-size: 13px; text-transform: uppercase; margin-bottom: 25px; }}
            .box {{ background: #f9f9f9; padding: 15px; border-radius: 6px; margin-bottom: 20px; border: 1px solid #eee; }}
            .field {{ margin-bottom: 10px; font-size: 15px; }}
            .field label {{ font-weight: bold; color: #444; display: inline-block; width: 140px; }}
            .total {{ font-size: 22px; color: #d4af37; font-weight: bold; text-align: right; margin-top: 20px; border-top: 2px solid #eee; padding-top: 15px; }}
            .footer {{ margin-top: 40px; font-size: 11px; color: #777; border-top: 1px dashed #ccc; padding-top: 15px; text-align: center; }}
            .btn-print {{ background: #d4af37; border: none; padding: 10px 20px; font-weight: bold; cursor: pointer; border-radius: 5px; margin-bottom: 20px; }}
            @media print {{ .btn-print {{ display: none; }} body {{ border: none; padding: 0; }} }}
        </style>
    </head>
    <body>
        <button onclick="window.print()" class="btn-print">🖨️ Imprimir / Guardar em PDF</button>
        <h1>CENTRO AUTO SOFISTICAR</h1>
        <div class="sub">Proposta de Orçamento Automóvel Nº {id_o}</div>
        <div class="box">
            <div class="field"><label>Cliente:</label> {cli}</div>
            <div class="field"><label>Contacto:</label> {cnt}</div>
            <div class="field"><label>Viatura / Matrícula:</label> <b>{mat}</b></div>
            <div class="field"><label>Data da Proposta:</label> {criado}</div>
            <div class="field"><label>Validade:</label> {validade}</div>
        </div>
        <h3>Descrição do Serviço / Peças:</h3>
        <div class="box" style="white-space: pre-line; line-height: 1.5;">{det}</div>
        <div class="total">TOTAL ESTIMADO: {val:.2f} €</div>
        <div class="footer">📌 Documento orientador sujeito a confirmação em oficina.<br>Centro Auto Sofisticar • RGPD 30 Dias</div>
    </body>
    </html>
    """

@app.post("/criar_orcamento")
def criar_orcamento(
    cliente: str = Form(...), contacto: str = Form(...), matricula: str = Form(...),
    detalhes: str = Form(...), valor_estimado: float = Form(...), validade: str = Form("15 dias"), pin: str = Form(...)
):
    if pin == PIN_ACESSO:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO orcamentos (cliente, contacto, matricula, detalhes, valor_estimado, validade) VALUES (?, ?, ?, ?, ?, ?)", 
                       (cliente, contacto, matricula.upper(), detalhes, valor_estimado, validade))
        conn.commit()
        conn.close()
    return RedirectResponse(url=f"/painel?pin={pin}", status_code=303)

@app.get("/comprovativo", response_class=HTMLResponse)
def emitir_comprovativo(id: int):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, cliente, contacto, matricula, servico, data, hora, estado, criado_em FROM agendamentos WHERE id = ?", (id,))
    reg = cursor.fetchone()
    conn.close()
    if not reg: return "<h3>Comprovativo não encontrado.</h3>"
    id_i, cli, cnt, mat, srv, dt, hr, est, criado = reg
    return f"""
    <!DOCTYPE html>
    <html lang="pt">
    <head><title>Comprovativo #{id_i}</title>
    <style>body {{ font-family: Arial; padding: 40px; max-width: 600px; margin: auto; border: 2px solid #d4af37; border-radius: 8px; }}</style>
    </head>
    <body>
        <h2>CENTRO AUTO SOFISTICAR</h2>
        <p><b>Agendamento Nº:</b> #{id_i}</p>
        <p><b>Cliente:</b> {cli} ({cnt})</p>
        <p><b>Matrícula:</b> {mat}</p>
        <p><b>Serviço:</b> {srv}</p>
        <p><b>Data:</b> {dt} às {hr}</p>
        <p><b>Estado:</b> {est}</p>
        <button onclick="window.print()">🖨️ Imprimir</button>
    </body>
    </html>
    """

@app.get("/estado", response_class=HTMLResponse)
def acompanhar_estado(matricula: str = ""):
    resultado = ""
    if matricula:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT id, cliente, servico, data, hora, estado FROM agendamentos WHERE UPPER(matricula) = ? ORDER BY id DESC LIMIT 1", (matricula.strip().upper(),))
        reg = cursor.fetchone()
        conn.close()
        if reg:
            id_i, cli, srv, dt, hr, est = reg
            resultado = f"<div style='background:#222; padding:15px; margin-top:15px; border-radius:6px;'><h3>Viatura: {matricula.upper()}</h3><p>Serviço: {srv}</p><p>Data: {dt} às {hr}</p><p><b>Estado: {est.upper()}</b></p></div>"
        else:
            resultado = "<p style='color:#ff6b6b; margin-top:15px;'>❌ Veículo não encontrado.</p>"
    return f"""
    <!DOCTYPE html>
    <html lang="pt"><head><title>Consultar Estado</title>
    <style>body {{ font-family: sans-serif; background: #121212; color: #fff; padding: 30px; display: flex; justify-content: center; }} .box {{ background: #1e1e1e; padding: 30px; border-radius: 10px; width: 400px; border-top: 4px solid #d4af37; }} input {{ width: 100%; padding: 10px; background: #2a2a2a; border: 1px solid #444; color: #fff; text-transform: uppercase; margin-bottom: 10px; }} button {{ width: 100%; padding: 10px; background: #d4af37; border: none; font-weight: bold; cursor: pointer; }}</style>
    </head>
    <body>
        <div class="box">
            <h2>Consultar Estado</h2>
            <form action="/estado" method="get">
                <input type="text" name="matricula" placeholder="Matrícula" value="{matricula}" required>
                <button type="submit">Pesquisar</button>
            </form>
            {resultado}
            <a href="/cliente" style="color:#d4af37; display:block; margin-top:15px; text-align:center;">Voltar</a>
        </div>
    </body>
    </html>
    """

@app.post("/agendar")
def processar_agendamento(cliente: str = Form(...), contacto: str = Form(...), matricula: str = Form(...), servico: str = Form(...), data: str = Form(...), hora: str = Form(...), observacoes: str = Form("")):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO agendamentos (cliente, contacto, matricula, servico, data, hora, observacoes) VALUES (?, ?, ?, ?, ?, ?, ?)",
                   (cliente, contacto, matricula.upper(), servico, data, hora, observacoes))
    novo_id = cursor.lastrowid
    conn.commit()
    conn.close()

    if GESTOR_PHONE_NUMBER:
        enviar_sms(GESTOR_PHONE_NUMBER, f"🚨 Novo Agendamento #{novo_id}\nCliente: {cliente}\nMatrícula: {matricula.upper()}\nData: {data} às {hora}")

    return RedirectResponse(url=f"/cliente?sucesso=True&id_agendamento={novo_id}", status_code=303)

@app.post("/alterar_estado")
def alterar_estado(id_agendamento: int = Form(...), novo_estado: str = Form(...), pin: str = Form(...)):
    if pin == PIN_ACESSO:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT cliente, contacto FROM agendamentos WHERE id = ?", (id_agendamento,))
        reg = cursor.fetchone()
        cursor.execute("UPDATE agendamentos SET estado = ? WHERE id = ?", (novo_estado, id_agendamento))
        conn.commit()
        conn.close()
        if reg:
            cli, cnt = reg
            msgs = {
                "Confirmado": f"Ola {cli}, o seu agendamento foi Confirmado!",
                "Em Oficina": f"Ola {cli}, a sua viatura ja esta em oficina.",
                "Pronto a Levantar": f"Ola {cli}, a sua viatura esta Pronta a levantar!"
            }
            if novo_estado in msgs: enviar_sms(cnt, msgs[novo_estado])
    return RedirectResponse(url=f"/painel?pin={pin}", status_code=303)

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
            enviar_sms(cnt, f"Lembrete: Ola {cli}, lembramos do seu agendamento para {dt} as {hr}.")
    return RedirectResponse(url=f"/painel?pin={pin}", status_code=303)

@app.get("/exportar_csv")
def exportar_csv(pin: str = ""):
    if pin != PIN_ACESSO: return Response("Acesso negado", status_code=403)
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, cliente, contacto, matricula, servico, data, hora, estado, observacoes, criado_em FROM agendamentos ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Cliente", "Contacto", "Matricula", "Servico", "Data", "Hora", "Estado", "Observacoes", "Criado Em"])
    writer.writerows(rows)
    return Response(content=output.getvalue(), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=agendamentos.csv"})

@app.get("/painel", response_class=HTMLResponse)
def painel(request: Request, pin: str = "", busca: str = ""):
    if pin != PIN_ACESSO:
        return """
        <!DOCTYPE html><head><title>Login</title></head>
        <body style="background:#121212; color:#fff; display:flex; justify-content:center; align-items:center; height:100vh; font-family:sans-serif;">
            <form action="/painel" method="get" style="background:#1e1e1e; padding:30px; border-radius:8px; border-top:4px solid #d4af37; text-align:center;">
                <h3>Painel de Gestão</h3>
                <input type="password" name="pin" placeholder="PIN" style="padding:10px; text-align:center;" required autofocus><br><br>
                <button style="padding:10px 20px; background:#d4af37; border:none; font-weight:bold; cursor:pointer;">Entrar</button>
            </form>
        </body></html>
        """
    
    base_url = str(request.base_url).rstrip('/')
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    if busca:
        q = f"%{busca}%"
        cursor.execute("SELECT id, cliente, contacto, matricula, servico, data, hora, observacoes, estado FROM agendamentos WHERE cliente LIKE ? OR matricula LIKE ? ORDER BY id DESC", (q, q))
    else:
        cursor.execute("SELECT id, cliente, contacto, matricula, servico, data, hora, observacoes, estado FROM agendamentos ORDER BY id DESC")
    agendamentos = cursor.fetchall()

    cursor.execute("SELECT id, cliente, contacto, matricula, detalhes, valor_estimado, validade, criado_em FROM orcamentos ORDER BY id DESC")
    orcamentos = cursor.fetchall()
    conn.close()

    linhas_ag = ""
    for r in agendamentos:
        id_i, cli, cnt, mat, srv, dt, hr, obs, est = r
        opts = "".join([f'<option value="{e}" {"selected" if est==e else ""}>{e}</option>' for e in ["Pendente", "Confirmado", "Em Oficina", "Pronto a Levantar", "Concluído"]])
        linhas_ag += f"""
        <tr style="border-bottom:1px solid #333;">
            <td style="padding:10px;">#{id_i}</td>
            <td style="padding:10px;"><b>{cli}</b><br><small>{cnt}</small></td>
            <td style="padding:10px;">{mat}</td>
            <td style="padding:10px;">{srv}</td>
            <td style="padding:10px;">{dt} {hr}</td>
            <td style="padding:10px;">
                <form action="/alterar_estado" method="post" style="display:inline;">
                    <input type="hidden" name="id_agendamento" value="{id_i}"><input type="hidden" name="pin" value="{pin}">
                    <select name="novo_estado" onchange="this.form.submit()" style="background:#2a2a2a; color:#fff; padding:5px;">{opts}</select>
                </form>
                <form action="/enviar_lembrete" method="post" style="display:inline; margin-left:5px;">
                    <input type="hidden" name="id_agendamento" value="{id_i}"><input type="hidden" name="pin" value="{pin}">
                    <button title="Enviar Lembrete SMS" style="background:#2a2a2a; color:#d4af37; border:1px solid #555; padding:5px;">🔔 SMS</button>
                </form>
            </td>
        </tr>
        """

    linhas_orc = ""
    for o in orcamentos:
        id_o, cli_o, cnt_o, mat_o, det_o, val_o, val_id, _ = o
        num_wa = "".join(filter(str.isdigit, cnt_o))
        if len(num_wa) == 9: num_wa = f"351{num_wa}"
        url_orc = f"{base_url}/orcamento?id={id_o}"
        msg_wa = urllib.parse.quote(f"Ola {cli_o}! Enviamos a proposta de orcamento para a viatura {mat_o}.\nTotal: {val_o:.2f}€\nConsulte aqui: {url_orc}")
        linhas_orc += f"""
        <tr style="border-bottom:1px solid #333;">
            <td style="padding:10px;">#{id_o}</td>
            <td style="padding:10px;"><b>{cli_o}</b><br><small>{cnt_o}</small></td>
            <td style="padding:10px;">{mat_o}</td>
            <td style="padding:10px; color:#28a745; font-weight:bold;">{val_o:.2f} €</td>
            <td style="padding:10px;">
                <a href="https://wa.me/{num_wa}?text={msg_wa}" target="_blank" style="background:#25D366; color:#fff; padding:5px 8px; text-decoration:none; border-radius:4px; font-weight:bold;">📲 WhatsApp</a>
                <a href="/orcamento?id={id_o}" target="_blank" style="background:#333; color:#d4af37; padding:5px 8px; text-decoration:none; border-radius:4px; margin-left:5px;">📄 PDF</a>
            </td>
        </tr>
        """

    return f"""
    <!DOCTYPE html><head><title>Painel Gestor</title>
    <style>body{{font-family:sans-serif; background:#121212; color:#fff; padding:20px;}} table{{width:100%; border-collapse:collapse; background:#1e1e1e; margin-bottom:20px;}} th{{background:#252525; padding:10px; color:#d4af37; text-align:left;}} input,textarea{{background:#2a2a2a; color:#fff; border:1px solid #444; padding:8px;}}</style>
    </head>
    <body>
        <h2>🛠️ Painel de Gestão - Centro Auto Sofisticar</h2>
        <a href="/exportar_csv?pin={pin}" style="background:#d4af37; color:#121212; padding:8px 12px; text-decoration:none; font-weight:bold; border-radius:4px; display:inline-block; margin-bottom:20px;">📥 Exportar CSV</a>
        
        <div style="background:#1e1e1e; padding:15px; border-left:4px solid #d4af37; margin-bottom:20px;">
            <h3 style="margin-top:0; color:#d4af37;">Criar Novo Orçamento</h3>
            <form action="/criar_orcamento" method="post" style="display:grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap:10px;">
                <input type="hidden" name="pin" value="{pin}">
                <input type="text" name="cliente" placeholder="Nome" required>
                <input type="text" name="contacto" placeholder="Telemóvel" required>
                <input type="text" name="matricula" placeholder="Matrícula" style="text-transform:uppercase;" required>
                <input type="number" step="0.01" name="valor_estimado" placeholder="Valor (€)" required>
                <textarea name="detalhes" placeholder="Detalhes..." style="grid-column:1/-1;" required></textarea>
                <button type="submit" style="grid-column:1/-1; background:#d4af37; border:none; font-weight:bold; padding:10px; cursor:pointer;">Emitir Orçamento</button>
            </form>
        </div>

        <h3 style="color:#d4af37;">Propostas de Orçamentos</h3>
        <table>
            <tr><th>ID</th><th>Cliente</th><th>Matrícula</th><th>Valor</th><th>Ações</th></tr>
            {linhas_orc if linhas_orc else '<tr><td colspan="5" style="padding:15px; text-align:center;">Nenhum orçamento.</td></tr>'}
        </table>

        <h3 style="color:#d4af37;">Agendamentos Marcados</h3>
        <form action="/painel" method="get" style="margin-bottom:10px; display:flex; gap:10px;">
            <input type="hidden" name="pin" value="{pin}">
            <input type="text" name="busca" placeholder="Pesquisar..." value="{busca}" style="flex:1;">
            <button type="submit" style="background:#d4af37; border:none; padding:8px; font-weight:bold;">Pesquisar</button>
        </form>
        <table>
            <tr><th>ID</th><th>Cliente</th><th>Matrícula</th><th>Serviço</th><th>Data/Hora</th><th>Ações</th></tr>
            {linhas_ag if linhas_ag else '<tr><td colspan="6" style="padding:15px; text-align:center;">Nenhum agendamento.</td></tr>'}
        </table>
    </body></html>
    """

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
