import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# ==========================================
# 1. CONFIGURAÇÕES E CSS "FORCE" (MOTO G30)
# ==========================================
st.set_page_config(
    page_title="Bear Snack PDV",
    page_icon="🐻",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Injeção de CSS que força 2 colunas e impede empilhamento
st.html("""
    <style>
        /* Ajuste do container principal */
        .block-container { 
            padding: 0.5rem 0.5rem 5rem 0.5rem !important; 
            max-width: 360px !important;
            margin: 0 auto;
        }

        /* FORÇA O MENU SUPERIOR EM 5 COLUNAS LADO A LADO */
        [data-testid="stHorizontalBlock"]:has(button[key="m1"]) {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            gap: 4px !important;
        }
        [data-testid="stHorizontalBlock"]:has(button[key="m1"]) [data-testid="column"] {
            width: 20% !important;
            min-width: 20% !important;
        }

        /* FORÇA OS BOTÕES DE PRODUTO EM 2 COLUNAS (IMPEDE O EMPILHAMENTO) */
        [data-testid="stHorizontalBlock"]:has(button[key^="btn_"]) {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            gap: 8px !important;
            margin-bottom: 8px !important;
        }
        [data-testid="stHorizontalBlock"]:has(button[key^="btn_"]) [data-testid="column"] {
            width: 50% !important;
            min-width: 50% !important;
        }

        /* ESTILO PROFISSIONAL DOS BOTÕES */
        div.stButton > button {
            width: 100% !important;
            border-radius: 10px !important;
            font-weight: bold !important;
            border: 1px solid #464855 !important;
            background: #262730 !important;
        }

        /* BOTÕES DE PRODUTO (ALTURA E TEXTO) */
        div.stButton > button[key^="btn_"] {
            height: 80px !important;
            font-size: 14px !important;
            white-space: pre-wrap !important;
            line-height: 1.2 !important;
            background: linear-gradient(145deg, #2e313c, #262730) !important;
        }

        /* BOTÃO DE CONFIRMAÇÃO */
        div.stButton > button[type="primary"] {
            height: 60px !important;
            background-color: #ff4b4b !important;
            font-size: 16px !important;
        }

        /* LIMPEZA DE INTERFACE */
        #MainMenu, header, footer { visibility: hidden; }
    </style>
""")

# ==========================================
# 2. BANCO DE DADOS
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
        # Garantir colunas para evitar erros de DatabaseError observados anteriormente
        try: cursor.execute("ALTER TABLE vendas ADD COLUMN baixada INTEGER DEFAULT 1")
        except: pass
        try: cursor.execute("ALTER TABLE vendas ADD COLUMN cliente_nome TEXT")
        except: pass
        try: cursor.execute("ALTER TABLE clientes ADD COLUMN saldo_devedor REAL DEFAULT 0.0")
        except: pass
        conn.commit()

iniciar_banco()

# ==========================================
# 3. ESTADO E LOGIN
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
# 4. MENU DE NAVEGAÇÃO (RESTAURADO)
# ==========================================
st.markdown(f"<p style='text-align:center; font-weight:bold;'>🐻 {st.session_state.pagina} PDV</p>", unsafe_allow_html=True)

m1, m2, m3, m4, m5 = st.columns(5)
if m1.button("🛒", key="m1"): st.session_state.pagina = "🛒"; st.rerun()
if m2.button("👥", key="m2"): st.session_state.pagina = "👥"; st.rerun()
if m3.button("🍱", key="m3"): st.session_state.pagina = "🍱"; st.rerun()
if m4.button("📜", key="m4"): st.session_state.pagina = "📜"; st.rerun()
if m5.button("📊", key="m5"): st.session_state.pagina = "📊"; st.rerun()

st.markdown("---")

# ==========================================
# 5. PÁGINAS
# ==========================================

if st.session_state.pagina == "🛒":
    # Nomes inteiros conforme solicitado para estética profissional
    atalhos = [
        ("SUCO", 6.0), ("REFRI", 6.0), 
        ("SALGADO", 8.0), ("PIPOCA", 7.0),
        ("SUCO NAT.", 8.0), ("P. QUEIJO", 7.0), 
        ("SANDUÍCHE", 8.0), ("BOLO", 9.0)
    ]
    
    # Criando as linhas de 2 colunas manualmente para forçar o layout
    for i in range(0, len(atalhos), 2):
        cols = st.columns(2)
        n1, p1 = atalhos[i]
        if cols[0].button(f"{n1}\nR${p1:.2f}", key=f"btn_{n1}"):
            st.session_state.desc_venda = n1
            st.session_state.valor_venda = p1
            st.rerun()
        
        if i + 1 < len(atalhos):
            n2, p2 = atalhos[i+1]
            if cols[1].button(f"{n2}\nR${p2:.2f}", key=f"btn_{n2}"):
                st.session_state.desc_venda = n2
                st.session_state.valor_venda = p2
                st.rerun()

    with st.container(border=True):
        v_item = st.text_input("Descrição", value=st.session_state.desc_venda)
        v_pre = st.number_input("Valor R$", value=st.session_state.valor_venda)
        v_mod = st.selectbox("Pagamento", ["DINHEIRO", "PIX", "CARTÃO", "FIADO"])
        
        v_cli = None
        if v_mod == "FIADO":
            with get_connection() as conn:
                clis = pd.read_sql_query("SELECT nome FROM clientes ORDER BY nome", conn)['nome'].tolist()
            v_cli = st.selectbox("Cliente", clis if clis else ["Sem Clientes"])
        
        if st.button("CONFIRMAR VENDA 🚀", use_container_width=True, type="primary"):
            agora = int(datetime.now().timestamp() * 1000)
            baixada = 0 if v_mod == "FIADO" else 1
            with get_connection() as conn:
                conn.execute("INSERT INTO vendas (data_ms, total, metodo, descricao_resumo, baixada, cliente_nome) VALUES (?,?,?,?,?,?)",
                            (agora, v_pre, v_mod, v_item, baixada, v_cli))
                if v_mod == "FIADO" and v_cli:
                    conn.execute("UPDATE clientes SET saldo_devedor = saldo_devedor + ? WHERE nome = ?", (v_pre, v_cli))
                conn.commit()
            st.success("Venda OK!")
            st.session_state.desc_venda = ""
            st.session_state.valor_venda = 0.0
            st.rerun()

elif st.session_state.pagina == "👥":
    st.write("### 👥 Gestão de Clientes")
    with st.expander("Cadastrar"):
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
    val_b = st.number_input("Valor", value=15.0)
    with get_connection() as conn:
        alunos = pd.read_sql_query("SELECT nome FROM clientes WHERE tipo='BANDEJA'", conn)['nome'].tolist()
    sel = []
    for a in alunos:
        if st.checkbox(a, key=f"chk_{a}"): sel.append(a)
    if st.button("LANÇAR SELECIONADOS", use_container_width=True, type="primary"):
        agora = int(datetime.now().timestamp() * 1000)
        with get_connection() as conn:
            for n in sel:
                conn.execute("INSERT INTO vendas (data_ms, total, metodo, descricao_resumo, baixada, cliente_nome) VALUES (?,?,?,?,0,?)", (agora, val_b, "FIADO", "BANDEJA", n))
                conn.execute("UPDATE clientes SET saldo_devedor = saldo_devedor + ? WHERE nome = ?", (val_b, n))
            conn.commit()
        st.rerun()

elif st.session_state.pagina == "📜":
    st.write("### 📜 Últimas Vendas")
    with get_connection() as conn:
        df_h = pd.read_sql_query("SELECT id, total, metodo, cliente_nome FROM vendas ORDER BY id DESC LIMIT 10", conn)
    st.dataframe(df_h, use_container_width=True, hide_index=True)

elif st.session_state.pagina == "📊":
    st.write("### 📊 Relatório")
    with get_connection() as conn:
        v = conn.execute("SELECT SUM(total) FROM vendas").fetchone()[0] or 0
        f = conn.execute("SELECT SUM(saldo_devedor) FROM clientes").fetchone()[0] or 0
    st.metric("Vendido", f"R${v:.2f}")
    st.metric("Pendente", f"R${f:.2f}")
    if st.button("SAIR"):
        st.session_state.autenticado = False
        st.rerun()
