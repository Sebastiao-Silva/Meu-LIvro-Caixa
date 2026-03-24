import streamlit as st
import sqlite3
import pandas as pd
import os
from datetime import datetime

# ==========================================
# 1. CONFIGURAÇÕES MOBILE (MOTO G30 360x800)
# ==========================================
st.set_page_config(
    page_title="Bear Snack PDV",
    page_icon="🐻",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS PROFISSIONAL PARA FORÇAR LAYOUT MOBILE SEM QUEBRAS
st.markdown("""
    <style>
        /* Remove margens e espaços do Streamlit para ganhar tela */
        .block-container { 
            padding: 0.5rem 0.5rem 5rem 0.5rem !important; 
            max-width: 100% !important;
        }
        
        /* FORÇA OS BOTÕES DO MENU A FICAREM LADO A LADO NO CELULAR */
        [data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            align-items: center !important;
            justify-content: space-between !important;
        }
        
        [data-testid="column"] {
            width: 18% !important;
            flex: 1 1 auto !important;
            min-width: 0px !important;
        }

        /* Estilo dos botões de Ícone */
        div.stButton > button {
            border-radius: 10px;
            padding: 0px;
            height: 55px;
            width: 100%;
            font-size: 22px !important;
            background-color: #262730;
            border: 1px solid #464855;
        }

        /* Destaque para o botão da página ativa */
        .stButton button:active, .stButton button:focus {
            background-color: #ff4b4b !important;
            color: white !important;
        }

        /* Esconde elementos inúteis do Streamlit */
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        footer {visibility: hidden;}

        /* Ajuste de inputs para não ocupar muito espaço vertical */
        .stNumberInput, .stTextInput, .stSelectbox {
            margin-bottom: -10px;
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
    # Garantia de colunas (Migração)
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
# 3. CONTROLE DE NAVEGAÇÃO E LOGIN
# ==========================================
if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if 'pagina' not in st.session_state: st.session_state.pagina = "🛒"
if 'desc_venda' not in st.session_state: st.session_state.desc_venda = ""
if 'valor_venda' not in st.session_state: st.session_state.valor_venda = 0.0

if not st.session_state.autenticado:
    st.markdown("<h2 style='text-align: center;'>🐻 Bear Snack</h2>", unsafe_allow_html=True)
    senha = st.text_input("Senha", type="password")
    if st.button("ENTRAR NO SISTEMA", use_container_width=True):
        if senha == "Hillary2010":
            st.session_state.autenticado = True
            st.rerun()
    st.stop()

# ==========================================
# 4. CABEÇALHO FIXO (MOTO G30)
# ==========================================
# Logo e Título compactos
c_logo, c_tit = st.columns([1, 4])
with c_logo:
    if os.path.exists("logo.png"): st.image("logo.png", width=45)
    else: st.write("🐻")
with c_tit:
    st.markdown(f"<h4 style='margin:0;'>Bear Snack <span style='color:#ff4b4b;'>{st.session_state.pagina}</span></h4>", unsafe_allow_html=True)

# BARRA DE ÍCONES (FORÇADA NA HORIZONTAL PELO CSS ACIMA)
m_cols = st.columns(5)
if m_cols[0].button("🛒"): st.session_state.pagina = "🛒"; st.rerun()
if m_cols[1].button("👥"): st.session_state.pagina = "👥"; st.rerun()
if m_cols[2].button("🍱"): st.session_state.pagina = "🍱"; st.rerun()
if m_cols[3].button("📜"): st.session_state.pagina = "📜"; st.rerun()
if m_cols[4].button("📊"): st.session_state.pagina = "📊"; st.rerun()

st.markdown("<hr style='margin:2px 0;'>", unsafe_allow_html=True)

# ==========================================
# 5. TELAS DO APLICATIVO
# ==========================================

# --- TELA PDV ---
if st.session_state.pagina == "🛒":
    # Grade de produtos 2x2 para dedos grandes
    atalhos = {
        "SUCO": 5.0, "REFRI": 6.0, "SALGADO": 8.0, "PIPOCA": 7.0,
        "NATU": 8.0, "P.QJO": 7.0, "SAND": 9.5, "BOLO": 8.0
    }
    grid = st.columns(2)
    for i, (item, preco) in enumerate(atalhos.items()):
        if grid[i % 2].button(f"{item}\nR${preco}", key=f"p_{item}", use_container_width=True):
            st.session_state.desc_venda = item
            st.session_state.valor_venda = preco
            st.rerun()

    with st.form("form_venda", clear_on_submit=True):
        v_item = st.text_input("Item", value=st.session_state.desc_venda)
        v_pre = st.number_input("R$", value=st.session_state.valor_venda)
        v_mod = st.selectbox("Pagamento", ["DINHEIRO", "PIX", "CARTÃO", "FIADO"])
        
        v_cli = None
        if v_mod == "FIADO":
            with get_connection() as conn:
                clis = pd.read_sql_query("SELECT nome FROM clientes ORDER BY nome", conn)['nome'].tolist()
            v_cli = st.selectbox("Qual Cliente?", clis if clis else ["Vazio"])
        
        if st.form_submit_button("FINALIZAR 🚀", use_container_width=True):
            agora = int(datetime.now().timestamp() * 1000)
            baixada = 0 if v_mod == "FIADO" else 1
            with get_connection() as conn:
                conn.execute("INSERT INTO vendas (data_ms, total, metodo, descricao_resumo, baixada, cliente_nome) VALUES (?,?,?,?,?,?)",
                            (agora, v_pre, v_mod, v_item, baixada, v_cli))
                if v_mod == "FIADO" and v_cli:
                    conn.execute("UPDATE clientes SET saldo_devedor = saldo_devedor + ? WHERE nome = ?", (v_pre, v_cli))
                conn.commit()
            st.success("Salvo!")
            st.session_state.desc_venda = ""
            st.session_state.valor_venda = 0.0
            st.rerun()

# --- TELA CADERNETA ---
elif st.session_state.pagina == "👥":
    st.write("### Devedores")
    with st.expander("➕ Novo Cliente"):
        n = st.text_input("Nome").upper()
        if st.button("CADASTRAR"):
            with get_connection() as conn:
                conn.execute("INSERT INTO clientes (nome, tipo) VALUES (?, 'ALUNO')", (n,))
            st.success("Ok!"); st.rerun()
    
    with get_connection() as conn:
        df_cli = pd.read_sql_query("SELECT nome, saldo_devedor FROM clientes WHERE saldo_devedor > 0 ORDER BY saldo_devedor DESC", conn)
    st.dataframe(df_cli, use_container_width=True, hide_index=True)

# --- TELA BANDEJA ---
elif st.session_state.pagina == "🍱":
    st.write("### Bandeja Diária")
    val_b = st.number_input("Valor R$", value=15.0)
    with get_connection() as conn:
        alunos = pd.read_sql_query("SELECT nome FROM clientes WHERE tipo='BANDEJA'", conn)['nome'].tolist()
    
    sel = []
    for a in alunos:
        if st.checkbox(a, key=f"b_{a}"): sel.append(a)
    
    if st.button("LANÇAR PARA SELECIONADOS", use_container_width=True, type="primary"):
        agora = int(datetime.now().timestamp() * 1000)
        with get_connection() as conn:
            for n in sel:
                conn.execute("INSERT INTO vendas (data_ms, total, metodo, descricao_resumo, baixada, cliente_nome) VALUES (?,?,?,?,0,?)", (agora, val_b, "FIADO", "BANDEJA", n))
                conn.execute("UPDATE clientes SET saldo_devedor = saldo_devedor + ? WHERE nome = ?", (val_b, n))
            conn.commit()
        st.success("Lançado!"); st.rerun()

# --- TELA HISTÓRICO ---
elif st.session_state.pagina == "📜":
    st.write("### Vendas Recentes")
    with get_connection() as conn:
        df_h = pd.read_sql_query("SELECT id, total, metodo, cliente_nome FROM vendas ORDER BY id DESC LIMIT 15", conn)
    st.dataframe(df_h, use_container_width=True, hide_index=True)

# --- TELA RELATÓRIOS ---
elif st.session_state.pagina == "📊":
    st.write("### Financeiro")
    with get_connection() as conn:
        v_total = conn.execute("SELECT SUM(total) FROM vendas").fetchone()[0] or 0
        f_total = conn.execute("SELECT SUM(saldo_devedor) FROM clientes").fetchone()[0] or 0
    
    st.metric("Vendido", f"R${v_total:.2f}")
    st.metric("Em Aberto", f"R${f_total:.2f}")
    
    if st.button("LOGOUT", use_container_width=True):
        st.session_state.autenticado = False
        st.rerun()

st.sidebar.caption(f"Bear Snack v2.4 | Sebas")
