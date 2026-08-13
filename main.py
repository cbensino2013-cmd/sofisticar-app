from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
import sqlite3
import os
from datetime import datetime, timedelta

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
def index(pin: str = ""):
    return f"""
    <!DOCTYPE html>
    <html lang="pt">
    <head>
        <meta charset="UTF-8">
        <title>Centro Auto Sofisticar</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #121212; color: #fff; text-align: center; padding-top: 100px; }}
            .card {{ background: #181818; max-width: 500px; margin: auto; padding: 40px; border-radius: 12px; border-top: 5px solid #d4af37; box-shadow: 0 8px 20px rgba(0,0,0,0.5); }}
            h1 {{ color: #d4af37; margin-bottom: 10px; }}
            p {{ color: #aaa; margin-bottom: 30px; }}
            a {{ display: inline-block; background: #d4af37; color: #121212; padding: 12px 25px; text-decoration: none; font-weight: bold; border-radius: 6px; transition: 0.3s; }}
            a:hover {{ background: #b8972f; }}
        </style>
    </head>
    <body>
        <div class="card">
            <div style="font-size: 50px; margin-bottom: 15px;">🏎️</div>
            <h1>Centro Auto Sofisticar</h1>
            <p>Sistema Profissional de Gestão e Orçamentos</p>
            <a href="/painel?pin={PIN_ACESSO}">Aceder ao Painel de Gestão</a>
        </div>
    </body>
    </html>
    """

@app.get("/painel", response_class=HTMLResponse)
def painel(pin: str = ""):
    if pin != PIN_ACESSO:
        return """
        <body style="background:#121212; color:#fff; font-family:sans-serif; text-align:center; padding-top:100px;">
            <div style="background:#181818; max-width:400px; margin:auto; padding:30px; border-radius:10px; border:1px solid #333;">
                <h3 style="color:#ff4d4d;">Acesso Restrito</h3>
                <p>PIN incorreto ou em falta. Use o link com ?pin=O_TEU_PIN</p>
            </div>
        </body>
        """
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, titulo, cliente, matricula, total, estado, criado_em FROM orcamentos ORDER BY id DESC")
    orcamentos = cursor.fetchall()
    conn.close()

    linhas_orc = ""
    for r in orcamentos:
        id_o, titulo, cli, mat, total, est, criado = r
        
        # Cor do estado
        cor_est = "#f0ad4e" if est == "Pendente" else ("#28a745" if est == "Aprovado" else "#d9534f")
        
        # Mensagem WhatsApp formatada
        msg_wa = f"Olá {cli}, o seu orçamento '{titulo}' na Centro Auto Sofisticar (Viatura: {mat}) tem o valor total de {total:.2f}€. Aguardamos a sua confirmação."
        link_wa = f"https://wa.me/?text={msg_wa.replace(' ', '%20')}"

        linhas_orc += f"""
        <tr style="border-bottom:1px solid #333; background: #1a1a1a;">
            <td style="padding:15px; font-weight:bold; color:#d4af37;">#{id_o}</td>
            <td style="padding:15px;"><b>{cli}</b><br><small style="color:#aaa;">{mat}</small></td>
            <td style="padding:15px;">{titulo}</td>
            <td style="padding:15px; font-weight:bold; color:#28a745; font-size:16px;">{total:.2f} €</td>
            <td style="padding:15px;">
                <select onchange="window.location.href='/mudar_estado?id={id_o}&estado='+this.value+'&pin={pin}'" style="background:#2a2a2a; color:#fff; padding:6px; border-radius:4px; border:1px solid #555; font-weight:bold; color:{cor_est}; cursor:pointer;">
                    <option value="Pendente" {'selected' if est == 'Pendente' else ''}>🟡 Pendente</option>
                    <option value="Aprovado" {'selected' if est == 'Aprovado' else ''}>🟢 Aprovado</option>
                    <option value="Recusado" {'selected' if est == 'Recusado' else ''}>🔴 Recusado</option>
                </select>
            </td>
            <td style="padding:15px;">
                <a href="/orcamento?id={id_o}" target="_blank" style="background:#333; color:#d4af37; padding:6px 10px; text-decoration:none; border-radius:4px; font-size:13px; margin-right:5px;">📄 PDF</a>
                <a href="{link_wa}" target="_blank" style="background:#25D366; color:#fff; padding:6px 10px; text-decoration:none; border-radius:4px; font-size:13px; font-weight:bold; margin-right:5px;">📲 WhatsApp</a>
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
            .mascot-area {{ display: flex; align-items: center; }}
            .content {{ padding: 30px; max-width: 1200px; margin: auto; }}
            .btn-new {{ background: #d4af37; color: #121212; padding: 12px 20px; text-decoration: none; font-weight: bold; border-radius: 6px; box-shadow: 0 4px 10px rgba(212,175,55,0.3); }}
            .btn-new:hover {{ background: #b8972f; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; background: #181818; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.4); }}
            th {{ background: #222; color: #d4af37; padding: 15px; text-align: left; font-size: 14px; border-bottom: 2px solid #333; }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="mascot-area">
                <span style="font-size: 45px; margin-right: 20px;">🏎️</span>
                <div>
                    <h1 style="margin:0; font-size: 24px; color:#fff;">Centro Auto Sofisticar</h1>
                    <p style="margin:0; color:#d4af37; font-size: 13px;">Painel de Controlo & Performance</p>
                </div>
            </div>
            <div>
                <a href="/novo_orcamento?pin={pin}" class="btn-new">＋ Criar Novo Orçamento</a>
            </div>
        </div>

        <div class="content">
            <h2 style="color:#fff; margin-bottom: 20px;">📋 Orçamentos Registados</h2>
            <table>
                <tr>
                    <th>ID</th>
                    <th>Cliente / Matrícula</th>
                    <th>Título / Avaria</th>
                    <th>Total (c/ IVA)</th>
                    <th>Estado</th>
                    <th>Ações Rápidas</th>
                </tr>
                {linhas_orc if linhas_orc else '<tr><td colspan="6" style="text-align:center; padding:30px; color:#777;">Nenhum orçamento registado de momento.</td></tr>'}
            </table>
        </div>
    </body>
    </html>
    """

@app.get("/novo_orcamento", response_class=HTMLResponse)
def form_orcamento(pin: str = ""):
    if pin != PIN_ACESSO:
        return "<body style='background:#121212; color:#fff; font-family:sans-serif; text-align:center; padding-top:50px;'><h3>Acesso restrito. Insira o PIN correto.</h3></body>"

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
                <input type="text" name="titulo" placeholder="Ex: Avaria no Sistema de Temperatura / Substituição de Radiador" required>

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

                <label><b>Descrição / Notas Adicionais para o Mecânico:</b></label>
                <textarea name="descricao" rows="3" placeholder="Ex: Tubagens secundárias também aparentam desgaste, verificar no ato da montagem..."></textarea>

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

@app.post("/apagar_orcamento")
def apagar_orcamento(id_orcamento: int = Form(...), pin: str = Form(...)):
    if pin == PIN_ACESSO:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM orcamentos WHERE id = ?", (id_orcamento,))
        conn.commit()
        conn.close()
    return RedirectResponse(url=f"/painel?pin={pin}", status_code=303)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
