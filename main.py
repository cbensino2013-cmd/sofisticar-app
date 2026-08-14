from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse

app = FastAPI(title="Centro Auto Sofisticar - Completo")

# PIN Secreto da Empresa (Podes alterar aqui para a tua senha privada)
PIN_ADMIN = "1234"

# Base de dados em memória
agendamentos = [
    {
        "id": 1,
        "cliente": "João Silva",
        "contacto": "912345678",
        "matricula": "AA-00-AA",
        "servico": "Lavagens - Lavagem Completa",
        "data": "2026-08-15",
        "hora": "10:00",
        "estado": "Pendente",
        "observacoes": "Limpeza interior e exterior"
    }
]

SERVICOS = [
    {"id": "mecanica", "nome": "Mecânica Geral / Manutenção", "preco": "Sob Consulta / Análise"},
    {"id": "eletrica", "nome": "Elétrica Auto & Diagnóstico", "preco": "Sob Consulta / Análise"},
    {"id": "ac", "nome": "Ar Condicionado (Carga e Manutenção)", "preco": "Sob Consulta / Análise"},
    {"id": "polimento", "nome": "Polimento e Detalhe Automóvel", "preco": "Sob Consulta / Análise"},
    {"id": "lavagem_simples", "nome": "Lavagens - Exterior", "preco": "Sob Consulta / Análise"},
    {"id": "lavagem_completa", "nome": "Lavagens - Completa (Interior + Exterior)", "preco": "Sob Consulta / Análise"},
    {"id": "higienizacao", "nome": "Lavagens - Higienização de Estofos", "preco": "Sob Consulta / Análise"},
]

def get_css():
    return """
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #1a1a1a; margin: 0; padding: 20px; color: #333; }
        .container { max-width: 700px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 25px rgba(0,0,0,0.4); border-top: 6px solid #d4af37; margin-bottom: 30px; }
        h1 { color: #1a1a1a; text-align: center; margin-bottom: 2px; font-size: 26px; text-transform: uppercase; letter-spacing: 1px; }
        .slogan { text-align: center; color: #d4af37; font-weight: bold; margin-top: 0; font-size: 14px; margin-bottom: 20px; text-transform: uppercase; }
        label { font-weight: bold; display: block; margin-top: 15px; margin-bottom: 5px; color: #444; }
        input, select, textarea { width: 100%; padding: 12px; border: 1px solid #ccc; border-radius: 6px; box-sizing: border-box; font-size: 15px; }
        button { width: 100%; background-color: #1a1a1a; color: #d4af37; border: 2px solid #d4af37; padding: 15px; border-radius: 6px; font-size: 16px; font-weight: bold; margin-top: 25px; cursor: pointer; transition: 0.3s; }
        button:hover { background-color: #d4af37; color: #1a1a1a; }
        .badge-info { background: #f4f4f4; padding: 10px; border-radius: 6px; font-size: 13px; color: #666; margin-top: 5px; border-left: 3px solid #d4af37; }
        .search-box { background: #f9f9f9; padding: 20px; border-radius: 8px; border: 1px solid #ddd; margin-bottom: 25px; }
        .btn-voltar { display: inline-block; background: #1a1a1a; color: #d4af37; padding: 10px 20px; text-decoration: none; border-radius: 6px; font-weight: bold; margin-bottom: 20px; border: 1px solid #d4af37; }
        
        .painel-body { background-color: #f8f9fa; }
        .painel-container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 25px rgba(0,0,0,0.1); }
        .header-painel { display: flex; justify-content: space-between; align-items: center; background: #1a1a1a; color: white; padding: 15px 25px; border-radius: 8px; margin-bottom: 25px; border-bottom: 4px solid #d4af37; }
        table { width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; }
        th, td { padding: 14px 15px; text-align: left; border-bottom: 1px solid #dee2e6; }
        th { background-color: #e9ecef; color: #495057; }
        .btn { padding: 6px 12px; border-radius: 4px; text-decoration: none; font-weight: bold; font-size: 12px; color: white; display: inline-block; margin-right: 5px; }
        .btn-iniciar { background-color: #007bff; }
        .btn-concluir { background-color: #28a745; }
        .btn-wpp { background-color: #25d366; display: inline-block; margin-top: 5px; }
    </style>
    """

@app.get("/", response_class=HTMLResponse)
def inicio():
    return RedirectResponse(url="/cliente")

# 📱 PORTAL DO CLIENTE
@app.get("/cliente", response_class=HTMLResponse)
def pagina_cliente(sucesso: bool = False, erro: str = None):
    opcoes_servicos = "".join(
        f'<option value="{s["nome"]}">{s["nome"]} — [{s["preco"]}]</option>' for s in SERVICOS
    )
    
    mensagem_alerta = ""
    if sucesso:
        mensagem_alerta = '<div style="background-color: #d4edda; color: #155724; padding: 15px; border-radius: 8px; margin-bottom: 20px; text-align: center; font-weight: bold;">✅ Agendamento enviado com sucesso!</div>'
    elif erro:
        mensagem_alerta = f'<div style="background-color: #f8d7da; color: #721c24; padding: 15px; border-radius: 8px; margin-bottom: 20px; text-align: center; font-weight: bold;">❌ {erro}</div>'

    return f"""
    <!DOCTYPE html>
    <html lang="pt">
    <head>
        <meta charset="UTF-8">
        <title>Centro Auto Sofisticar - Portal do Cliente</title>
        {get_css()}
    </head>
    <body>
        <div class="container">
            <h1>CENTRO AUTO SOFISTICAR</h1>
            <div class="slogan">Portal Oficial do Cliente</div>
            
            <div class="search-box">
                <h3 style="margin-top:0; color:#1a1a1a; font-size:16px;">🔍 Consultar o Estado da minha Viatura</h3>
                <form action="/consultar_cliente" method="get" style="display:flex; gap:10px;">
                    <input type="text" name="matricula" placeholder="Insira a matrícula (ex: AA-00-AA)" required style="margin:0; text-transform:uppercase;">
                    <button type="submit" style="margin:0; width:140px; padding:10px; font-size:14px;">Consultar</button>
                </form>
            </div>

            {mensagem_alerta}
            
            <h3 style="border-bottom: 2px solid #d4af37; padding-bottom: 8px; color:#1a1a1a;">📅 Marcar Novo Serviço</h3>
            <form action="/agendar" method="post">
                <label for="cliente">Nome Completo:</label>
                <input type="text" id="cliente" name="cliente" required placeholder="Ex: João Silva">

                <label for="contacto">Telefone / Telemóvel:</label>
                <input type="tel" id="contacto" name="contacto" required placeholder="Ex: 912345678">

                <label for="matricula">Matrícula da Viatura:</label>
                <input type="text" id="matricula" name="matricula" required placeholder="Ex: AA-00-AA" style="text-transform:uppercase;">

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

# 🔍 CONSULTAR ESTADO POR MATRÍCULA
@app.get("/consultar_cliente", response_class=HTMLResponse)
def consultar_cliente(matricula: str):
    matricula_limpa = matricula.strip().upper()
    resultados = [item for item in agendamentos if item["matricula"].upper() == matricula_limpa]
    
    linhas = ""
    if resultados:
        for r in resultados:
            cor_badge = "#ffc107" if r["estado"] == "Pendente" else ("#007bff" if r["estado"] == "Em Serviço" else "#28a745")
            linhas += f"""
            <tr style="border-bottom: 1px solid #ddd;">
                <td style="padding:12px;"><b>{r['servico']}</b></td>
                <td style="padding:12px;">{r['data']} às {r['hora']}</td>
                <td style="padding:12px;"><i>{r['observacoes'] or 'Nenhuma'}</i></td>
                <td style="padding:12px;"><span style="background-color: {cor_badge}; color: {'black' if r['estado']=='Pendente' else 'white'}; padding: 4px 10px; border-radius: 12px; font-weight: bold; font-size: 12px;">{r['estado']}</span></td>
            </tr>
            """
    else:
        linhas = '<tr><td colspan="4" style="padding:20px; text-align:center; color:#666;">Nenhum agendamento encontrado para esta matrícula.</td></tr>'

    return f"""
    <!DOCTYPE html>
    <html lang="pt">
    <head>
        <meta charset="UTF-8">
        <title>Resultados - Centro Auto Sofisticar</title>
        {get_css()}
    </head>
    <body>
        <div class="container">
            <a href="/cliente" class="btn-voltar">← Voltar ao Portal</a>
            <h2>Resultados para a Matrícula: <span style="color:#d4af37;">{matricula_limpa}</span></h2>
            <table>
                <tr><th>Serviço</th><th>Data & Hora</th><th>Observações</th><th>Estado Atual</th></tr>
                {linhas}
            </table>
        </div>
    </body>
    </html>
    """

# 📩 PROCESSAR AGENDAMENTO
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
    matricula_Formatada = matricula.strip().upper()
    
    for item in agendamentos:
        if item["data"] == data and item["hora"] == hora and item["estado"] != "Cancelado":
            return RedirectResponse(
                url=f"/cliente?erro=O horário {hora} do dia {data} já se encontra ocupado. Por favor, escolha outra hora.", 
                status_code=303
            )

    novo_id = len(agendamentos) + 1
    agendamentos.append({
        "id": novo_id,
        "cliente": cliente,
        "contacto": contacto,
        "matricula": matricula_Formatada,
        "servico": servico,
        "data": data,
        "hora": hora,
        "estado": "Pendente",
        "observacoes": observacoes
    })
    return RedirectResponse(url="/cliente?sucesso=True", status_code=303)

# 📊 PAINEL DE GESTÃO DA EMPRESA (PROTEGIDO POR PIN)
@app.get("/painel", response_class=HTMLResponse)
def pagina_painel(pin: str = ""):
    if pin != PIN_ADMIN:
        return """
        <!DOCTYPE html>
        <html lang="pt">
        <head>
            <meta charset="UTF-8">
            <title>Acesso Negado - Centro Auto Sofisticar</title>
            <style>
                body { font-family: 'Segoe UI', sans-serif; background: #1a1a1a; color: white; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
                .box { background: white; color: #333; padding: 40px; border-radius: 12px; text-align: center; box-shadow: 0 4px 25px rgba(0,0,0,0.5); border-top: 6px solid #d4af37; max-width: 400px; width: 100%; }
                input { width: 100%; padding: 12px; margin: 15px 0; border: 1px solid #ccc; border-radius: 6px; box-sizing: border-box; font-size: 16px; }
                button { background: #1a1a1a; color: #d4af37; border: 2px solid #d4af37; padding: 12px; width: 100%; border-radius: 6px; font-weight: bold; cursor: pointer; font-size: 16px; }
                button:hover { background: #d4af37; color: #1a1a1a; }
            </style>
        </head>
        <body>
            <div class="box">
                <h2 style="color:#1a1a1a; margin-top:0;">🔒 Área Restrita</h2>
                <p style="color:#666; font-size:14px;">Introduza o PIN de acesso da oficina para visualizar o painel de gestão.</p>
                <form action="/painel" method="get">
                    <input type="password" name="pin" placeholder="PIN Secreto" required autofocus>
                    <button type="submit">Entrar no Painel</button>
                </form>
            </div>
        </body>
        </html>
        """

    linhas_tabela = ""
    for item in reversed(agendamentos):
        cor_badge = "#ffc107" if item["estado"] == "Pendente" else ("#007bff" if item["estado"] == "Em Serviço" else "#28a745")
        
        estilo_linha = ""
        if "Lavagens" in item["servico"]:
            estilo_linha = "background-color: #f1f8ff;"
        elif "Polimento" in item["servico"]:
            estilo_linha = "background-color: #faf5fb;"

        # Geração do link dinâmico para o WhatsApp com indicativo de Portugal (351)
        msg_wpp = f"Olá {item['cliente']}! Confirmamos o agendamento da viatura {item['matricula']} para o serviço '{item['servico']}' no dia {item['data']} às {item['hora']}."
        link_wpp = f"https://wa.me/351{item['contacto']}?text={msg_wpp.replace(' ', '%20')}"

        linhas_tabela += f"""
        <tr style="{estilo_linha}">
            <td>#{item['id']}</td>
            <td><b>{item['cliente']}</b><br><small>{item['contacto']}</small></td>
            <td><span style="background: #333; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold;">{item['matricula']}</span></td>
            <td><b>{item['servico']}</b></td>
            <td>{item['data']} às {item['hora']}</td>
            <td><i>{item['observacoes'] or '-'}</i></td>
            <td><span style="background-color: {cor_badge}; color: {'black' if item['estado']=='Pendente' else 'white'}; padding: 5px 10px; border-radius: 12px; font-weight: bold; font-size: 12px;">{item['estado']}</span></td>
            <td>
                <a href="/alterar_estado?id={item['id']}&estado=Em Serviço&pin={PIN_ADMIN}" class="btn btn-iniciar">Iniciar</a>
                <a href="/alterar_estado?id={item['id']}&estado=Concluído&pin={PIN_ADMIN}" class="btn btn-concluir">Concluir</a><br>
                <a href="{link_wpp}" target="_blank" class="btn btn-wpp">📲 WhatsApp</a>
            </td>
        </tr>
        """

    return f"""
    <!DOCTYPE html>
    <html lang="pt">
    <head>
        <meta charset="UTF-8">
        <title>Painel - Centro Auto Sofisticar</title>
        {get_css()}
    </head>
    <body class="painel-body">
        <div class="painel-container">
            <div class="header-painel">
                <h2>🛠️ Painel de Gestão - Centro Auto Sofisticar</h2>
                <span>Agendamentos Totais: <b>{len(agendamentos)}</b></span>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Cliente</th>
                        <th>Matrícula</th>
                        <th>Serviço Solicitado</th>
                        <th>Data & Hora</th>
                        <th>Observações</th>
                        <th>Estado</th>
                        <th>Ações</th>
                    </tr>
                </thead>
                <tbody>
                    {linhas_tabela}
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """

# ⚙️ ROTA PARA MUDAR O ESTADO NO PAINEL (Protegida por PIN)
@app.get("/alterar_estado")
def alterar_estado(id: int, estado: str, pin: str = ""):
    if pin != PIN_ADMIN:
        return RedirectResponse(url="/painel", status_code=303)
        
    for item in agendamentos:
        if item["id"] == id:
            item["estado"] = estado
    return RedirectResponse(url=f"/painel?pin={PIN_ADMIN}", status_code=303)
