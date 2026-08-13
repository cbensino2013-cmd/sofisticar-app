from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
import sqlite3
import os

app = FastAPI(title="Centro Auto Sofisticar")

# 🔒 Definir a palavra-passe do Painel de Gestão
PIN_ACESSO = "1234"

# 💾 Configuração da Base de Dados SQLite
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

# Inicializar a base de dados ao arrancar
init_db()

SERVICOS = [
    {"id": "mecanica", "nome": "Mecânica Geral / Manutenção", "preco": "Sob Consulta / Análise"},
    {"id": "eletrica", "nome": "Elétrica Auto & Diagnóstico", "preco": "Sob Consulta / Análise"},
    {"id": "ac", "nome": "Ar Condicionado (Carga e Manutenção)", "preco": "Sob Consulta / Análise"},
    {"id": "polimento", "nome": "Polimento e Detalhe Automóvel", "preco": "Sob Consulta / Análise"},
    {"id": "lavagem_simples", "nome": "Lavagens - Exterior", "preco": "Sob Consulta / Análise"},
    {"id": "lavagem_completa", "nome": "Lavagens - Completa (Interior + Exterior)", "preco": "Sob Consulta / Análise"},
    {"id": "higienizacao", "nome": "Lavagens - Higienização de Estofos", "preco": "Sob Consulta / Análise"},
]

@app.get("/", response_class=HTMLResponse)
def inicio():
    return RedirectResponse(url="/cliente")

# 📱 ÁREA DO CLIENTE
@app.get("/cliente", response_class=HTMLResponse)
def pagina_cliente(sucesso: bool = False):
    opcoes_servicos = "".join(
        f'<option value="{s["nome"]}">{s["nome"]} — [{s["preco"]}]</option>' for s in SERVICOS
    )
    
    mensagem_sucesso = ""
    if sucesso:
        mensagem_sucesso = """
        <div style="background-color: #d4edda; color: #155724; padding: 15px; border-radius: 8px; margin-bottom: 20px; text-align: center; font-weight: bold; border: 1px solid #c3e6cb;">
            ✅ Agendamento enviado com sucesso! O Centro Auto Sofisticar entrará em contacto para confirmar.
        </div>
        """

    html = f"""
    <!DOCTYPE html>
    <html lang="pt">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Centro Auto Sofisticar - Agendamento</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #1a1a1a; margin: 0; padding: 20px; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.3); border-top: 6px solid #d4af37; }}
            h1 {{ color: #1a1a1a; text-align: center; margin-bottom: 2px; font-size: 26px; text-transform: uppercase; letter-spacing: 1px; }}
            .slogan {{ text-align: center; color: #d4af37; font-weight: bold; margin-top: 0; font-size: 14px; margin-bottom: 20px; text-transform: uppercase; }}
            label {{ font-weight: bold; display: block; margin-top: 15px; margin-bottom: 5px; }}
            input, select, textarea {{ width: 100%; padding: 12px; border: 1px solid #ccc; border-radius: 6px; box-sizing: border-box; font-size: 15px; }}
            button {{ width: 100%; background-color: #1a1a1a; color: #d4af37; border: 2px solid #d4af37; padding: 15px; border-radius: 6px; font-size: 16px; font-weight: bold; margin-top: 25px; cursor: pointer; transition: 0.3s; }}
            button:hover {{ background-color: #d4af37; color: #1a1a1a; }}
            .badge-info {{ background: #f4f4f4; padding: 10px; border-radius: 6px; font-size: 13px; color: #666; margin-top: 5px; border-left: 3px solid #d4af37; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>CENTRO AUTO SOFISTICAR</h1>
            <div class="slogan">Qualidade e Confiança para o seu Carro!</div>
            {mensagem_sucesso}
            <form action="/agendar" method="post">
                <label for="cliente">Nome Completo:</label>
                <input type="text" id="cliente" name="cliente" required placeholder="Ex: João Silva">

                <label for="contacto">Telefone / Telemóvel:</label>
                <input type="tel" id="contacto" name="contacto" required placeholder="Ex: 912345678">

                <label for="matricula">Matrícula da Viatura:</label>
                <input type="text" id="matricula" name="matricula" required placeholder="Ex: AA-00-AA">

                <label for="servico">Serviço Pretendido:</label>
                <select id="servico" name="servico" required>
                    {opcoes_servicos}
                </select>
                <div class="badge-info">ℹ️ Os valores são sob consulta e avaliação prévia da viatura nas nossas instalações.</div>

                <label for="data">Data Pretendida:</label>
                <input type="date" id="data" name="data" required>

                <label for="hora">Hora Pretendida:</label>
                <input type="time" id="hora" name="hora" required>

                <label for="observacoes">Observações (opcional):</label>
                <textarea id="observacoes" name="observacoes" rows="3" placeholder="Ex: Detalhes sobre lavagem, polimento ou avaria..."></textarea>

                <button type="submit">MARCAR AGENDAMENTO</button>
            </form>
        </div>
    </body>
    </html>
    """
    return html

# 📩 PROCESSAR AGENDAMENTO (Grava na Base de Dados)
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
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO agendamentos (cliente, contacto, matricula, servico, data, hora, observacoes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (cliente, contacto, matricula, servico, data, hora, observacoes))
    conn.commit()
    conn.close()
    
    return RedirectResponse(url="/cliente?sucesso=True", status_code=303)

# 📊 PAINEL DA OFICINA (Com Login / PIN de Segurança)
@app.get("/painel", response_class=HTMLResponse)
def pagina_painel(pin: str = ""):
    # Se o PIN estiver incorreto ou não for preenchido, mostra formulário de login
    if pin != PIN_ACESSO:
        erro_html = '<p style="color: red; text-align: center;">❌ PIN Incorreto!</p>' if pin else ''
        return f"""
        <!DOCTYPE html>
        <html lang="pt">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Acesso Restrito - Centro Auto Sofisticar</title>
            <style>
                body {{ font-family: sans-serif; background-color: #1a1a1a; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
                .login-card {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); width: 300px; border-top: 5px solid #d4af37; }}
                h3 {{ text-align: center; color: #1a1a1a; margin-top: 0; }}
                input {{ width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ccc; border-radius: 5px; box-sizing: border-box; text-align: center; font-size: 18px; letter-spacing: 4px; }}
                button {{ width: 100%; background: #1a1a1a; color: #d4af37; padding: 12px; border: 1px solid #d4af37; border-radius: 5px; font-size: 16px; font-weight: bold; cursor: pointer; }}
                button:hover {{ background: #d4af37; color: #1a1a1a; }}
            </style>
        </head>
        <body>
            <div class="login-card">
                <h3>🛠️ Área do Gestor</h3>
                {erro_html}
                <form action="/painel" method="get">
                    <input type="password" name="pin" placeholder="Introduza o PIN" required autofocus>
                    <button type="submit">ENTRAR</button>
                </form>
            </div>
        </body>
        </html>
        """

    # Se o PIN estiver correto, lê da Base de Dados
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, cliente, contacto, matricula, servico, data, hora, observacoes, estado FROM agendamentos ORDER BY id DESC")
    registos = cursor.fetchall()
    conn.close()

    linhas_tabela = ""
    for item in registos:
        id_item, cliente, contacto, matricula, servico, data, hora, observacoes, estado = item
        cor_badge = "#ffc107" if estado == "Pendente" else "#28a745"
        
        estilo_linha = ""
        if "Lavagens" in servico:
            estilo_linha = "background-color: #e3f2fd;"
        elif "Polimento" in servico:
            estilo_linha = "background-color: #f3e5f5;"
        elif "Elétrica" in servico or "Ar Condicionado" in servico:
            estilo_linha = "background-color: #fffde7;"

        linhas_tabela += f"""
        <tr style="{estilo_linha}">
            <td>#{id_item}</td>
            <td><b>{cliente}</b><br><small>{contacto}</small></td>
            <td><span style="background: #333; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold;">{matricula}</span></td>
            <td><b>{servico}</b></td>
            <td>{data} às {hora}</td>
            <td><i>{observacoes or '-'}</i></td>
            <td><span style="background-color: {cor_badge}; color: black; padding: 5px 10px; border-radius: 12px; font-weight: bold; font-size: 12px;">{estado}</span></td>
        </tr>
        """

    html = f"""
    <!DOCTYPE html>
    <html lang="pt">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Painel - Centro Auto Sofisticar</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8f9fa; margin: 0; padding: 20px; }}
            .header {{ display: flex; justify-content: space-between; align-items: center; background: #1a1a1a; color: white; padding: 15px 25px; border-radius: 8px; margin-bottom: 20px; border-bottom: 4px solid #d4af37; }}
            table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }}
            th, td {{ padding: 14px 15px; text-align: left; border-bottom: 1px solid #dee2e6; }}
            th {{ background-color: #e9ecef; color: #495057; }}
            tr:hover {{ filter: brightness(0.97); }}
        </style>
    </head>
    <body>
        <div class="header">
            <h2>🛠️ Painel de Gestão - Centro Auto Sofisticar</h2>
            <span>Agendamentos Totais: <b>{len(registos)}</b></span>
        </div>
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Cliente</th>
                    <th>Matrícula</th>
                    <th>Área / Serviço Solicitado</th>
                    <th>Data & Hora</th>
                    <th>Observações</th>
                    <th>Estado</th>
                </tr>
            </thead>
            <tbody>
                {linhas_tabela if linhas_tabela else '<tr><td colspan="7" style="text-align:center;">Nenhum agendamento registado até ao momento.</td></tr>'}
            </tbody>
        </table>
    </body>
    </html>
    """
    return html
