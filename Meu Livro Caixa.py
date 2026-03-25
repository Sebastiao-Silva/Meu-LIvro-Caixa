import streamlit as st
import sqlite3
import pandas as pd
import os
from datetime import datetime

# ==========================================
# 1. CONFIGURAÇÕES E CSS "FORCE SIDE-BY-SIDE"
# ==========================================
st.set_page_config(
    page_title="Bear Snack PDV",
    page_icon="🐻",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS que força as colunas a NÃO QUEBRAREM no celular
st.html("""
    <style>
        /* Ajuste do container principal */
        .block-container { 
            padding: 0.5rem !important; 
            max-width: 100% !important;
        }

        /* FORÇA O MENU SUPERIOR (5 COLUNAS) - IMPEDE EMPILHAMENTO */
        [data-testid="stHorizontalBlock"]:has(button[key="m1"]) {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            width: 100% !important;
        }
        [data-testid="stHorizontalBlock"]:has(button[key="m1"]) > div {
            width: 20% !important;
            min-width: 20% !important;
        }

        /* FORÇA OS BOTÕES DE PRODUTO (2 COLUNAS) - O PONTO CHAVE */
        [data-testid="stHorizontalBlock"]:has(button[key^="btn_"]) {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            width: 100% !important;
            gap: 10px !important;
        }
        [data-testid="stHorizontalBlock"]:has(button[key^="btn_"]) > div {
            width: 50% !important;
            min-width: 50% !important;
            flex: 1 1 auto !important;
        }

        /* ESTILO DOS BOTÕES DE PRODUTO */
        div.stButton > button[key^="btn_"] {
            height: 90px !important;
            width: 100% !important;
            border-radius: 12px !important;
            font-size: 14px !important;
            font-weight: bold !important;
            background: linear-gradient(145deg, #2e313c, #262730) !important;
            border: 1px solid #464855 !important;
            color: white !important;
            white-space: pre-wrap !important;
            line-height: 1.2 !important;
        }

        /* ESTILO DOS BOTÕES DO MENU */
        div.stButton > button {
            height: 50px !important;
            border-radius: 8px !important;
            background-color: #262730 !important;
        }

        /* BOTÃO CONFIRMAR */
        div.stButton > button[type="primary"] {
            height: 65px !important;
            background-color: #ff4b4b !important;
            font-size: 18px !important;
        }

        /* LIMPEZA GERAL */
        #MainMenu, header, footer, [data-testid="stHeader"] { 
            visibility: hidden; 
            display: none; 
        }
    </style>
""")

# ==========================================
# 2. BANCO DE DADOS (SQLITE)
# ==========================================
DB_NAME = 'livro_caixa.db'

def get_connection():
    return sqlite3.connect(DB_NAME)

def iniciar_banco():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS vendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_ms INTEGER, total REAL, metodo TEXT, descricao_resumo TEXT, 
            baixada INTEGER DEFAULT 1, cliente_nome TEXT
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE, tipo TEXT DEFAULT 'CLIENTE',
            telefone TEXT, saldo_devedor REAL DEFAULT 0.0
        )''')
        # Migrações para garantir funcionamento
        try: cursor.execute("ALTER TABLE vendas ADD COLUMN baixada INTEGER DEFAULT 1")
        except: pass
        try: cursor.execute("ALTER TABLE vendas ADD COLUMN cliente_nome TEXT")
        except: pass
        try: cursor.execute("ALTER TABLE clientes ADD COLUMN saldo_devedor REAL DEFAULT 0.0")
        except: pass
        conn.commit()

iniciar_banco()

# ==========================================
# 3. ESTADO E NAVEGAÇÃO
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

# TÍTULO DA PÁGINA
st.markdown(f"<p style='text-align:center; font-weight:bold; margin-bottom:5px;'>🐻 {st.session_state.pagina} Bear Snack</p>", unsafe_allow_html=True)

# BARRA DE MENU (5 COLUNAS)
m1, m2, m3, m4, m5 = st.columns(5)
if m1.button("🛒", key="m1"): st.session_state.pagina = "🛒"; st.rerun()
if m2.button("👥", key="m2"): st.session_state.pagina = "👥"; st.rerun()
if m3.button("🍱", key="m3"): st.session_state.pagina = "🍱"; st.rerun()
if m4.button("📜", key="m4"): st.session_state.pagina = "📜"; st.rerun()
if m5.button("📊", key="m5"): st.session_state.pagina = "📊"; st.rerun()

st.markdown("---")

# ==========================================
# 4. CONTEÚDO PDV
# ==========================================

if st.session_state.pagina == "🛒":
    atalhos = [
        ("SUCO", 6.0), ("REFRI", 6.0), 
        ("SALGADO", 8.0), ("PIPOCA", 7.0),
        ("SUCO NAT.", 8.0), ("P. QUEIJO", 7.0), 
        ("SANDUÍCHE", 8.0), ("BOLO", 9.0)
    ]
    
    # Renderização em 2 colunas travadas pelo CSS
    for i in range(0, len(atalhos), 2):
        row = st.columns(2)
        n1, p1 = atalhos[i]
        if row[0].button(f"{n1}\nR${p1:.2f}", key=f"btn_{n1}"):
            st.session_state.desc_venda = n1
            st.session_state.valor_venda = p1
            st.rerun()
        
        if i + 1 < len(atalhos):
            n2, p2 = atalhos[i+1]
            if row[1].button(f"{n2}\nR${p2:.2f}", key=f"btn_{n2}"):
                st.session_state.desc_venda = n2
                st.session_state.valor_venda = p2
                st.rerun()

    with st.container(border=True):
        v_item = st.text_input("Item", value=st.session_state.desc_venda)
        v_pre = st.number_input("R$", value=st.session_state.valor_venda)
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
            st.success("OK!")
            st.session_state.desc_venda = ""
            st.session_state.valor_venda = 0.0
            st.rerun()

# --- OUTRAS PÁGINAS (MANTIDAS) ---
elif st.session_state.pagina == "👥":
    st.write("### 👥 Clientes")
    with st.expander("Novo"):
        n = st.text_input("Nome").upper()
        if st.button("SALVAR"):
            with get_connection() as conn:
                conn.execute("INSERT INTO clientes (nome, tipo) VALUES (?, 'ALUNO')", (n,))
            st.rerun()
    with get_connection() as conn:
        df = pd.read_sql_query("SELECT nome, saldo_devedor FROM clientes WHERE saldo_devedor > 0", conn)
    st.dataframe(df, use_container_width=True, hide_index=True)

elif st.session_state.pagina == "🍱":
    st.write("### 🍱 Bandeja")
    v_b = st.number_input("Valor", value=15.0)
    with get_connection() as conn:
        alunos = pd.read_sql_query("SELECT nome FROM clientes WHERE tipo='BANDEJA'", conn)['nome'].tolist()
    sel = [a for a in alunos if st.checkbox(a, key=f"chk_{a}")]
    if st.button("LANÇAR", use_container_width=True, type="primary"):
        agora = int(datetime.now().timestamp() * 1000)
        with get_connection() as conn:
            for n in sel:
                conn.execute("INSERT INTO vendas (data_ms, total, metodo, descricao_resumo, baixada, cliente_nome) VALUES (?,?,?,?,0,?)", (agora, v_b, "FIADO", "BANDEJA", n))
                conn.execute("UPDATE clientes SET saldo_devedor = saldo_devedor + ? WHERE nome = ?", (v_b, n))
            conn.commit()
        st.rerun()

elif st.session_state.pagina == "📜":
    st.write("### 📜 Histórico")
    with get_connection() as conn:
        df_h = pd.read_sql_query("SELECT id, total, metodo, cliente_nome FROM vendas ORDER BY id DESC LIMIT 15", conn)
    st.dataframe(df_h, use_container_width=True, hide_index=True)

elif st.session_state.pagina == "📊":
    st.write("### 📊 Relatório")
    with get_connection() as conn:
        v = conn.execute("SELECT SUM(total) FROM vendas").fetchone()[0] or 0
        f = conn.execute("SELECT SUM(saldo_devedor) FROM clientes").fetchone()[0] or 0
    st.metric("Vendido", f"R${v:.2f}")
    st.metric("Fiado", f"R${f:.2f}")
    if st.button("SAIR"):
        st.session_state.autenticado = False
        st.rerun()
