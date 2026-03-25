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

# CSS PROFISSIONAL: BOTÕES COM MELHOR PROPORÇÃO E TEXTO INTEIRO
st.markdown("""
    <style>
        /* Trava a largura e centraliza o app */
        .main {
            max-width: 360px !important;
            margin: 0 auto;
        }

        /* Ajuste de respiro lateral */
        .block-container { 
            padding: 0.5rem 0.3rem 5rem 0.3rem !important; 
            max-width: 360px !important;
        }
        
        /* MENU SUPERIOR: GRID 1x5 */
        [data-testid="stHorizontalBlock"] {
            display: grid !important;
            grid-template-columns: repeat(5, 1fr) !important;
            gap: 4px !important;
            width: 100% !important;
            margin-bottom: 10px !important;
        }
        
        [data-testid="column"] {
            width: 100% !important;
            flex: none !important;
            min-width: 0px !important;
            padding: 0px !important;
        }

        /* ESTILO DOS BOTÕES DO MENU (SUPERIOR) */
        [data-testid="column"] div.stButton > button {
            border-radius: 8px;
            height: 55px !important; 
            width: 100% !important;
            font-size: 22px !important; 
            background-color: #262730;
            border: 1px solid #464855;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        /* BOTÕES DE PRODUTOS (MAIS ALTOS E PROFISSIONAIS) */
        /* Alvo: botões dentro da grade de produtos do PDV */
        div.stButton > button[key^="btn_"] {
            height: 85px !important; /* Aumentado para não ficar achatado */
            border-radius: 10px !important;
            font-size: 15px !important;
            font-weight: 600 !important;
            line-height: 1.3 !important;
            background: linear-gradient(145deg, #2e313c, #262730) !important;
            border: 1px solid #464855 !important;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.2) !important;
            white-space: pre-wrap !important; /* Permite quebra de linha entre nome e preço */
        }

        /* ESTILO DO BOTÃO DE CONFIRMAÇÃO */
        div.stButton > button[type="primary"] {
            height: 60px !important;
            font-size: 18px !important;
            font-weight: bold !important;
            letter-spacing: 1px !important;
        }

        /* CORES DE INTERAÇÃO */
        div.stButton > button:active {
            background-color: #ff4b4b !important;
            transform: scale(0.98);
        }

        /* ESCONDER ELEMENTOS NATIVOS */
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        footer {visibility: hidden;}
        
        .app-header {
            font-size: 16px !important;
            font-weight: bold;
            text-align: center;
            margin-bottom: 8px;
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
# 4. MENU DE NAVEGAÇÃO SUPERIOR
# ==========================================
st.markdown(f"<p class='app-header'>🐻 Bear Snack | {st.session_state.pagina}</p>", unsafe_allow_html=True)

m1, m2, m3, m4, m5 = st.columns(5)
if m1.button("🛒"): st.session_state.pagina = "🛒"; st.rerun()
if m2.button("👥"): st.session_state.pagina = "👥"; st.rerun()
if m3.button("🍱"): st.session_state.pagina = "🍱"; st.rerun()
if m4.button("📜"): st.session_state.pagina = "📜"; st.rerun()
if m5.button("📊"): st.session_state.pagina = "📊"; st.rerun()

st.markdown("<hr style='margin:5px 0; border-color: #464855;'>", unsafe_allow_html=True)

# ==========================================
# 5. CONTEÚDO DAS PÁGINAS
# ==========================================

# --- TELA: PDV ---
if st.session_state.pagina == "🛒":
    # Nomes inteiros conforme solicitado
    atalhos = {
        "SUCO": 6.0, "REFRI": 6.0, "SALGADO": 8.0, "PIPOCA": 7.0,
        "SUCO NAT.": 8.0, "P. QUEIJO": 7.0, "SANDUÍCHE": 8.0, "BOLO": 9.0
    }
    
    grid = st.columns(2)
    for i, (item, preco) in enumerate(atalhos.items()):
        # \n força o preço para a linha de baixo, melhorando a estética do botão alto
        if grid[i % 2].button(f"{item}\nR${preco:.2f}", key=f"btn_{item}", use_container_width=True):
            st.session_state.desc_venda = item
            st.session_state.valor_venda = preco
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    with st.container(border=True):
        v_item = st.text_input("Descrição do Item", value=st.session_state.desc_venda)
        v_pre = st.number_input("Valor Unitário (R$)", value=st.session_state.valor_venda, step=0.5)
        v_mod = st.selectbox("Forma de Pagamento", ["DINHEIRO", "PIX", "CARTÃO", "FIADO"])
        
        v_cli = None
        if v_mod == "FIADO":
            with get_connection() as conn:
                clis = pd.read_sql_query("SELECT nome FROM clientes ORDER BY nome", conn)['nome'].tolist()
            v_cli = st.selectbox("Selecionar Cliente", clis if clis else ["Nenhum cliente cadastrado"])
        
        if st.button("CONFIRMAR VENDA 🚀", use_container_width=True, type="primary"):
            if v_mod == "FIADO" and (not v_cli or v_cli == "Nenhum cliente cadastrado"):
                st.error("Selecione um cliente para fiado!")
            else:
                agora = int(datetime.now().timestamp() * 1000)
                baixada = 0 if v_mod == "FIADO" else 1
                with get_connection() as conn:
                    conn.execute("INSERT INTO vendas (data_ms, total, metodo, descricao_resumo, baixada, cliente_nome) VALUES (?,?,?,?,?,?)",
                                (agora, v_pre, v_mod, v_item, baixada, v_cli))
                    if v_mod == "FIADO" and v_cli:
                        conn.execute("UPDATE clientes SET saldo_devedor = saldo_devedor + ? WHERE nome = ?", (v_pre, v_cli))
                    conn.commit()
                st.success("Venda registrada!")
                st.session_state.desc_venda = ""
                st.session_state.valor_venda = 0.0
                st.rerun()

# --- TELA: CADERNETA ---
elif st.session_state.pagina == "👥":
    st.write("### 👥 Gestão de Clientes")
    with st.expander("➕ Cadastrar Novo Cliente"):
        n = st.text_input("Nome do Cliente").upper()
        if st.button("SALVAR CADASTRO", use_container_width=True):
            if n:
                try:
                    with get_connection() as conn:
                        conn.execute("INSERT INTO clientes (nome, tipo) VALUES (?, 'ALUNO')", (n,))
                    st.success("Cliente cadastrado!"); st.rerun()
                except: st.error("Nome já existe!")
    
    with get_connection() as conn:
        df_cli = pd.read_sql_query("SELECT nome, saldo_devedor FROM clientes WHERE saldo_devedor > 0 ORDER BY saldo_devedor DESC", conn)
    st.dataframe(df_cli, use_container_width=True, hide_index=True)

# --- TELA: BANDEJA ---
elif st.session_state.pagina == "🍱":
    st.write("### 🍱 Lançamento de Bandeja")
    val_b = st.number_input("Valor da Bandeja R$", value=15.0)
    with get_connection() as conn:
        alunos = pd.read_sql_query("SELECT nome FROM clientes WHERE tipo='BANDEJA'", conn)['nome'].tolist()
    
    sel = []
    if alunos:
        for a in alunos:
            if st.checkbox(a, key=f"chk_{a}"): sel.append(a)
        
        if st.button("LANÇAR SELECIONADOS", use_container_width=True, type="primary"):
            agora = int(datetime.now().timestamp() * 1000)
            with get_connection() as conn:
                for n in sel:
                    conn.execute("INSERT INTO vendas (data_ms, total, metodo, descricao_resumo, baixada, cliente_nome) VALUES (?,?,?,?,0,?)", (agora, val_b, "FIADO", "BANDEJA", n))
                    conn.execute("UPDATE clientes SET saldo_devedor = saldo_devedor + ? WHERE nome = ?", (val_b, n))
                conn.commit()
            st.success("Bandejas lançadas!"); st.rerun()
    else:
        st.info("Nenhum cliente do tipo 'BANDEJA' encontrado.")

# --- TELA: HISTÓRICO ---
elif st.session_state.pagina == "📜":
    st.write("### 📜 Últimas Movimentações")
    with get_connection() as conn:
        df_h = pd.read_sql_query("SELECT id, total, metodo, cliente_nome FROM vendas ORDER BY id DESC LIMIT 15", conn)
    st.dataframe(df_h, use_container_width=True, hide_index=True)

# --- TELA: RELATÓRIOS ---
elif st.session_state.pagina == "📊":
    st.write("### 📊 Resumo Financeiro")
    with get_connection() as conn:
        v_total = conn.execute("SELECT SUM(total) FROM vendas").fetchone()[0] or 0
        f_total = conn.execute("SELECT SUM(saldo_devedor) FROM clientes").fetchone()[0] or 0
    
    c1, c2 = st.columns(2)
    c1.metric("Total Geral", f"R${v_total:.2f}")
    c2.metric("Pendente (Fiado)", f"R${f_total:.2f}")
    
    st.markdown("---")
    if st.button("LOGOUT (SAIR)", use_container_width=True):
        st.session_state.autenticado = False
        st.rerun()
