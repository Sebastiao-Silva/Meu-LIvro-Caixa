import streamlit as st
import sqlite3
import pandas as pd
import urllib.parse
import os
from datetime import datetime

# ==========================================
# 1. CONFIGURAÇÕES MOBILE E ESTILO (CSS)
# ==========================================
st.set_page_config(
    page_title="Bear Snack PDV",
    page_icon="🐻",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Estilização para parecer um Aplicativo de Celular
st.markdown("""
    <style>
        /* Remove espaços excessivos no topo */
        .block-container { padding-top: 1rem; padding-bottom: 5rem; }
        
        /* Deixa o cabeçalho do Urso Centralizado */
        .header-container { text-align: center; margin-bottom: 20px; }
        
        /* Estiliza os botões de Navegação (Ícones) */
        div.stButton > button {
            border-radius: 12px;
            height: 3.5em;
            font-size: 18px !important;
            transition: 0.3s;
        }
        
        /* Botão de Confirmar Venda em Destaque */
        .stButton button[kind="primary"] {
            background-color: #ff4b4b;
            color: white;
            border: none;
        }

        /* Ajuste de tabelas para telas pequenas */
        .stDataFrame { width: 100% !important; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. GESTÃO DO BANCO DE DADOS (SQLite)
# ==========================================
DB_NAME = 'livro_caixa.db'

def get_connection():
    return sqlite3.connect(DB_NAME)

def iniciar_banco():
    """Garante que todas as tabelas e colunas existam para evitar erros."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Tabela de Vendas
    cursor.execute('''CREATE TABLE IF NOT EXISTS vendas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data_ms INTEGER,
        total REAL,
        metodo TEXT,
        descricao_resumo TEXT,
        baixada INTEGER DEFAULT 1,
        cliente_nome TEXT
    )''')
    
    # Tabela de Clientes
    cursor.execute('''CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL UNIQUE,
        tipo TEXT DEFAULT 'CLIENTE',
        telefone TEXT,
        saldo_devedor REAL DEFAULT 0.0
    )''')
    
    # Migrações Automáticas (Caso o banco já exista sem essas colunas)
    try: cursor.execute("ALTER TABLE vendas ADD COLUMN baixada INTEGER DEFAULT 1")
    except: pass
    try: cursor.execute("ALTER TABLE vendas ADD COLUMN cliente_nome TEXT")
    except: pass
    try: cursor.execute("ALTER TABLE clientes ADD COLUMN telefone TEXT")
    except: pass
    try: cursor.execute("ALTER TABLE clientes ADD COLUMN saldo_devedor REAL DEFAULT 0.0")
    except: pass
    
    conn.commit()
    conn.close()

iniciar_banco()

# ==========================================
# 3. CONTROLE DE ACESSO E ESTADO
# ==========================================
if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if 'pagina' not in st.session_state: st.session_state.pagina = "🛒 PDV"
if 'desc_venda' not in st.session_state: st.session_state.desc_venda = ""
if 'valor_venda' not in st.session_state: st.session_state.valor_venda = 0.0

if not st.session_state.autenticado:
    st.markdown("<div class='header-container'><h1>🐻 Bear Snack</h1><p>Sistema de Cantina</p></div>", unsafe_allow_html=True)
    senha = st.text_input("Senha de Acesso", type="password")
    if st.button("ENTRAR", use_container_width=True, type="primary"):
        if senha == "Hillary2010":
            st.session_state.autenticado = True
            st.rerun()
        else:
            st.error("Senha incorreta!")
    st.stop()

# ==========================================
# 4. MENU SUPERIOR ESTÁTICO (WEB APP STYLE)
# ==========================================
# Exibe o logo e o menu sempre no topo
col_logo, col_titulo = st.columns([1, 4])
with col_logo:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=200)
    else:
        st.title("🐻")
with col_titulo:
    st.subheader("Bear Snack Admin")

# Botões de Navegação estilo Barra de Ícones
# Ideal para o polegar no Moto G30
m1, m2, m3, m4, m5 = st.columns(5)
if m1.button("🛒", help="Vendas", use_container_width=True): st.session_state.pagina = "🛒 PDV"
if m2.button("👥", help="Clientes", use_container_width=True): st.session_state.pagina = "👥 Caderneta"
if m3.button("🍱", help="Bandeja", use_container_width=True): st.session_state.pagina = "🍱 Bandeja"
if m4.button("📜", help="Histórico", use_container_width=True): st.session_state.pagina = "📜 Histórico"
if m5.button("📊", help="Relatórios", use_container_width=True): st.session_state.pagina = "📊 Relatórios"

st.markdown("---")

# ==========================================
# 5. TELAS DO SISTEMA
# ==========================================

# --- TELA: PDV ---
if st.session_state.pagina == "🛒 PDV":
    st.write("### 🛒 Ponto de Venda")
    
    # Atalhos em grade de 2 colunas para mobile
    atalhos = {
        "SUCO": 5.0, "REFRI": 6.0, "SALGADO": 8.0, "PIPOCA": 7.0,
        "SUCO NAT.": 8.0, "BISCOITO": 4.0, "SANDUÍCHE": 8.50, "BOLO": 7.0
    }
    
    grid_atalhos = st.columns(2)
    for i, (item, preco) in enumerate(atalhos.items()):
        if grid_atalhos[i % 2].button(f"{item}\nRS {preco:.2f}", key=f"btn_{item}", use_container_width=True):
            st.session_state.desc_venda = item
            st.session_state.valor_venda = preco
            st.rerun()

    with st.container(border=True):
        st.write("**Resumo da Venda**")
        desc_final = st.text_input("Descrição", value=st.session_state.desc_venda)
        valor_final = st.number_input("Valor R$", value=st.session_state.valor_venda, step=0.50)
        metodo_final = st.selectbox("Pagamento", ["DINHEIRO", "PIX", "CARTÃO", "FIADO"])
        
        cliente_venda = None
        if metodo_final == "FIADO":
            with get_connection() as conn:
                cli_df = pd.read_sql_query("SELECT nome FROM clientes ORDER BY nome", conn)
            cliente_venda = st.selectbox("Quem é o cliente?", cli_df['nome'].tolist() if not cli_df.empty else ["Nenhum cliente cadastrado"])

        if st.button("FINALIZAR VENDA 🚀", use_container_width=True, type="primary"):
            agora = int(datetime.now().timestamp() * 1000)
            baixada = 0 if metodo_final == "FIADO" else 1
            
            with get_connection() as conn:
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO vendas (data_ms, total, metodo, descricao_resumo, baixada, cliente_nome) 
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (agora, valor_final, metodo_final, desc_final, baixada, cliente_venda))
                
                if metodo_final == "FIADO" and cliente_venda:
                    cur.execute("UPDATE clientes SET saldo_devedor = saldo_devedor + ? WHERE nome = ?", (valor_final, cliente_venda))
                conn.commit()
            
            st.success("Venda salva!")
            st.session_state.desc_venda = ""
            st.session_state.valor_venda = 0.0
            st.rerun()

# --- TELA: CADERNETA ---
elif st.session_state.pagina == "👥 Caderneta":
    st.write("### 👥 Gestão de Clientes")
    sub_menu = st.radio("Ação:", ["Listar Débitos", "Novo Cadastro"], horizontal=True)
    
    if sub_menu == "Novo Cadastro":
        with st.form("form_cliente"):
            n = st.text_input("Nome Completo").upper()
            t = st.selectbox("Categoria", ["ALUNO", "FUNCIONÁRIO", "BANDEJA"])
            tel = st.text_input("WhatsApp")
            if st.form_submit_button("Cadastrar Cliente", use_container_width=True):
                if n:
                    with get_connection() as conn:
                        conn.execute("INSERT INTO clientes (nome, tipo, telefone) VALUES (?,?,?)", (n, t, tel))
                    st.success("Cadastrado!")
                else: st.warning("Nome obrigatório.")
    else:
        try:
            with get_connection() as conn:
                df_cli = pd.read_sql_query("SELECT nome, tipo, saldo_devedor FROM clientes WHERE saldo_devedor > 0 ORDER BY saldo_devedor DESC", conn)
            st.dataframe(df_cli, use_container_width=True, hide_index=True)
        except:
            st.info("Nenhum débito encontrado.")

# --- TELA: BANDEJA ---
elif st.session_state.pagina == "🍱 Bandeja":
    st.write("### 🍱 Lançamento em Massa")
    valor_b = st.number_input("Preço da Bandeja R$", value=15.0)
    
    with get_connection() as conn:
        lista_bandeja = pd.read_sql_query("SELECT nome FROM clientes WHERE tipo='BANDEJA'", conn)['nome'].tolist()
    
    if not lista_bandeja:
        st.warning("Não há clientes cadastrados como 'BANDEJA'.")
    else:
        st.write("Selecione quem comeu hoje:")
        selecionados = []
        for aluno in lista_bandeja:
            if st.checkbox(aluno, key=f"b_{aluno}"):
                selecionados.append(aluno)
        
        if st.button("Lançar para Selecionados", type="primary", use_container_width=True):
            if selecionados:
                agora = int(datetime.now().timestamp() * 1000)
                with get_connection() as conn:
                    for n in selecionados:
                        conn.execute("INSERT INTO vendas (data_ms, total, metodo, descricao_resumo, baixada, cliente_nome) VALUES (?,?,?,?,0,?)",
                                    (agora, valor_b, "FIADO", "BANDEJA", n))
                        conn.execute("UPDATE clientes SET saldo_devedor = saldo_devedor + ? WHERE nome = ?", (valor_b, n))
                    conn.commit()
                st.success("Lançado com sucesso!")
            else: st.error("Selecione alguém!")

# --- TELA: HISTÓRICO ---
elif st.session_state.pagina == "📜 Histórico":
    st.write("### 📜 Últimas 20 Vendas")
    try:
        with get_connection() as conn:
            df_hist = pd.read_sql_query("SELECT id, total, metodo, cliente_nome FROM vendas ORDER BY id DESC LIMIT 20", conn)
        st.dataframe(df_hist, use_container_width=True, hide_index=True)
        
        if st.button("Limpar Tudo (Cuidado!)"):
            with get_connection() as conn:
                conn.execute("DELETE FROM vendas")
                conn.commit()
            st.rerun()
    except:
        st.info("Sem vendas no histórico.")

# --- TELA: RELATÓRIOS ---
elif st.session_state.pagina == "📊 Relatórios":
    st.write("### 📊 Financeiro")
    with get_connection() as conn:
        vendas_tot = conn.execute("SELECT SUM(total) FROM vendas").fetchone()[0] or 0
        fiado_tot = conn.execute("SELECT SUM(saldo_devedor) FROM clientes").fetchone()[0] or 0
    
    st.metric("Vendas Totais", f"R$ {vendas_tot:.2f}")
    st.metric("Total a Receber (Fiado)", f"R$ {fiado_tot:.2f}")
    
    if st.button("Sair / Logout", use_container_width=True):
        st.session_state.autenticado = False
        st.rerun()

st.sidebar.caption(f"Bear Snack v2.4 | Sebas")
