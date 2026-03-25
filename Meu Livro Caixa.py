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

# CSS PARA FORÇAR OS 5 BOTÕES LADO A LADO E REMOVER ESPAÇOS
st.markdown("""
    <style>
        /* Remove paddings laterais para ganhar largura no celular */
        .block-container { 
            padding: 0.5rem 0.2rem 5rem 0.2rem !important; 
            max-width: 100% !important;
        }
        
        /* FORÇA O CONTAINER DE COLUNAS A SER UM FLEXBOX SEM QUEBRA */
        [data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            gap: 1px !important; /* Espaço mínimo entre os botões */
            width: 100% !important;
        }
        
        /* CADA COLUNA OCUPA EXATAMENTE 20% DA LARGURA */
        [data-testid="column"] {
            width: 20% !important;
            flex: 1 1 auto !important;
            min-width: 0px !important;
            padding: 0px !important;
        }

        /* ESTILO DOS BOTÕES DO MENU (ALTURA PARA O POLEGAR) */
        div.stButton > button {
            border-radius: 4px;
            padding: 0px !important;
            height: 60px !important; 
            width: 100% !important;
            font-size: 22px !important; 
            background-color: #262730;
            border: 1px solid #464855;
            margin: 0px !important;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        /* COR DE DESTAQUE AO CLICAR */
        div.stButton > button:active, div.stButton > button:focus {
            background-color: #ff4b4b !important;
            border-color: #ff4b4b !important;
            color: white !important;
        }

        /* ESCONDE INTERFACE PADRÃO DO STREAMLIT */
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* TÍTULO COMPACTO */
        .app-header {
            font-size: 16px !important;
            font-weight: bold;
            text-align: center;
            margin-bottom: 5px;
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
    # Migrações (Adiciona colunas se não existirem)
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
# 3. CONTROLE DE ESTADO E NAVEGAÇÃO
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
# 4. MENU DE NAVEGAÇÃO SUPERIOR (FIXO)
# ==========================================
st.markdown(f"<p class='app-header'>🐻 Bear Snack | {st.session_state.pagina}</p>", unsafe_allow_html=True)

# Forçando 5 colunas lado a lado (20% cada via CSS)
m1, m2, m3, m4, m5 = st.columns(5)
if m1.button("🛒"): st.session_state.pagina = "🛒"; st.rerun()
if m2.button("👥"): st.session_state.pagina = "👥"; st.rerun()
if m3.button("🍱"): st.session_state.pagina = "🍱"; st.rerun()
if m4.button("📜"): st.session_state.pagina = "📜"; st.rerun()
if m5.button("📊"): st.session_state.pagina = "📊"; st.rerun()

st.markdown("<hr style='margin:5px 0;'>", unsafe_allow_html=True)

# ==========================================
# 5. CONTEÚDO DAS PÁGINAS
# ==========================================

# --- TELA: PDV ---
if st.session_state.pagina == "🛒":
    atalhos = {
        "SUCO": 6.0, "REFRI": 6.0, "SALGADO": 8.0, "PIPOCA": 7.0,
        "NATU": 8.0, "P.QJO": 7.0, "SAND": 8.0, "BOLO": 9.0
    }
    # Botões de venda em 2 colunas para o celular
    grid = st.columns(2)
    for i, (item, preco) in enumerate(atalhos.items()):
        if grid[i % 2].button(f"{item}\nR${preco}", key=f"btn_{item}", use_container_width=True):
            st.session_state.desc_venda = item
            st.session_state.valor_venda = preco
            st.rerun()

    with st.container(border=True):
        v_item = st.text_input("Descrição", value=st.session_state.desc_venda)
        v_pre = st.number_input("Preço R$", value=st.session_state.valor_venda)
        v_mod = st.selectbox("Pgto", ["DINHEIRO", "PIX", "CARTÃO", "FIADO"])
        
        v_cli = None
        if v_mod == "FIADO":
            with get_connection() as conn:
                clis = pd.read_sql_query("SELECT nome FROM clientes ORDER BY nome", conn)['nome'].tolist()
            v_cli = st.selectbox("Cliente?", clis if clis else ["Vazio"])
        
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
    st.write("### 👥 Clientes Devedores")
    with st.expander("➕ Cadastrar Novo"):
        n = st.text_input("Nome").upper()
        if st.button("SALVAR"):
            with get_connection() as conn:
                conn.execute("INSERT INTO clientes (nome, tipo) VALUES (?, 'ALUNO')", (n,))
            st.success("Cadastrado!"); st.rerun()
    
    with get_connection() as conn:
        df_cli = pd.read_sql_query("SELECT nome, saldo_devedor FROM clientes WHERE saldo_devedor > 0 ORDER BY saldo_devedor DESC", conn)
    st.dataframe(df_cli, use_container_width=True, hide_index=True)

# --- TELA: BANDEJA ---
elif st.session_state.pagina == "🍱":
    st.write("### 🍱 Bandeja Diária")
    val_b = st.number_input("Valor R$", value=15.0)
    with get_connection() as conn:
        alunos = pd.read_sql_query("SELECT nome FROM clientes WHERE tipo='BANDEJA'", conn)['nome'].tolist()
    
    sel = []
    for a in alunos:
        if st.checkbox(a, key=f"chk_{a}"): sel.append(a)
    
    if st.button("LANÇAR BANDEJAS", use_container_width=True, type="primary"):
        agora = int(datetime.now().timestamp() * 1000)
        with get_connection() as conn:
            for n in sel:
                conn.execute("INSERT INTO vendas (data_ms, total, metodo, descricao_resumo, baixada, cliente_nome) VALUES (?,?,?,?,0,?)", (agora, val_b, "FIADO", "BANDEJA", n))
                conn.execute("UPDATE clientes SET saldo_devedor = saldo_devedor + ? WHERE nome = ?", (val_b, n))
            conn.commit()
        st.success("Sucesso!"); st.rerun()

# --- TELA: HISTÓRICO ---
elif st.session_state.pagina == "📜":
    st.write("### 📜 Últimas Vendas")
    with get_connection() as conn:
        df_h = pd.read_sql_query("SELECT id, total, metodo, cliente_nome FROM vendas ORDER BY id DESC LIMIT 15", conn)
    st.dataframe(df_h, use_container_width=True, hide_index=True)

# --- TELA: RELATÓRIOS ---
elif st.session_state.pagina == "📊":
    st.write("### 📊 Financeiro")
    with get_connection() as conn:
        v_total = conn.execute("SELECT SUM(total) FROM vendas").fetchone()[0] or 0
        f_total = conn.execute("SELECT SUM(saldo_devedor) FROM clientes").fetchone()[0] or 0
    
    st.metric("Total Vendido", f"R${v_total:.2f}")
    st.metric("A Receber (Fiado)", f"R${f_total:.2f}")
    
    if st.button("SAIR DO SISTEMA"):
        st.session_state.autenticado = False
        st.rerun()
