from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
import sqlite3
import os

app = FastAPI(title="Centro Auto Sofisticar - Gestão de Elite")
DB_FILE = "oficina.db"
PIN_ACESSO = os.getenv("GESTOR_PIN", "1234")

# 🛠️ CATÁLOGO GERAL E COMPLETO DE PEÇAS E SERVIÇOS POR CATEGORIA
CATALOGO_COMPLETO = {
    "🛞 Pneus & Direção": {
        "Pneu 175/65 R14": 50.00,
        "Pneu 195/65 R15": 65.00,
        "Pneu 205/55 R16": 85.00,
        "Pneu 225/45 R17": 110.00,
        "Alinhamento de Direção": 35.00,
        "Equilíbrio de Rodas (Cada)": 10.00
    },
    "🌡️ Sistema de Temperatura / Refrigeração": {
        "Termóstato": 35.00,
        "Bomba de Água": 75.00,
        "Radiador Principal": 140.00,
        "Ventoinha do Radiador": 90.00,
        "Sensor de Temperatura": 25.00,
        "Líquido de Refrigeração / Anticongelante (5L)": 20.00,
        "Mangueira de Refrigeração": 30.00,
        "Substituição e Purga do Sistema (Mão de Obra)": 45.00
    },
    "🛑 Sistema de Travões": {
        "Pastilhas de Travão (Frente)": 55.00,
        "Pastilhas de Travão (Traseiras)": 45.00,
        "Discos de Travão (Par Frente)": 90.00,
        "Discos de Travão (Par Traseiro)": 80.00,
        "Líquido de Travões": 15.00,
        "Pinça de Travão Recondicionada": 120.00
    },
    "🛢️ Óleos e Filtros (Revisão)": {
        "Óleo Motor 5W30 (5L)": 50.00,
        "Óleo Motor 10W40 (5L)": 40.00,
        "Filtro de Óleo": 15.00,
        "Filtro de Ar": 20.00,
        "Filtro de Combustível": 25.00,
        "Filtro de Habitáculo / Polén": 25.00
    },
    "⚡ Eletricidade & Arranque": {
        "Bateria 12V 60Ah": 85.00,
        "Bateria 12V 74Ah": 110.00,
        "Alternador Recondicionado": 180.00,
        "Motor de Arranque": 150.00,
        "Velas de Ignição (Jogo de 4)": 40.00,
        "Velas de Preaquecimento (Diesel - Jogo)": 60.00
    },
    "⚙️ Motor & Distribuição": {
        "Kit de Correia de Distribuição": 120.00,
        "Kit de Correia de Acessórios (Alternador)": 45.00,
        "Junta da Colaça": 85.00,
        "Válvula EGR": 160.00
    },
    "🔧 Mão de Obra Geral": {
        "Mão de Obra Especializada (Hora)": 35.00,
        "Diagnóstico Eletrónico / Computador": 30.00,
        "Serviço de Descarbonização": 60.00
    }
}

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
            criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orcamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            cliente TEXT NOT NULL,
            matricula TEXT NOT NULL,
            pecas TEXT NOT NULL,
            descricao TEXT,
            subtotal REAL NOT NULL,
            iva REAL NOT NULL,
            total REAL NOT NULL,
            estado TEXT DEFAULT 'Pendente',
            criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_db()

@app.get("/", response_class=HTMLResponse)
def pagina_cliente(pin: str = PIN_ACESSO):
    return f"""
    <!DOCTYPE html>
    <html lang="pt">
    <head>
        <meta charset="UTF-8">
        <title>Centro Auto Sofisticar - Agendamentos</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #121212; color: #fff; margin: 0; padding: 20px; }}
            .container {{ max-width: 650px; margin: 40px auto; background: #181818; padding: 35px; border-radius: 12px; border-top: 5px solid #d4af37; box-shadow: 0 8px 20px rgba(0,0,0,0.5); }}
            .header {{ display: flex; align-items: center; margin-bottom: 25px; }}
            input, select, textarea {{ width: 100%; padding: 12px; background: #2a2a2a; border: 1px solid #555; border-radius: 6px; color: #fff; margin-bottom: 15px; box-sizing: border-box; font-size: 14px; }}
            button {{ background: #d4af37; color: #121212; border: none; padding: 14px; font-weight: bold; border-radius: 6px; cursor: pointer; width: 100%; font-size: 16px; transition: 0.3s; }}
            button:hover {{ background: #b8972f; }}
            .admin-link {{ display: block; text-align: center; margin-top: 20px; color: #d4af37; text-decoration: none; font-size: 13px; }}
            .admin-link:hover {{ text-decoration: underline; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <span style="font-size: 45px; margin-right: 20px;">🏎️</span>
                <div>
                    <h1 style="margin:0; font-size: 24px; color:#fff;">Centro Auto Sofisticar</h1>
                    <p style="margin:0; color:#d4af37; font-size: 13px;">Agendamento Online de Serviços & Oficina</p>
                </div>
            </div>
            
            <form action="/agendar_servico" method="post">
                <label><b>Nome Completo:</b></label>
                <input type="text" name="cliente" placeholder="O seu nome" required>

                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                    <div>
                        <label><b>Contacto Telefónico:</b></label>
                        <input type="text" name="contacto" placeholder="912345678" required>
                    </div>
                    <div>
                        <label><b>Matrícula da Viatura:</b></label>
                        <input type="text" name="matricula" placeholder="00-AA-00" style="text-transform:uppercase;" required>
                    </div>
                </div>

                <label><b>Serviço Pretendido:</b></label>
                <select name="servico">
                    <option>Revisão Periódica (Óleos e Filtros)</option>
                    <option>Substituição de Pneus / Alinhamento</option>
                    <option>Sistema de Travões</option>
                    <option>Sistema de Temperatura / Refrigeração</option>
                    <option>Diagnóstico Eletrónico / Avaria</option>
                    <option>Orçamento / Outro Serviço</option>
                </select>

                <label><b>Data Preferida para a Visita:</b></label>
                <input type="date" name="data" required>

                <button type="submit">CONFIRMAR AGENDAMENTO</button>
            </form>
            
            <a href="/painel?pin={pin}" class="admin-link">🔒 Aceder ao Painel de Gestão da Oficina</a>
        </div>
    </body>
    </html>
    """

@app.post("/agendar_servico")
def agendar_servico(cliente: str = Form(...), contacto: str = Form(...), matricula: str = Form(...), servico: str = Form(...), data: str = Form(...)):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO agendamentos (cliente, contacto, matricula, servico, data) VALUES (?, ?, ?, ?, ?)",
                   (cliente, contacto, matricula.upper(), servico, data))
    conn.commit()
    conn.close()
    return """
    <body style="background:#121212; color:#fff; font-family:sans-serif; text-align:center; padding-top:100px;">
        <div style="background:#181818; max-width:450px; margin:auto; padding:40px; border-radius:12px; border:1px solid #333;">
            <h2 style="color:#28a745;">Agendamento Registado com Sucesso!</h2>
            <p style="color:#aaa; line-height:1.6;">Obrigado. A sua viatura foi registada no sistema. Entraremos em contacto para validação final.</p>
            <a href="/" style="display:inline-block; margin-top:20px; background:#d4af37; color:#121212; padding:10px 20px; text-decoration:none; font-weight:bold; border-radius:6px;">Fazer Novo Agendamento</a>
        </div>
    </body>
    """

@app.get("/painel", response_class=HTMLResponse)
def painel(pin: str = ""):
    if pin != PIN_ACESSO:
        return "<body style='background:#121212; color:#fff; text-align:center; padding-top:100px;'><h3 style='color:#ff4d4d;'>Acesso Restrito. PIN incorreto.</h3></body>"
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, cliente, contacto, matricula, servico, data FROM agendamentos ORDER BY id DESC")
    agendamentos = cursor.fetchall()

    cursor.execute("SELECT id, titulo, cliente, matricula, total, estado, criado_em FROM orcamentos ORDER BY id DESC")
    orcamentos = cursor.fetchall()
    conn.close()

    linhas_ag = ""
    for a in agendamentos:
        id_a, cli_a, cont_a, mat_a, serv_a, data_a = a
        linhas_ag += f"""
        <tr style="border-bottom:1px solid #333; background: #1a1a1a;">
            <td style="padding:14px; color:#d4af37; font-weight:bold;">#{id_a}</td>
            <td style="padding:14px;"><b>{cli_a}</b><br><small style="color:#aaa;">{cont_a}</small></td>
            <td style="padding:14px; font-weight:bold;">{mat_a}</td>
            <td style="padding:14px;">{serv_a}</td>
            <td style="padding:14px; color:#f0ad4e;"><b>{data_a}</b></td>
            <td style="padding:14px;">
                <form action="/apagar_agendamento" method="post" style="display:inline;">
                    <input type="hidden" name="id_agendamento" value="{id_a}"><input type="hidden" name="pin" value="{pin}">
                    <button type="submit" onclick="return confirm('Marcar agendamento como concluído/apagar?')" style="background:#8b0000; color:#fff; border:none; padding:6px 12px; border-radius:4px; cursor:pointer; font-weight:bold;">🗑️ Concluir</button>
                </form>
            </td>
        </tr>
        """

    linhas_orc = ""
    for r in orcamentos:
        id_o, titulo, cli, mat, total, est, criado = r
        cor_est = "#f0ad4e" if est == "Pendente" else ("#28a745" if est == "Aprovado" else "#d9534f")
        msg_wa = f"Olá {cli}, o seu orçamento '{titulo}' na Centro Auto Sofisticar (Viatura: {mat}) tem o valor total de {total:.2f}€. Aguardamos a sua confirmação."
        link_wa = f"https://wa.me/?text={msg_wa.replace(' ', '%20')}"

        linhas_orc += f"""
        <tr style="border-bottom:1px solid #333; background: #1a1a1a;">
            <td style="padding:14px; color:#d4af37; font-weight:bold;">#{id_o}</td>
            <td style="padding:14px;"><b>{cli}</b><br><small style="color:#aaa;">{mat}</small></td>
            <td style="padding:14px;">{titulo}</td>
            <td style="padding:14px; color:#28a745; font-weight:bold; font-size:15px;">{total:.2f} €</td>
            <td style="padding:14px;">
                <select onchange="window.location.href='/mudar_estado?id={id_o}&estado='+this.value+'&pin={pin}'" style="background:#2a2a2a; padding:6px; border-radius:4px; border:1px solid #555; color:{cor_est}; font-weight:bold; cursor:pointer;">
                    <option value="Pendente" {'selected' if est == 'Pendente' else ''}>🟡 Pendente</option>
                    <option value="Aprovado" {'selected' if est == 'Aprovado' else ''}>🟢 Aprovado</option>
                    <option value="Recusado" {'selected' if est == 'Recusado' else ''}>🔴 Recusado</option>
                </select>
            </td>
            <td style="padding:14px;">
                <a href="/orcamento?id={id_o}" target="_blank" style="background:#333; color:#d4af37; padding:6px 10px; text-decoration:none; border-radius:4px; font-size:12px; margin-right:4px;">📄 PDF</a>
                <a href="{link_wa}" target="_blank" style="background:#25D366; color:#fff; padding:6px 10px; text-decoration:none; border-radius:4px; font-size:12px; font-weight:bold; margin-right:4px;">📲 WhatsApp</a>
                <form action="/apagar_orcamento" method="post" style="display:inline;">
                    <input type="hidden" name="id_orcamento" value="{id_o}"><input type="hidden" name="pin" value="{pin}">
                    <button type="submit" onclick="return confirm('Tem certeza que pretende apagar este orçamento?')" style="background:#8b0000; color:#fff; border:none; padding:6px 10px; border-radius:4px; cursor:pointer;">🗑️</button>
                </form>
            </td>
        </tr>
        """

    return f"""
    <!DOCTYPE html>
    <html lang="pt">
    <head>
        <meta charset="UTF-8">
        <title>Painel de Gestão - Centro Auto Sofisticar</title>
        <style>
            body {{ font-family: 'Segoe UI', sans-serif; background: #121212; color: #fff; margin: 0; padding: 0; }}
            .header {{ background: linear-gradient(135deg, #1a1a1a, #000); padding: 25px 40px; border-bottom: 3px solid #d4af37; display: flex; align-items: center; justify-content: space-between; }}
            .content {{ padding: 30px; max-width: 1250px; margin: auto; }}
            .btn-new {{ background: #d4af37; color: #121212; padding: 10px 18px; text-decoration: none; font-weight: bold; border-radius: 6px; box-shadow: 0 4px 10px rgba(212,175,55,0.3); }}
            .btn-new:hover {{ background: #b8972f; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 15px; margin-bottom: 30px; background: #181818; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.4); }}
            th {{ background: #222; color: #d4af37; padding: 14px; text-align: left; font-size: 13px; border-bottom: 2px solid #333; }}
        </style>
    </head>
    <body>
        <div class="header">
            <div style="display: flex; align-items: center;">
                <span style="font-size: 45px; margin-right: 20px;">🏎️</span>
                <div>
                    <h1 style="margin:0; font-size: 24px; color:#fff;">Centro Auto Sofisticar</h1>
                    <p style="margin:0; color:#d4af37; font-size: 13px;">Painel de Controlo & Gestão de Oficina</p>
                </div>
            </div>
            <div>
                <a href="/" style="color:#aaa; text-decoration:none; margin-right:20px; font-size:14px; font-weight:bold;">← Ver Site do Cliente</a>
                <a href="/novo_orcamento?pin={pin}" class="btn-new">＋ Criar Novo Orçamento</a>
            </div>
        </div>

        <div class="content">
            <h2 style="color:#fff; margin-bottom: 5px;">📅 Agendamentos Pendentes dos Clientes</h2>
            <table>
                <tr><th>ID</th><th>Cliente / Contacto</th><th>Matrícula</th><th>Serviço Pretendido</th><th>Data</th><th>Ação</th></tr>
                {linhas_ag if linhas_ag else '<tr><td colspan="6" style="text-align:center; padding:25px; color:#777;">Nenhum agendamento de cliente registado.</td></tr>'}
            </table>

            <h2 style="color:#fff; margin-bottom: 5px;">📋 Orçamentos Detalhados por Categoria</h2>
            <table>
                <tr><th>ID</th><th>Cliente / Matrícula</th><th>Título / Avaria</th><th>Total (c/ IVA)</th><th>Estado</th><th>Ações Rápidas</th></tr>
                {linhas_orc if linhas_orc else '<tr><td colspan="6" style="text-align:center; padding:25px; color:#777;">Nenhum orçamento registado de momento.</td></tr>'}
            </table>
        </div>
    </body>
    </html>
    """

@app.get("/novo_orcamento", response_class=HTMLResponse)
def form_orcamento(pin: str = ""):
    if pin != PIN_ACESSO:
        return "<body style='background:#121212; color:#fff; text-align:center; padding-top:50px;'><h3>Acesso restrito. Insira o PIN correto.</h3></body>"

    blocos_html = ""
    for categoria, itens in CATALOGO_COMPLETO.items():
        blocos_html += f"""
        <div style="background:#1e1e1e; padding:15px; margin-bottom:15px; border-radius:8px; border:1px solid #444;">
            <h3 style="color:#d4af37; margin-top:0; border-bottom:1px solid #333; padding-bottom:5px;">{categoria}</h3>
        """
        for peca, preco in itens.items():
            blocos_html += f"""
            <div style="margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; background: #252525; padding: 6px 10px; border-radius: 4px;">
                <label style="cursor: pointer; flex: 1; font-size: 14px;">
                    <input type="checkbox" name="pecas_selecionadas" value="{peca}" style="margin-right: 8px;"> 
                    {peca}
                </label>
                <b style="color:#28a745; font-size: 14px;">{preco:.2f} €</b>
            </div>
            """
        blocos_html += "</div>"

    return f"""
    <!DOCTYPE html>
    <html lang="pt">
    <head>
        <meta charset="UTF-8">
        <title>Criar Orçamento - Centro Auto Sofisticar</title>
        <style>
            body {{ font-family: 'Segoe UI', sans-serif; background: #121212; color: #fff; padding: 20px; }}
            .container {{ max-width: 750px; margin: auto; background: #181818; padding: 30px; border-radius: 12px; border-top: 5px solid #d4af37; box-shadow: 0 8px 20px rgba(0,0,0,0.5); }}
            input[type="text"], textarea {{ width: 100%; padding: 10px; background: #2a2a2a; border: 1px solid #555; border-radius: 6px; color: #fff; margin-bottom: 15px; box-sizing: border-box; }}
            button {{ background: #d4af37; color: #121212; border: none; padding: 12px 20px; font-weight: bold; border-radius: 6px; cursor: pointer; width: 100%; font-size: 16px; }}
            button:hover {{ background: #b8972f; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div style="display:flex; align-items:center; margin-bottom: 15px;">
                <span style="font-size: 30px; margin-right: 15px;">🏎️</span>
                <h2 style="margin:0; color:#d4af37;">Novo Orçamento Detalhado</h2>
            </div>
            <a href="/painel?pin={pin}" style="color:#d4af37; text-decoration:none; display:inline-block; margin-bottom:20px;">← Voltar ao Painel</a>
            
            <form action="/criar_orcamento" method="post">
                <input type="hidden" name="pin" value="{pin}">
                
                <label><b>Título / Objetivo do Orçamento:</b></label>
                <input type="text" name="titulo" placeholder="Ex: Substituição de Kit de Distribuição e Óleos" required>

                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                    <div>
                        <label><b>Nome do Cliente:</b></label>
                        <input type="text" name="cliente" placeholder="Nome completo" required>
                    </div>
                    <div>
                        <label><b>Matrícula:</b></label>
                        <input type="text" name="matricula" placeholder="00-AA-00" style="text-transform:uppercase;" required>
                    </div>
                </div>

                <label><b>Selecione as Peças e Serviços Necessários (por Categoria):</b></label>
                {blocos_html}

                <label><b>Descrição / Notas Adicionais:</b></label>
                <textarea name="descricao" rows="3" placeholder="Observações para o cliente ou mecânico..."></textarea>

                <button type="submit">GERAR ORÇAMENTO COM CÁLCULO DE IVA (23%)</button>
            </form>
        </div>
    </body>
    </html>
    """

@app.post("/criar_orcamento")
def processar_criar_orcamento(
    pin: str = Form(...),
    titulo: str = Form(...),
    cliente: str = Form(...),
    matricula: str = Form(...),
    pecas_selecionadas: list = Form(default=[]),
    descricao: str = Form("")
):
    if pin != PIN_ACESSO:
        return RedirectResponse(url="/painel", status_code=303)

    subtotal = 0.0
    for peca in pecas_selecionadas:
        for cat, itens in CATALOGO_COMPLETO.items():
            if peca in itens:
                subtotal += itens[peca]

    valor_iva = subtotal * 0.23
    total_com_iva = subtotal + valor_iva
    pecas_str = ", ".join(pecas_selecionadas)

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO orcamentos (titulo, cliente, matricula, pecas, descricao, subtotal, iva, total)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (titulo, cliente, matricula.upper(), pecas_str, descricao, subtotal, valor_iva, total_com_iva))
    conn.commit()
    conn.close()

    return RedirectResponse(url=f"/painel?pin={pin}", status_code=303)

@app.get("/mudar_estado")
def mudar_estado(id: int, estado: str, pin: str):
    if pin == PIN_ACESSO:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("UPDATE orcamentos SET estado = ? WHERE id = ?", (estado, id))
        conn.commit()
        conn.close()
    return RedirectResponse(url=f"/painel?pin={pin}", status_code=303)

@app.post("/apagar_orcamento")
def apagar_orcamento(id_orcamento: int = Form(...), pin: str = Form(...)):
    if pin == PIN_ACESSO:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM orcamentos WHERE id = ?", (id_orcamento,))
        conn.commit()
        conn.close()
    return RedirectResponse(url=f"/painel?pin={pin}", status_code=303)

@app.post("/apagar_agendamento")
def apagar_agendamento(id_agendamento: int = Form(...), pin: str = Form(...)):
    if pin == PIN_ACESSO:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM agendamentos WHERE id = ?", (id_agendamento,))
        conn.commit()
        conn.close()
    return RedirectResponse(url=f"/painel?pin={pin}", status_code=303)

@app.get("/orcamento", response_class=HTMLResponse)
def ver_orcamento(id: int):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, titulo, cliente, matricula, pecas, descricao, subtotal, iva, total, estado, criado_em FROM orcamentos WHERE id = ?", (id,))
    reg = cursor.fetchone()
    conn.close()

    if not reg: return "<h3>Orçamento não encontrado.</h3>"
    id_o, titulo, cli, mat, pecas, desc, sub, iva, total, est, criado = reg
    itens_lista = "".join([f"<li>{p.strip()}</li>" for p in pecas.split(",") if p.strip()])

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
            .field {{ margin-bottom: 8px; font-size: 15px; }}
            .field label {{ font-weight: bold; color: #444; display: inline-block; width: 140px; }}
            .totals {{ font-size: 16px; text-align: right; margin-top: 20px; border-top: 2px solid #eee; padding-top: 15px; }}
            .total-final {{ font-size: 22px; color: #d4af37; font-weight: bold; }}
            .footer {{ margin-top: 40px; font-size: 11px; color: #777; border-top: 1px dashed #ccc; padding-top: 15px; text-align: center; }}
            .btn-print {{ background: #d4af37; border: none; padding: 10px 20px; font-weight: bold; cursor: pointer; border-radius: 5px; margin-bottom: 20px; }}
            @media print {{ .btn-print {{ display: none; }} body {{ border: none; padding: 0; }} }}
        </style>
    </head>
    <body>
        <button onclick="window.print()" class="btn-print">🖨️ Imprimir / Guardar em PDF</button>
        <div style="display:flex; align-items:center; margin-bottom: 5px;">
            <span style="font-size: 30px; margin-right: 15px;">🏎️</span>
            <h1 style="margin:0; border:none; padding:0;">CENTRO AUTO SOFISTICAR</h1>
        </div>
        <div class="sub">Proposta de Orçamento Automóvel Nº {id_o} — {titulo}</div>
        
        <div class="box">
            <div class="field"><label>Cliente:</label> {cli}</div>
            <div class="field"><label>Viatura / Matrícula:</label> <b>{mat}</b></div>
            <div class="field"><label>Data:</label> {criado}</div>
            <div class="field"><label>Estado:</label> <b>{est}</b></div>
        </div>

        <h3>Peças e Serviços Selecionados:</h3>
        <div class="box">
            <ul style="margin: 0; padding-left: 20px; line-height: 1.6;">
                {itens_lista}
            </ul>
        </div>

        <h3>Observações Técnicas:</h3>
        <div class="box" style="white-space: pre-line; line-height: 1.5;">{desc if desc else 'Nenhuma observação registada.'}</div>

        <div class="totals">
            <p>Subtotal: {sub:.2f} €</p>
            <p>IVA (23%): {iva:.2f} €</p>
            <div class="total-final">TOTAL ESTIMADO: {total:.2f} €</div>
        </div>

        <div class="footer">📌 Documento orientador sujeito a confirmação física em oficina.<br>Centro Auto Sofisticar</div>
    </body>
    </html>
    """

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
