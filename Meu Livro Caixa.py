import streamlit as st
import sqlite3
import pandas as pd
import os
from datetime import datetime

# ==========================================
# 1. CONFIGURAÇÕES MOBILE (FOCO MOTO G30)
# ==========================================
st.set_page_config(
    page_title="Bear Snack PDV",
    page_icon="🐻",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS PROFISSIONAL PARA TRAVAR GRADE 2 COLUNAS E MENU 5 COLUNAS
st.markdown("""
    <style>
        /* Centraliza e limita a largura para mobile */
        .main {
            max-width: 360px !important;
            margin: 0 auto;
        }

        .block-container { 
            padding: 0.5rem 0.5rem 5rem 0.5rem !important; 
        }
        
        /* MENU SUPERIOR: TRAVA EM 5 COLUNAS SEM QUEBRA */
        [data-testid="stHorizontalBlock"]:has(button[key="m1"]) {
            display: grid !important;
            grid-template-columns: repeat(5, 1fr) !important;
            gap: 4px !important;
        }

        /* GRADE DE PRODUTOS: FORÇA 2 COLUNAS (IMPEDE EMPILHAMENTO VERTICAL) */
        [data-testid="stHorizontalBlock"]:has(button[key^="btn_"]) {
            display: grid !important;
            grid-template-columns: repeat(2, 1fr) !important;
            gap: 10px !important;
            margin-bottom: 10px !important;
        }

        /* ESTILO DOS BOTÕES DE PRODUTO (NOME INTEIRO E PREÇO) */
        div.stButton > button[key^="btn_"] {
            height: 85px !important;
            width: 100% !important;
            border-radius: 12px !important;
            font-size: 15px !important;
            font-weight: bold !important;
            background: linear-gradient(145deg, #2e313c, #262730) !important;
            border: 1px solid #464855 !important;
            color: white !important;
            box-shadow: 2px 2px 8px rgba(0,0,0,0.4) !important;
            white-space: pre-wrap !important; /* Mantém o \n funcionando */
            line-height: 1.2 !important;
        }

        /* BOTÃO DE CONFIRMAÇÃO (ROBÚSTO) */
        div.stButton > button[type="primary"] {
            height: 65px !important;
            font-size: 18px !important;
            font-weight: 800 !important;
            background-color: #ff4b4b !important;
            border-radius: 10px !important;
        }

        /* ESTILO DOS BOTÕES DO MENU SUPERIOR */
        div.stButton > button {
            border-radius: 8px;
            height: 50px !important;
            background-color: #262730;
            border: 1px solid #464855;
        }

        /* ESCONDE INTERFACE NATIVA */
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        footer {visibility: hidden;}
        
        .app-header {
            font-size: 16px !important;
            font-weight: bold;
            text-align: center;
            margin-bottom: 10px;
            color: #f0f2f6;
        }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. BANCO DE DADOS (SQLITE)
# ==========================================
DB_NAME = 'livro_caixa.db'

def get_connection():
    return sqlite3.connect(DB_NAME)

def iniciar_banco():
    conn = get_connection()
    cursor = conn.cursor()
    # Tabela Vendas
    cursor.execute('''CREATE TABLE IF NOT EXISTS vendas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data_ms INTEGER, total REAL, metodo TEXT, descricao_resumo TEXT, 
        baixada INTEGER DEFAULT 1, cliente_nome TEXT
    )''')
    # Tabela Clientes
    cursor.execute('''CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL UNIQUE, tipo TEXT DEFAULT 'CLIENTE',
        telefone TEXT, saldo_devedor REAL DEFAULT 0.0
    )''')
    # Garantir colunas (Migrações)
    try: cursor.execute("ALTER TABLE vendas ADD COLUMN baixada INTEGER DEFAULT 1")
    except: pass
    try: cursor.execute("ALTER TABLE vendas ADD COLUMN cliente_nome TEXT")
    except: pass
    try: cursor.execute("ALTER TABLE clientes ADD COLUMN saldo_devedor REAL DEFAULT 0.0")
    except: pass
    conn.commit()
    conn.close()

iniciar_banco()

# ==========================================
# 3. CONTROLE DE ESTADO
# ==========================================
if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if 'pagina' not in st.session_state: st.session_state.pagina = "🛒"
if 'desc_venda' not in st.session_state: st.session_state.desc_venda = ""
if 'valor_venda' not in st.session_state: st.session_state.valor_venda = 0.0

if not st.session_state.autenticado:
    st.markdown("<h2 style='text-align: center;'>🐻 Bear Snack</h2>", unsafe_allow_html=True)
    senha = st.text_input("Senha", type="password")
    if st.button("ACESSAR", use_container_width=True):
        if senha == "Hillary2010":
            st.session_state.autenticado = True
            st.rerun()
    st.stop()

# ==========================================
# 4. MENU DE NAVEGAÇÃO SUPERIOR
# ==========================================
st.markdown(f"<p class='app-header'>🐻 Bear Snack | {st.session_state.pagina}</p>", unsafe_allow_html=True)

m_cols = st.columns(5)
if m_cols[0].button("🛒", key="m1"): st.session_state.pagina = "🛒"; st.rerun()
if m_cols[1].button("👥", key="m2"): st.session_state.pagina = "👥"; st.rerun()
if m_cols[2].button("🍱", key="m3"): st.session_state.pagina = "🍱"; st.rerun()
if m_cols[3].button("📜", key="m4"): st.session_state.pagina = "📜"; st.rerun()
if m_cols[4].button("📊", key="m5"): st.session_state.pagina = "📊"; st.rerun()

st.markdown("<hr style='margin:5px 0; border-color: #464855;'>", unsafe_allow_html=True)

# ==========================================
# 5. CONTEÚDO DAS PÁGINAS
# ==========================================

# --- TELA: PDV ---
if st.session_state.pagina == "🛒":
    atalhos = [
        ("SUCO", 6.0), ("REFRI", 6.0), 
        ("SALGADO", 8.0), ("PIPOCA", 7.0),
        ("SUCO NAT.", 8.0), ("P. QUEIJO", 7.0), 
        ("SANDUÍCHE", 8.0), ("BOLO", 9.0)
    ]
    
    # IMPORTANTE: st.columns(2) dentro de um loop para o CSS travar o grid
    for i in range(0, len(atalhos), 2):
        cols = st.columns(2)
        
        # Produto Esquerda
        n1, p1 = atalhos[i]
        if cols[0].button(f"{n1}\nR${p1:.2f}", key=f"btn_{n1}"):
            st.session_state.desc_venda = n1
            st.session_state.valor_venda = p1
            st.rerun()
            
        # Produto Direita
        if i + 1 < len(atalhos):
            n2, p2 = atalhos[i+1]
            if cols[1].button(f"{n2}\nR${p2:.2f}", key=f"btn_{n2}"):
                st.session_state.desc_venda = n2
                st.session_state.valor_venda = p2
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    with st.container(border=True):
        v_item = st.text_input("Item selecionado", value=st.session_state.desc_venda)
        v_pre = st.number_input("Preço R$", value=st.session_state.valor_venda)
        v_mod = st.selectbox("Pagamento", ["DINHEIRO", "PIX", "CARTÃO", "FIADO"])
        
        v_cli = None
        if v_mod == "FIADO":
            with get_connection() as conn:
                clis = pd.read_sql_query("SELECT nome FROM clientes ORDER BY nome", conn)['nome'].tolist()
            v_cli = st.selectbox("Cliente", clis if clis else ["Vazio"])
        
        if st.button("CONFIRMAR VENDA 🚀", use_container_width=True, type="primary"):
            agora = int(datetime.now().timestamp() * 1000)
            baixada = 0 if v_mod == "FIADO" else 1
            with get_connection() as conn:
                conn.execute("INSERT INTO vendas (data_ms, total, metodo, descricao_resumo, baixada, cliente_nome) VALUES (?,?,?,?,?,?)",
                            (agora, v_pre, v_mod, v_item, baixada, v_cli))
                if v_mod == "FIADO" and v_cli:
                    conn.execute("UPDATE clientes SET saldo_devedor = saldo_devedor + ? WHERE nome = ?", (v_pre, v_cli))
                conn.commit()
            st.success("Vendido!")
            st.session_state.desc_venda = ""
            st.session_state.valor_venda = 0.0
            st.rerun()

# --- TELA: CADERNETA ---
elif st.session_state.pagina == "👥":
    st.write("### 👥 Devedores")
    with st.expander("➕ Novo Cadastro"):
        n = st.text_input("Nome").upper()
        if st.button("SALVAR"):
            with get_connection() as conn:
                conn.execute("INSERT INTO clientes (nome, tipo) VALUES (?, 'ALUNO')", (n,))
            st.success("OK!"); st.rerun()
    with get_connection() as conn:
        df_cli = pd.read_sql_query("SELECT nome, saldo_devedor FROM clientes WHERE saldo_devedor > 0 ORDER BY nome", conn)
    st.dataframe(df_cli, use_container_width=True, hide_index=True)

# --- TELA: BANDEJA ---
elif st.session_state.pagina == "🍱":
    st.write("### 🍱 Lançar Bandeja")
    val_b = st.number_input("Valor R$", value=15.0)
    with get_connection() as conn:
        alunos = pd.read_sql_query("SELECT nome FROM clientes WHERE tipo='BANDEJA'", conn)['nome'].tolist()
    sel = []
    for a in alunos:
        if st.checkbox(a, key=f"chk_{a}"): sel.append(a)
    if st.button("LANÇAR TUDO", use_container_width=True, type="primary"):
        agora = int(datetime.now().timestamp() * 1000)
        with get_connection() as conn:
            for n in sel:
                conn.execute("INSERT INTO vendas (data_ms, total, metodo, descricao_resumo, baixada, cliente_nome) VALUES (?,?,?,?,0,?)", (agora, val_b, "FIADO", "BANDEJA", n))
                conn.execute("UPDATE clientes SET saldo_devedor = saldo_devedor + ? WHERE nome = ?", (val_b, n))
            conn.commit()
        st.success("Sucesso!"); st.rerun()

# --- TELA: HISTÓRICO ---
elif st.session_state.pagina == "📜":
    st.write("### 📜 Recentes")
    with get_connection() as conn:
        df_h = pd.read_sql_query("SELECT id, total, metodo, cliente_nome FROM vendas ORDER BY id DESC LIMIT 15", conn)
    st.dataframe(df_h, use_container_width=True, hide_index=True)

# --- TELA: RELATÓRIOS ---
elif st.session_state.pagina == "📊":
    st.write("### 📊 Resumo")
    with get_connection() as conn:
        v_total = conn.execute("SELECT SUM(total) FROM vendas").fetchone()[0] or 0
        f_total = conn.execute("SELECT SUM(saldo_devedor) FROM clientes").fetchone()[0] or 0
    st.metric("Vendido", f"R${v_total:.2f}")
    st.metric("Fiado", f"R${f_total:.2f}")
    if st.button("LOGOUT"):
        st.session_state.autenticado = False
        st.rerun()
