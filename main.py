from fastapi import FastAPI, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import sqlite3
import os

app = FastAPI(title="Centro Auto Sofisticar - Plataforma Completa")

# --- CONFIGURAÇÃO E SEGURANÇA ---
PIN_ACESSO = "1234"
DB_FILE = "oficina.db"

# --- BASE DE DADOS & CATÁLOGO ---
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
            preco REAL DEFAULT 0.0
        )
    """)
    conn.commit()
    conn.close()

init_db()

SERVICOS = [
    {"id": "mecanica", "nome": "Mecânica Geral / Manutenção", "preco": 60.0},
    {"id": "eletrica", "nome": "Elétrica Auto & Diagnóstico", "preco": 45.0},
    {"id": "ac", "nome": "Ar Condicionado (Carga e Manutenção)", "preco": 55.0},
    {"id": "polimento", "nome": "Polimento e Detalhe Automóvel", "preco": 120.0},
    {"id": "lavagem_simples", "nome": "Lavagens - Exterior", "preco": 15.0},
    {"id": "lavagem_completa", "nome": "Lavagens - Completa (Interior + Exterior)", "preco": 30.0},
    {"id": "higienizacao", "nome": "Lavagens - Higienização de Estofos", "preco": 75.0},
]

# --- ESTILOS CSS (DARK PREMIUM & GOLD) ---
CSS_GLOBAL = """
<style>
    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #1a1a1a; margin: 0; padding: 20px; color: #E0E0E0; }
    .container { max-width: 800px; margin: 0 auto; background: #222; padding: 30px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.5); border-top: 6px solid #d4af37; }
    h1 { color: #fff; text-align: center; font-size: 26px; text-transform: uppercase; letter-spacing: 1px; }
    .slogan { text-align: center; color: #d4af37; font-weight: bold; margin-bottom: 20px; text-transform: uppercase; font-size: 14px; }
    label { font-weight: bold; display: block; margin-top: 15px; margin-bottom: 5px; color: #d4af37; }
    input, select, textarea { width: 100%; padding: 12px; border: 1px solid #444; background: #333; color: white; border-radius: 6px; box-sizing: border-box; font-size: 15px; }
    button { width: 100%; background-color: #1a1a1a; color: #d4af37; border: 2px solid #d4af37; padding: 15px; border-radius: 6px; font-size: 16px; font-weight: bold; margin-top: 25px; cursor: pointer; transition: 0.3s; }
    button:hover { background-color: #d4af37; color: #1a1a1a; }
    table { width: 100%; border-collapse: collapse; background: #222; border-radius: 8px; overflow: hidden; margin-top: 20px; }
    th, td { padding: 14px 15px; text-align: left; border-bottom: 1px solid #333; }
    th { background-color: #1a1a1a; color: #d4af37; }
    .btn-acao { color: #d4af37; text-decoration: none; font-weight: bold; margin-right: 10px; }
    .btn-acao:hover { text-decoration: underline; }
</style>
"""

# --- ROTAS DA APLICAÇÃO ---

@app.get("/", response_class=HTMLResponse)
def inicio():
    return RedirectResponse(url="/cliente")

@app.get("/cliente", response_class=HTMLResponse)
def pagina_cliente(sucesso: bool = False):
    opcoes = "".join([f'<option value="{s["nome"]}" data-preco="{s["preco"]}">{s["nome"]} — [{s["preco"]}€]</option>' for s in SERVICOS])
    msg = '<div style="background-color:#d4af37; color:#1a1a1a; padding:15px; border-radius:8px; margin-bottom:20px; text-align:center; font-weight:bold;">✅ Agendamento enviado com sucesso!</div>' if sucesso else ''
    
    return f"""
    <!DOCTYPE html><html lang="pt"><head><meta charset="UTF-8"><title>Centro Auto Sofisticar - Agendamento</title>{CSS_GLOBAL}</head>
    <body>
        <div class="container">
            <h1>CENTRO AUTO SOFISTICAR</h1>
            <div class="slogan">Qualidade e Confiança para o seu Carro!</div>
            {msg}
            <form action="/agendar" method="post">
                <label>Nome Completo:</label><input type="text" name="cliente" required placeholder="Ex: João Silva">
                <label>Telefone / Telemóvel:</label><input type="tel" name="contacto" required placeholder="Ex: 912345678">
                <label>Matrícula da Viatura:</label><input type="text" name="matricula" required placeholder="Ex: AA-00-AA">
                <label>Serviço Pretendido:</label><select name="servico" required>{opcoes}</select>
                <label>Data Pretendida:</label><input type="date" name="data" required>
                <label>Hora Pretendida:</label><input type="time" name="hora" required>
                <label>Observações:</label><textarea name="observacoes" rows="3"></textarea>
                <button type="submit">MARCAR AGENDAMENTO</button>
            </form>
        </div>
    </body></html>
    """

@app.post("/agendar")
def processar_agendamento(cliente: str = Form(...), contacto: str = Form(...), matricula: str = Form(...), servico: str = Form(...), data: str = Form(...), hora: str = Form(...), observacoes: str = Form("")):
    preco_base = next((s["preco"] for s in SERVICOS if s["nome"] == servico), 50.0)
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO agendamentos (cliente, contacto, matricula, servico, data, hora, observacoes, preco) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                   (cliente, contacto, matricula, servico, data, hora, observacoes, preco_base))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/cliente?sucesso=True", status_code=303)

@app.get("/painel", response_class=HTMLResponse)
def pagina_painel(pin: str = ""):
    if pin != PIN_ACESSO:
        return f"""
        <!DOCTYPE html><html lang="pt"><head><meta charset="UTF-8"><title>Login - Gestor</title>{CSS_GLOBAL}</head>
        <body style="display:flex; justify-content:center; align-items:center; height:100vh;">
            <div class="container" style="width:350px; text-align:center;">
                <h3>⚙️ Área do Gestor</h3>
                <form action="/painel" method="get">
                    <input type="password" name="pin" placeholder="PIN (1234)" required autofocus style="text-align:center; letter-spacing:4px; font-size:18px;">
                    <button type="submit">ENTRAR</button>
                </form>
            </div>
        </body></html>
        """
    
    conn = sqlite3.connect(DB_FILE)
    registos = conn.execute("SELECT id, cliente, contacto, matricula, servico, data, hora, estado, preco FROM agendamentos ORDER BY id DESC").fetchall()
    conn.close()
    
    linhas = ""
    for r in registos:
        rid, cliente, contacto, matricula, servico, data, hora, estado, preco = r
        iva = round(preco * 0.23, 2)
        total_com_iva = round(preco + iva, 2)
        
        linhas += f"""
        <tr>
            <td>#{rid}</td>
            <td><b>{cliente}</b><br><small>{contacto}</small></td>
            <td><span style="background:#333; color:#d4af37; padding:3px 8px; border-radius:4px; font-weight:bold;">{matricula}</span></td>
            <td><b>{servico}</b></td>
            <td>{data} às {hora}</td>
            <td><b>{total_com_iva}€</b><br><small>IVA incl.</small></td>
            <td>
                <a class="btn-acao" href="/gerar_pdf/{rid}">📥 PDF</a>
                <a class="btn-acao" href="https://wa.me/351{contacto}?text=Olá%20{cliente},%20o%20seu%20serviço%20({servico})%20no%20Centro%20Auto%20Sofisticar%20está%20confirmado!">💬 WhatsApp</a>
            </td>
        </tr>
        """
    
    return f"""
    <!DOCTYPE html><html lang="pt"><head><meta charset="UTF-8"><title>Painel - Centro Auto Sofisticar</title>{CSS_GLOBAL}</head>
    <body>
        <div class="container" style="max-width: 1100px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <h2>🛠️ Painel de Gestão - Centro Auto Sofisticar</h2>
                <span>Total Registos: <b>{len(registos)}</b></span>
            </div>
            <table>
                <thead>
                    <tr><th>ID</th><th>Cliente</th><th>Matrícula</th><th>Serviço</th><th>Data & Hora</th><th>Total (c/ IVA)</th><th>Ações & Faturação</th></tr>
                </thead>
                <tbody>
                    {linhas if linhas else '<tr><td colspan="7" style="text-align:center;">Sem agendamentos registados.</td></tr>'}
                </tbody>
            </table>
        </div>
    </body></html>
    """

@app.get("/gerar_pdf/{id_agendamento}")
def obter_pdf(id_agendamento: int):
    conn = sqlite3.connect(DB_FILE)
    r = conn.execute("SELECT id, cliente, contacto, matricula, servico, data, hora, preco FROM agendamentos WHERE id=?", (id_agendamento,)).fetchone()
    conn.close()
    
    if not r:
        raise HTTPException(status_code=404, detail="Orçamento não encontrado")
    
    rid, cliente, contacto, matricula, servico, data, hora, preco = r
    iva = round(preco * 0.23, 2)
    total = round(preco + iva, 2)
    
    filename = f"orcamento_{rid}.pdf"
    c = canvas.Canvas(filename, pagesize=A4)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, 800, "CENTRO AUTO SOFISTICAR - ORÇAMENTO")
    c.setFont("Helvetica", 12)
    c.drawString(50, 760, f"ID do Registo: #{rid} | Data: {data}")
    c.drawString(50, 740, f"Cliente: {cliente} | Contacto: {contacto}")
    c.drawString(50, 720, f"Matrícula da Viatura: {matricula}")
    c.line(50, 700, 550, 700)
    
    c.drawString(50, 670, f"Serviço Selecionado: {servico}")
    c.drawString(50, 640, f"Valor Líquido (s/ IVA): {preco}€")
    c.drawString(50, 620, f"IVA (23%): {iva}€")
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, 590, f"TOTAL COM IVA: {total}€")
    c.save()
    
    return FileResponse(filename, media_type='application/pdf', filename=filename)
