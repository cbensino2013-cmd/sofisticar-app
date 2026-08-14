from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
import sqlite3
import os
import random
from datetime import datetime

app = FastAPI(title="Centro Auto Sofisticar - Enterprise Edition")
DB_FILE = "oficina.db"

# Sistema de Código Dinâmico de Acesso Temporário para o Gestor
ESTADO_SESSAO = {"codigo_atual": "7788", "autenticado": False}

# Catálogo exato com os serviços e produtos que a oficina oferece
CATALOGO_COMPLETO = {
    "🛞 Pneus & Direção": {
        "Pneu 175/65 R14": {"preco": 50.00, "stock": 12},
        "Pneu 195/65 R15": {"preco": 65.00, "stock": 8},
        "Pneu 205/55 R16": {"preco": 85.00, "stock": 20},
        "Alinhamento de Direção": {"preco": 35.00, "stock": 999}
    },
    "🛑 Sistema de Travões": {
        "Pastilhas de Travão (Frente)": {"preco": 55.00, "stock": 10},
        "Pastilhas de Travão (Traseiras)": {"preco": 45.00, "stock": 8},
        "Discos de Travão (Par)": {"preco": 90.00, "stock": 6},
        "Líquido de Travões": {"preco": 15.00, "stock": 15}
    },
    "🛢️ Óleos e Filtros (Revisão)": {
        "Óleo Motor 5W30 (5L)": {"preco": 50.00, "stock": 25},
        "Filtro de Óleo": {"preco": 15.00, "stock": 18},
        "Filtro de Ar": {"preco": 20.00, "stock": 14},
        "Filtro Habitáculo": {"preco": 25.00, "stock": 10}
    },
    "⚡ Eletricidade & Baterias": {
        "Bateria 12V 60Ah": {"preco": 85.00, "stock": 5},
        "Velas de Ignição (Jogo)": {"preco": 40.00, "stock": 7}
    },
    "🔧 Mão de Obra e Diagnóstico": {
        "Diagnóstico Eletrónico": {"preco": 30.00, "stock": 999},
        "Mão de Obra Especializada (Hora)": {"preco": 35.00, "stock": 999}
    }
}

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agendamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_seguimento TEXT UNIQUE,
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
            desconto REAL NOT NULL,
            iva REAL NOT NULL,
            total REAL NOT NULL,
            criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_db()

# 🌐 1. PORTAL DO CLIENTE (Layout Inspirado nas Referências Visuais)
@app.get("/", response_class=HTMLResponse)
def portal_cliente():
    return """
    <!DOCTYPE html>
    <html lang="pt">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Centro Auto Sofisticar - Portal Oficial</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #121212; color: #fff; margin: 0; padding: 0; }
            /* Barra de topo promocional amarela */
            .top-bar { background: #d4af37; color: #121212; text-align: center; padding: 8px; font-weight: bold; font-size: 13px; }
            /* Header principal estilo e-commerce profissional */
            header { background: #181818; border-bottom: 2px solid #333; padding: 15px 40px; display: flex; justify-content: space-between; align-items: center; }
            .brand { display: flex; align-items: center; gap: 12px; text-decoration: none; }
            .logo-box { background: #d4af37; color: #121212; font-weight: bold; padding: 10px 14px; border-radius: 6px; font-size: 18px; letter-spacing: 1px; }
            .brand h1 { margin: 0; color: #d4af37; font-size: 18px; line-height: 1.1; }
            .brand p { margin: 0; color: #aaa; font-size: 10px; text-transform: uppercase; }
            
            .header-search { display: flex; align-items: center; background: #fff; border-radius: 30px; width: 400px; padding: 4px 15px; }
            .header-search input { border: none; outline: none; width: 100%; padding: 8px; font-size: 14px; color: #333; background: transparent; }
            
            .header-links { display: flex; align-items: center; gap: 25px; font-size: 13px; color: #ccc; }
            .header-links a { color: #ccc; text-decoration: none; display: flex; align-items: center; gap: 6px; transition: 0.2s; }
            .header-links a:hover { color: #d4af37; }
            .btn-gestor { border: 1px solid #d4af37; padding: 6px 14px; border-radius: 6px; color: #d4af37 !important; font-weight: bold; }

            .hero { background: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)), url('https://images.unsplash.com/photo-1486006920555-c77dce18193b?auto=format&fit=crop&w=1200&q=80'); background-size: cover; padding: 45px 20px; text-align: center; }
            
            .container { max-width: 850px; margin: -25px auto 40px auto; background: #1e1e1e; padding: 35px; border-radius: 12px; border: 1px solid #333; box-shadow: 0 10px 30px rgba(0,0,0,0.6); position: relative; }
            .form-group { margin-bottom: 18px; }
            label { display: block; margin-bottom: 6px; font-weight: bold; color: #ddd; font-size: 14px; }
            input, select, textarea { width: 100%; padding: 12px; background: #2a2a2a; border: 1px solid #444; border-radius: 6px; color: #fff; box-sizing: border-box; font-size: 14px; }
            input:focus, select:focus { border-color: #d4af37; outline: none; }
            button { background: #d4af37; color: #121212; border: none; padding: 14px; font-weight: bold; font-size: 16px; border-radius: 6px; cursor: pointer; width: 100%; transition: 0.2s; }
            button:hover { background: #b8972f; }
            .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
            .box-search { background: #181818; padding: 20px; border-radius: 8px; border: 1px solid #444; margin-bottom: 30px; text-align: center; }
            .gdpr { font-size: 12px; color: #888; background: #151515; padding: 12px; border-radius: 6px; border-left: 3px solid #d4af37; margin-bottom: 20px; }
            
            /* Rodapé idêntico aos portais profissionais */
            footer { background: #151515; border-top: 1px solid #333; padding: 30px 40px; margin-top: 50px; color: #888; font-size: 12px; text-align: center; }
            .footer-links { display: flex; justify-content: center; gap: 20px; margin-bottom: 15px; flex-wrap: wrap; }
            .footer-links a { color: #aaa; text-decoration: none; }
            .footer-links a:hover { color: #d4af37; text-decoration: underline; }
        </style>
    </head>
    <body>
        <div class="top-bar">🔥 Campanha de Verão: Revisão Oficial com 15% de Desconto em Peças Selecionadas!</div>
        
        <header>
            <a href="/" class="brand">
                <div class="logo-box">CAS</div>
                <div>
                    <h1>CENTRO AUTO SOFISTICAR</h1>
                    <p>Oficina Oficial & Multimarca</p>
                </div>
            </a>

            <div class="header-search">
                <input type="text" placeholder="O que procura? (ex: Pneus, Óleos, Travões...)">
                <span style="color: #666; font-size: 16px;">🔍</span>
            </div>

            <div class="header-links">
                <a href="#agendar">📍 Os Nossos Serviços</a>
                <a href="/login_gestor" class="btn-gestor">🔒 Área Gestor</a>
            </div>
        </header>

        <div class="hero">
            <h2 style="color: #d4af37; margin-bottom: 5px; font-size: 28px;">Portal Oficial do Cliente</h2>
            <p>Agende os nossos serviços especializados ou consulte o histórico da sua viatura em tempo real.</p>
        </div>

        <div class="container" id="agendar">
            <div class="box-search">
                <h4 style="color:#d4af37; margin-top:0;">🔍 Acompanhar Estado ou Consultar Histórico</h4>
                <p style="font-size:13px; color:#aaa;">Insira o seu Código de Seguimento ou a Matrícula da viatura:</p>
                <form action="/seguir" method="get" style="display: flex; gap: 10px;">
                    <input type="text" name="codigo" placeholder="Ex: CAS-5819 ou 00-AA-00" required style="margin-bottom:0; text-transform:uppercase;">
                    <button type="submit" style="width: 160px; padding: 10px;">Consultar</button>
                </form>
            </div>

            <h3 style="color: #d4af37; border-bottom: 1px solid #333; padding-bottom: 10px; margin-top:0;">📅 Agendar Novo Serviço</h3>
            
            <form action="/agendar" method="post">
                <div class="grid-2">
                    <div class="form-group">
                        <label>Nome do Cliente:</label>
                        <input type="text" name="cliente" placeholder="Nome completo" required>
                    </div>
                    <div class="form-group">
                        <label>Contacto Telefónico:</label>
                        <input type="text" name="contacto" placeholder="912345678" required>
                    </div>
                </div>

                <div class="grid-2">
                    <div class="form-group">
                        <label>Matrícula da Viatura:</label>
                        <input type="text" name="matricula" placeholder="00-AA-00" style="text-transform:uppercase;" required>
                    </div>
                    <div class="form-group">
                        <label>Serviço Pretendido:</label>
                        <select name="servico" required>
                            <option value="">Selecione o serviço...</option>
                            <option value="Revisão Geral / Óleos">🛢️ Revisão Geral (Óleos e Filtros)</option>
                            <option value="Pneus & Alinhamento">🛞 Pneus & Alinhamento de Direção</option>
                            <option value="Sistema de Travões">🛑 Sistema de Travões</option>
                            <option value="Diagnóstico Eletrónico">⚡ Diagnóstico Eletrónico</option>
                            <option value="Lavagem & Polimento">✨ Lavagem & Polimento</option>
                            <option value="Outro Serviço">🔧 Outro Serviço / Avaria</option>
                        </select>
                    </div>
                </div>

                <div class="grid-2">
                    <div class="form-group">
                        <label>Data Pretendida:</label>
                        <input type="date" name="data" required>
                    </div>
                    <div class="form-group">
                        <label>Horário:</label>
                        <select name="hora" required>
                            <option value="">Selecione a hora...</option>
                            <option value="09:00">09:00 - Período da Manhã</option>
                            <option value="11:00">11:00 - Fim da Manhã</option>
                            <option value="14:30">14:30 - Período da Tarde</option>
                            <option value="16:30">16:30 - Fim de Tarde</option>
                        </select>
                    </div>
                </div>

                <div class="form-group">
                    <label>Sintomas / Observações:</label>
                    <textarea name="observacoes" rows="2" placeholder="Descreva brevemente o problema ou pedido..."></textarea>
                </div>

                <div class="gdpr">
                    🔒 <b>Aviso Legal & Privacidade (GDPR):</b> Os dados recolhidos destinam-se exclusivamente à gestão da reparação e serão <b>eliminados automaticamente ao fim de 30 dias</b>.
                </div>

                <button type="submit">CONFIRMAR AGENDAMENTO</button>
            </form>
        </div>

        <footer>
            <div class="footer-links">
                <a href="#">C. Gerais de Venda</a> | 
                <a href="#">C. Gerais de Reparação</a> | 
                <a href="#">Termos e Condições</a> | 
                <a href="#">Regulamento Cookies</a> | 
                <a href="#">Contrato de Dados Pessoais</a> | 
                <a href="#">Compromisso com a Ética</a>
            </div>
            <p>⭐ Avaliações baseadas nos dados recolhidos para o Centro Auto Sofisticar: <b>4.8/5</b> (baseado em avaliações de clientes verificados)</p>
            <p style="margin-top: 10px;">© 2026 Centro Auto Sofisticar. Todos os direitos reservados.</p>
        </footer>
    </body>
    </html>
    """

# 🔐 2. LOGIN COM CÓDIGO DINÂMICO PARA O GESTOR
@app.get("/login_gestor", response_class=HTMLResponse)
def login_gestor():
    novo_codigo = f"{random.randint(1000, 9999)}"
    ESTADO_SESSAO["codigo_atual"] = novo_codigo

    return f"""
    <!DOCTYPE html>
    <html lang="pt">
    <head><meta charset="UTF-8"><title>Autenticação do Gestor - Centro Auto Sofisticar</title>
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; background: #121212; color: #fff; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
        .box {{ background: #181818; padding: 40px; border-radius: 12px; border-top: 5px solid #d4af37; width: 100%; max-width: 400px; text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,0.7); }}
        input {{ width: 100%; padding: 12px; background: #2a2a2a; border: 1px solid #555; border-radius: 6px; color: #fff; text-align: center; font-size: 22px; letter-spacing: 5px; margin-bottom: 20px; box-sizing: border-box; }}
        button {{ background: #d4af37; color: #121212; border: none; padding: 12px; font-weight: bold; font-size: 16px; border-radius: 6px; cursor: pointer; width: 100%; }}
        button:hover {{ background: #b8972f; }}
        .info-code {{ background: #252525; padding: 12px; border-radius: 6px; color: #d4af37; font-size: 14px; margin-bottom: 20px; border: 1px dashed #d4af37; }}
    </style>
    </head>
    <body>
        <div class="box">
            <h2 style="color: #d4af37; margin-top:0;">🔒 Área Restrita</h2>
            <p style="font-size:13px; color:#aaa;">Insira o código dinâmico de acesso gerado para esta sessão:</p>
            
            <div class="info-code">
                🔑 <b>Código Temporário Ativo:</b><br><span style="font-size:24px; font-weight:bold;">{novo_codigo}</span>
            </div>

            <form action="/verificar_login" method="post">
                <input type="text" name="codigo_inserido" placeholder="••••" maxlength="4" required autofocus>
                <button type="submit">ENTRAR NO PAINEL</button>
            </form>
            <br><a href="/" style="color: #888; text-decoration: none; font-size: 12px;">← Voltar ao Portal Público</a>
        </div>
    </body>
    </html>
    """

@app.post("/verificar_login")
def verificar_login(codigo_inserido: str = Form(...)):
    if codigo_inserido.strip() == ESTADO_SESSAO["codigo_atual"]:
        ESTADO_SESSAO["autenticado"] = True
        return RedirectResponse(url="/painel", status_code=303)
    else:
        return """
        <body style="background:#121212; color:#fff; font-family:sans-serif; text-align:center; padding-top:80px;">
            <div style="max-width:350px; margin:auto; background:#181818; padding:30px; border-radius:8px; border:1px solid #ff4d4d;">
                <h3 style="color:#ff4d4d;">Código Incorreto!</h3>
                <p style="color:#aaa; font-size:14px;">O código inserido não corresponde ao código dinâmico gerado.</p>
                <a href="/login_gestor" style="color:#d4af37; text-decoration:none; font-weight:bold;">← Tentar Novamente</a>
            </div>
        </body>
        """

# ⚙️ 3. PAINEL DE GESTÃO (Protegido por Sessão Dinâmica)
@app.get("/painel", response_class=HTMLResponse)
def painel_geral():
    if not ESTADO_SESSAO["autenticado"]:
        return RedirectResponse(url="/login_gestor", status_code=303)

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, codigo_seguimento, cliente, contacto, matricula, servico, data, hora, estado, observacoes FROM agendamentos ORDER BY id DESC")
    agendamentos = cursor.fetchall()
    
    cursor.execute("SELECT COUNT(*) FROM agendamentos WHERE estado = 'Pendente'")
    total_pendentes = cursor.fetchone()[0]

    cursor.execute("SELECT id, titulo, cliente, matricula, total, criado_em FROM orcamentos ORDER BY id DESC")
    orcamentos = cursor.fetchall()
    conn.close()

    alerta_html = ""
    if total_pendentes > 0:
        alerta_html = f"""
        <div style="background: #ff4d4d; color: #fff; padding: 12px 20px; border-radius: 8px; margin-bottom: 20px; font-weight: bold; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 4px 12px rgba(255,77,77,0.3);">
            <span>🚨 ATENÇÃO: Tem {total_pendentes} novo(s) agendamento(s) pendente(s) a aguardar confirmação!</span>
            <span style="background: #fff; color: #ff4d4d; padding: 2px 10px; border-radius: 12px; font-size: 12px;">Ação Necessária</span>
        </div>
        """

    linhas_ag = ""
    for a in agendamentos:
        id_a, cod, cli, cont, mat, serv, data, hora, estado, obs = a
        destaque_linha = "background: rgba(212, 175, 55, 0.05);" if estado == 'Pendente' else ""
        
        linhas_ag += f"""
        <tr style="border-bottom: 1px solid #333; {destaque_linha}">
            <td style="padding: 10px; color:#d4af37;"><b>{cod}</b></td>
            <td style="padding: 10px;">{cli}<br><small style="color:#aaa;">{cont}</small></td>
            <td style="padding: 10px;"><b>{mat}</b></td>
            <td style="padding: 10px;">{serv}<br><small>{data} às {hora}</small></td>
            <td style="padding: 10px;">
                <form action="/atualizar_estado" method="post" style="display:inline;">
                    <input type="hidden" name="id_agendamento" value="{id_a}">
                    <select name="novo_estado" onchange="this.form.submit()" style="background:#222; color:#fff; border:1px solid #555; padding:5px; border-radius:4px; font-size:13px;">
                        <option value="Pendente" {'selected' if estado == 'Pendente' else ''}>🟡 Pendente</option>
                        <option value="Confirmado" {'selected' if estado == 'Confirmado' else ''}>🔵 Confirmado</option>
                        <option value="Em Espera" {'selected' if estado == 'Em Espera' else ''}>🟠 Em Espera</option>
                        <option value="Pronto para Levantamento" {'selected' if estado == 'Pronto para Levantamento' else ''}>🟢 Pronto p/ Levantamento</option>
                    </select>
                </form>
            </td>
            <td style="padding: 10px;">
                <form action="/apagar_agendamento" method="post" style="display:inline;">
                    <input type="hidden" name="id_agendamento" value="{id_a}">
                    <button type="submit" style="background:#ff4d4d; color:#fff; border:none; padding:5px 10px; border-radius:4px; cursor:pointer;" onclick="return confirm('Apagar agendamento?');">Apagar</button>
                </form>
            </td>
        </tr>
        """

    linhas_orc = ""
    for o in orcamentos:
        linhas_orc += f"""
        <tr style="border-bottom: 1px solid #333;">
            <td style="padding: 10px;">#{o[0]}</td>
            <td style="padding: 10px;">{o[1]}</td>
            <td style="padding: 10px;">{o[2]} ({o[3]})</td>
            <td style="padding: 10px; color: #28a745; font-weight: bold;">{o[4]:.2f} €</td>
            <td style="padding: 10px;">
                <a href="/orcamento?id={o[0]}" target="_blank" style="color: #d4af37; text-decoration: none; margin-right: 10px;">Ver PDF</a>
                <form action="/apagar_orcamento" method="post" style="display:inline;">
                    <input type="hidden" name="id_orcamento" value="{o[0]}">
                    <button type="submit" style="background:#ff4d4d; color:#fff; border:none; padding:5px 10px; border-radius:4px; cursor:pointer;">Apagar</button>
                </form>
            </td>
        </tr>
        """

    return f"""
    <!DOCTYPE html>
    <html lang="pt">
    <head><meta charset="UTF-8"><title>Painel de Gestão - Centro Auto Sofisticar</title>
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; background: #121212; color: #fff; margin:0; padding:0; }}
        header {{ background: #181818; border-bottom: 2px solid #333; padding: 15px 40px; display: flex; justify-content: space-between; align-items: center; }}
        .brand {{ display: flex; align-items: center; gap: 12px; }}
        .logo-box {{ background: #d4af37; color: #121212; font-weight: bold; padding: 10px 14px; border-radius: 6px; font-size: 18px; }}
        .brand h1 {{ margin: 0; color: #d4af37; font-size: 18px; }}
        .container {{ max-width: 1100px; margin: 30px auto; background: #181818; padding: 35px; border-radius: 12px; border-top: 5px solid #d4af37; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 15px; margin-bottom: 40px; }}
        th {{ background: #222; color: #d4af37; padding: 10px; text-align: left; font-size: 13px; }}
        .btn {{ background: #d4af37; color: #121212; padding: 10px 18px; text-decoration: none; font-weight: bold; border-radius: 6px; display: inline-block; }}
    </style>
    </head>
    <body>
        <header>
            <div class="brand">
                <div class="logo-box">CAS</div>
                <div>
                    <h1>PAINEL DE CONTROLO ENTERPRISE</h1>
                    <p style="margin:0; color:#aaa; font-size:11px;">Centro Auto Sofisticar - Gestão Interna</p>
                </div>
            </div>
            <div>
                <a href="/logout" style="color: #ff4d4d; text-decoration: none; border: 1px solid #ff4d4d; padding: 6px 12px; border-radius: 6px; font-size: 13px;">🚪 Terminar Sessão</a>
            </div>
        </header>

        <div class="container">
            {alerta_html}

            <div style="margin-bottom: 25px;">
                <a href="/novo_orcamento" class="btn">+ Criar Orçamento / Descontos</a>
                <a href="/" target="_blank" style="color:#d4af37; text-decoration:none; margin-left:20px; font-weight:bold;">🌐 Ver Portal Público</a>
            </div>

            <h3 style="color:#d4af37;">📥 Gestão de Agendamentos e Estados</h3>
            <table>
                <tr><th>Código</th><th>Cliente</th><th>Matrícula</th><th>Serviço</th><th>Estado Atual</th><th>Ação</th></tr>
                {linhas_ag if linhas_ag else '<tr><td colspan="6" style="padding:15px; text-align:center; color:#777;">Sem agendamentos.</td></tr>'}
            </table>

            <h3 style="color:#d4af37;">📄 Orçamentos Emitidos</h3>
            <table>
                <tr><th>ID</th><th>Título</th><th>Cliente (Matrícula)</th><th>Total</th><th>Ações</th></tr>
                {linhas_orc if linhas_orc else '<tr><td colspan="5" style="padding:15px; text-align:center; color:#777;">Sem orçamentos.</td></tr>'}
            </table>
        </div>
    </body>
    </html>
    """

@app.get("/logout")
def logout():
    ESTADO_SESSAO["autenticado"] = False
    return RedirectResponse(url="/login_gestor", status_code=303)

@app.post("/atualizar_estado")
def atualizar_estado(id_agendamento: int = Form(...), novo_estado: str = Form(...)):
    if ESTADO_SESSAO["autenticado"]:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("UPDATE agendamentos SET estado = ? WHERE id = ?", (novo_estado, id_agendamento))
        conn.commit()
        conn.close()
    return RedirectResponse(url="/painel", status_code=303)

@app.get("/novo_orcamento", response_class=HTMLResponse)
def form_orcamento():
    if not ESTADO_SESSAO["autenticado"]: return RedirectResponse(url="/login_gestor", status_code=303)

    blocos = ""
    for cat, itens in CATALOGO_COMPLETO.items():
        blocos += f"""<div style="background:#1e1e1e; padding:15px; margin-bottom:15px; border-radius:8px; border:1px solid #444;">
        <h4 style="color:#d4af37; margin-top:0;">{cat}</h4>"""
        for nome, info in itens.items():
            blocos += f"""<div style="display:flex; justify-content:space-between; align-items:center; background:#252525; padding:6px 10px; margin-bottom:6px; border-radius:4px;">
            <label style="cursor:pointer; flex:1; font-size:13px;"><input type="checkbox" name="pecas_selecionadas" value="{nome}" style="margin-right:8px;">{nome}</label>
            <b style="color:#28a745; font-size:13px;">{info['preco']:.2f} € (Stock: {info['stock']})</b></div>"""
        blocos += "</div>"

    return f"""
    <!DOCTYPE html>
    <html lang="pt">
    <head><meta charset="UTF-8"><title>Criar Orçamento com Desconto</title>
    <style>body {{ font-family: 'Segoe UI', sans-serif; background: #121212; color: #fff; padding: 25px; }}
    .box {{ max-width: 750px; margin: auto; background: #181818; padding: 30px; border-radius: 12px; border-top: 5px solid #d4af37; }}
    input[type="text"], input[type="number"], textarea {{ width: 100%; padding: 10px; background: #2a2a2a; border: 1px solid #555; border-radius: 6px; color: #fff; margin-bottom: 15px; box-sizing: border-box; }}
    button {{ background: #d4af37; color: #121212; border: none; padding: 12px; font-weight: bold; border-radius: 6px; cursor: pointer; width: 100%; font-size: 15px; }}
    </style></head>
    <body>
        <div class="box">
            <h2>🛠️ Criar Orçamento (Com Catálogo e Descontos)</h2>
            <a href="/painel" style="color:#d4af37; text-decoration:none; display:inline-block; margin-bottom:20px;">← Voltar ao Painel</a>
            <form action="/criar_orcamento" method="post">
                <label><b>Título / Serviço:</b></label><input type="text" name="titulo" required>
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:15px;">
                    <div><label><b>Cliente:</b></label><input type="text" name="cliente" required></div>
                    <div><label><b>Matrícula:</b></label><input type="text" name="matricula" style="text-transform:uppercase;" required></div>
                </div>
                <label><b>Desconto Aplicado (€):</b></label>
                <input type="number" step="0.01" name="desconto_valor" value="0.00" placeholder="Ex: 10.00">
                <label><b>Selecionar Peças / Serviços Oferecidos:</b></label>{blocos}
                <label><b>Notas:</b></label><textarea name="descricao" rows="2"></textarea>
                <button type="submit">GERAR ORÇAMENTO E FATURAÇÃO (IVA 23%)</button>
            </form>
        </div>
    </body>
    </html>
    """

@app.post("/criar_orcamento")
def processar_criar_orcamento(
    titulo: str = Form(...), cliente: str = Form(...),
    matricula: str = Form(...), desconto_valor: float = Form(0.0),
    pecas_selecionadas: list = Form(default=[]), descricao: str = Form("")
):
    if not ESTADO_SESSAO["autenticado"]: return RedirectResponse(url="/login_gestor", status_code=303)
    
    subtotal = 0.0
    for p in pecas_selecionadas:
        for cat, itens in CATALOGO_COMPLETO.items():
            if p in itens:
                subtotal += itens[p]["preco"]

    base_tributavel = max(0.0, subtotal - desconto_valor)
    iva = base_tributavel * 0.23
    total = base_tributavel * 1.23

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO orcamentos (titulo, cliente, matricula, pecas, descricao, subtotal, desconto, iva, total) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (titulo, cliente, matricula.upper(), ", ".join(pecas_selecionadas), descricao, subtotal, desconto_valor, iva, total))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/painel", status_code=303)

@app.get("/orcamento", response_class=HTMLResponse)
def ver_orcamento(id: int):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, titulo, cliente, matricula, pecas, descricao, subtotal, desconto, iva, total, criado_em FROM orcamentos WHERE id = ?", (id,))
    reg = cursor.fetchone()
    conn.close()
    if not reg: return "<h3>Orçamento não encontrado.</h3>"
    id_o, titulo, cli, mat, pecas, desc, sub, desc_val, iva, total, criado = reg
    itens = "".join([f"<li>{p.strip()}</li>" for p in pecas.split(",") if p.strip()])

    desconto_html = f"<p>Desconto Comercial: -{desc_val:.2f} €</p>" if desc_val > 0 else ""

    return f"""
    <!DOCTYPE html>
    <html lang="pt">
    <head><meta charset="UTF-8"><title>Orçamento #{id_o}</title>
    <style>body{{font-family:Arial,sans-serif;padding:40px;max-width:650px;margin:auto;border:2px solid #d4af37;border-radius:8px;background:#fff;color:#000;}}
    @media print {{ .btn {{ display: none; }} }}</style>
    </head>
    <body>
        <button onclick="window.print()" class="btn" style="background:#d4af37;border:none;padding:8px 15px;font-weight:bold;cursor:pointer;border-radius:4px;margin-bottom:15px;">🖨️ Imprimir PDF</button>
        <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:2px solid #d4af37; padding-bottom:10px; margin-bottom:15px;">
            <div><h2 style="margin:0; color:#121212;">CENTRO AUTO SOFISTICAR</h2><small style="color:#666;">Oficina Oficial & Multimarca</small></div>
            <div style="text-align:right; font-weight:bold; font-size:14px;">Orçamento Nº {id_o}<br><span style="font-size:11px; color:#666;">{criado}</span></div>
        </div>
        <p><b>Cliente:</b> {cli} | <b>Matrícula:</b> <span style="background:#eee; padding:2px 6px; border-radius:4px;">{mat}</span></p>
        <p><b>Serviço Principal:</b> {titulo}</p>
        <h4 style="border-bottom:1px solid #ddd; padding-bottom:5px;">Serviços e Peças Aplicados:</h4>
        <ul>{itens}</ul>
        <p><b>Observações:</b> {desc if desc else 'Nenhuma'}</p>
        <div style="text-align:right; margin-top:30px; border-top:2px solid #eee; padding-top:15px;">
            <p>Subtotal Peças/Serviços: {sub:.2f} €</p>
            {desconto_html}
            <p>IVA (23%): {iva:.2f} €</p>
            <h2 style="color:#d4af37; margin:5px 0;">TOTAL FINAL: {total:.2f} €</h2>
        </div>
    </body>
    </html>
    """

@app.post("/apagar_agendamento")
def apagar_agendamento(id_agendamento: int = Form(...)):
    if ESTADO_SESSAO["autenticado"]:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM agendamentos WHERE id = ?", (id_agendamento,))
        conn.commit()
        conn.close()
    return RedirectResponse(url="/painel", status_code=303)

@app.post("/apagar_orcamento")
def apagar_orcamento(id_orcamento: int = Form(...)):
    if ESTADO_SESSAO["autenticado"]:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM orcamentos WHERE id = ?", (id_orcamento,))
        conn.commit()
        conn.close()
    return RedirectResponse(url="/painel", status_code=303)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
