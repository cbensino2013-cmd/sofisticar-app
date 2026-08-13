from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, Response
import sqlite3
import os
import io
import csv
from datetime import datetime, timedelta

app = FastAPI(title="Centro Auto Sofisticar - Gestão Completa")
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
            hora TEXT NOT NULL,
            estado TEXT DEFAULT 'Pendente',
            observacoes TEXT,
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
            criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_db()

# Função de semáforo para o Painel
def get_status_emoji(criado_em_str, estado):
    if estado != "Pendente": return "✅ Concluído"
    try:
        dt = datetime.strptime(criado_em_str, '%Y-%m-%d %H:%M:%S')
        dif = datetime.now() - dt
    except:
        return "🟢 Em Prazo"
    
    if dif < timedelta(hours=1): return "🟢 Em Prazo"
    if dif < timedelta(hours=2): return "🟡 Atenção (1h+)"
    if dif < timedelta(hours=3): return "🟠 Alerta (2h+)"
    return "🔴 Crítico (3h+)"

# 🌐 PÁGINA DE CRIAÇÃO DE ORÇAMENTOS COM TODAS AS PEÇAS
@app.get("/novo_orcamento", response_class=HTMLResponse)
def form_orcamento(pin: str = ""):
    if pin != PIN_ACESSO:
        return "<body style='background:#121212; color:#fff; font-family:sans-serif; text-align:center; padding-top:50px;'><h3>Acesso restrito. Insira o PIN correto no link (ex: /novo_orcamento?pin=1234)</h3></body>"

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
        <title>Criar Orçamento Detalhado</title>
        <style>
            body {{ font-family: 'Segoe UI', sans-serif; background: #121212; color: #fff; padding: 20px; }}
            .container {{ max-width: 750px; margin: auto; background: #181818; padding: 30px; border-radius: 12px; border-top: 5px solid #d4af37; }}
            input[type="text"], textarea {{ width: 100%; padding: 10px; background: #2a2a2a; border: 1px solid #555; border-radius: 6px; color: #fff; margin-bottom: 15px; box-sizing: border-box; }}
            button {{ background: #d4af37; color: #121212; border: none; padding: 12px 20px; font-weight: bold; border-radius: 6px; cursor: pointer; width: 100%; font-size: 16px; }}
            button:hover {{ background: #b8972f; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>🛠️ Criar Orçamento Personalizado</h2>
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

    # Calcular o subtotal somando os preços reais do catálogo
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

# 📄 VISUALIZAR / IMPRIMIR ORÇAMENTO EM PDF
@app.get("/orcamento", response_class=HTMLResponse)
def ver_orcamento(id: int):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, titulo, cliente, matricula, pecas, descricao, subtotal, iva, total, criado_em FROM orcamentos WHERE id = ?", (id,))
    reg = cursor.fetchone()
    conn.close()

    if not reg: return "<h3>Orçamento não encontrado.</h3>"
    id_o, titulo, cli, mat, pecas, desc, sub, iva, total, criado = reg

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
        <h1>CENTRO AUTO SOFISTICAR</h1>
        <div class="sub">Proposta de Orçamento Automóvel Nº {id_o} — {titulo}</div>
        
        <div class="box">
            <div class="field"><label>Cliente:</label> {cli}</div>
            <div class="field"><label>Viatura / Matrícula:</label> <b>{mat}</b></div>
            <div class="field"><label>Data:</label> {criado}</div>
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
