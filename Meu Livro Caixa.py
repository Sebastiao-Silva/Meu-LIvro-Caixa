import streamlit as st
import sqlite3
import pandas as pd
import urllib.parse
import os
from datetime import datetime

# ==========================================
# 1. CONFIGURAÇÕES DA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Bear Snack - Gestão de Cantina",
    page_icon="🐻",
    layout="wide"
)

# Inicialização de variáveis de estado (Session State)
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
if 'desc_venda' not in st.session_state:
    st.session_state.desc_venda = ""
if 'valor_venda' not in st.session_state:
    st.session_state.valor_venda = 0.0

# ==========================================
# 2. BANCO DE DADOS (SQLite com Auto-Migração)
# ==========================================
DB_NAME = 'livro_caixa.db'

def get_connection():
    return sqlite3.connect(DB_NAME)

def iniciar_banco():
    """Cria as tabelas e garante que as colunas novas existam."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Criar Tabela de Vendas se não existir
    cursor.execute('''CREATE TABLE IF NOT EXISTS vendas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data_ms INTEGER,
        total REAL,
        metodo TEXT,
        descricao_resumo TEXT
    )''')
    
    # MIGRACAO: Adicionar colunas novas caso a tabela já existisse antes
    try:
        cursor.execute("ALTER TABLE vendas ADD COLUMN baixada INTEGER DEFAULT 1")
    except:
        pass # Coluna já existe
        
    try:
        cursor.execute("ALTER TABLE vendas ADD COLUMN cliente_nome TEXT")
    except:
        pass # Coluna já existe

    # Criar Tabela de Clientes
    cursor.execute('''CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL UNIQUE,
        tipo TEXT DEFAULT 'CLIENTE',
        telefone TEXT,
        documento TEXT,
        classe TEXT,
        periodo TEXT,
        saldo_devedor REAL DEFAULT 0.0
    )''')
    
    conn.commit()
    conn.close()

# Executa a inicialização/migração
iniciar_banco()

# ==========================================
# 3. SISTEMA DE LOGIN
# ==========================================
if not st.session_state.autenticado:
    st.markdown("<h1 style='text-align: center;'>🐻 Bear Snack Admin</h1>", unsafe_allow_html=True)
    col_l, col_r = st.columns([1, 2])
    with col_l:
        senha = st.text_input("Senha de Acesso", type="password")
        if st.button("Entrar", use_container_width=True):
            if senha == "Hillary2010":
                st.session_state.autenticado = True
                st.rerun()
            else:
                st.error("Senha incorreta!")
    st.stop()

# ==========================================
# 4. BARRA LATERAL
# ==========================================
if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", width=150)
else:
    st.sidebar.title("🐻 Bear Snack")

st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "Navegação", 
    ["🛒 PDV", "👥 Caderneta", "🍱 Bandeja", "📜 Histórico", "📊 Relatórios"]
)

st.sidebar.markdown("---")
st.sidebar.caption(f"Usuário: Sebas | v2.2")

# ==========================================
# 5. LÓGICA DAS ABAS
# ==========================================

# --- ABA: PDV ---
if menu == "🛒 PDV":
    st.header("Ponto de Venda")
    c1, c2 = st.columns([2, 1])
    
    with c1:
        st.subheader("Atalhos")
        atalhos = {
            "SUCO": 5.0, "FRUTA": 4.0, "REFRI": 6.0, "SALGADO": 8.0,
            "SUCO NAT.": 8.0, "PIPOCA": 7.0, "BISCOITO": 4.0, "P. QUEIJO": 7.0,
            "SANDUÍCHE": 8.0, "BOLO": 8.0
        }
        cols_at = st.columns(4)
        for i, (item, preco) in enumerate(atalhos.items()):
            if cols_at[i % 4].button(f"{item}\nR$ {preco:.2f}", key=f"pdv_{item}", use_container_width=True):
                st.session_state.desc_venda = item
                st.session_state.valor_venda = preco
                st.rerun()

    with c2:
        st.subheader("Finalizar")
        with st.container(border=True):
            desc = st.text_input("Descrição", value=st.session_state.desc_venda)
            valor = st.number_input("Preço R$", min_value=0.0, value=st.session_state.valor_venda)
            metodo = st.selectbox("Pagamento", ["DINHEIRO", "PIX", "CARTÃO", "FIADO"])
            
            cliente_venda = None
            lista_c = []
            if metodo == "FIADO":
                with get_connection() as conn:
                    df_cli = pd.read_sql_query("SELECT nome FROM clientes", conn)
                    lista_c = df_cli['nome'].tolist()
                cliente_venda = st.selectbox("Selecione o Cliente", lista_c if lista_c else ["Nenhum cliente cadastrado"])

            if st.button("CONFIRMAR", use_container_width=True, type="primary"):
                if metodo == "FIADO" and not lista_c:
                    st.error("Cadastre um cliente primeiro!")
                else:
                    agora = int(datetime.now().timestamp() * 1000)
                    baixada = 0 if metodo == "FIADO" else 1
                    
                    with get_connection() as conn:
                        cur = conn.cursor()
                        # INSERT CORRIGIDO COM 6 COLUNAS
                        cur.execute("""
                            INSERT INTO vendas (data_ms, total, metodo, descricao_resumo, baixada, cliente_nome) 
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (agora, valor, metodo, desc, baixada, cliente_venda))
                        
                        if metodo == "FIADO" and cliente_venda:
                            cur.execute("UPDATE clientes SET saldo_devedor = saldo_devedor + ? WHERE nome = ?", (valor, cliente_venda))
                        conn.commit()
                    
                    st.success("Venda Realizada!")
                    st.session_state.desc_venda = ""
                    st.session_state.valor_venda = 0.0
                    st.rerun()

# --- ABA: CADERNETA ---
elif menu == "👥 Caderneta":
    st.header("Clientes e Débitos")
    tab1, tab2 = st.tabs(["Listagem", "Novo Cadastro"])
    
    with tab1:
        with get_connection() as conn:
            df_c = pd.read_sql_query("SELECT nome, tipo, saldo_devedor, telefone FROM clientes", conn)
        st.dataframe(df_c, use_container_width=True)
    
    with tab2:
        with st.form("novo_cliente"):
            n_nome = st.text_input("Nome").upper()
            n_tipo = st.selectbox("Tipo", ["ALUNO", "FUNCIONÁRIO", "BANDEJA"])
            n_tel = st.text_input("Telefone (WhatsApp)")
            if st.form_submit_button("Salvar Cadastro"):
                if n_nome:
                    try:
                        with get_connection() as conn:
                            conn.execute("INSERT INTO clientes (nome, tipo, telefone) VALUES (?,?,?)", (n_nome, n_tipo, n_tel))
                        st.success("Cliente cadastrado!")
                        st.rerun()
                    except:
                        st.error("Este nome já existe.")
                else:
                    st.warning("Preencha o nome.")

# --- ABA: BANDEJA ---
elif menu == "🍱 Bandeja":
    st.header("Lançamento de Bandeja (Em Massa)")
    valor_b = st.number_input("Valor Unitário R$", value=15.0)
    
    with get_connection() as conn:
        alunos = pd.read_sql_query("SELECT nome FROM clientes WHERE tipo='BANDEJA'", conn)['nome'].tolist()
    
    if not alunos:
        st.info("Cadastre clientes com o tipo 'BANDEJA' para usar esta função.")
    else:
        selecionados = []
        st.write("Selecione quem consumiu hoje:")
        c_b = st.columns(4)
        for i, nome in enumerate(alunos):
            if c_b[i % 4].checkbox(nome):
                selecionados.append(nome)
            
        if st.button("Lançar Dívida para Selecionados", type="primary"):
            if selecionados:
                agora = int(datetime.now().timestamp() * 1000)
                with get_connection() as conn:
                    for n in selecionados:
                        conn.execute("""
                            INSERT INTO vendas (data_ms, total, metodo, descricao_resumo, baixada, cliente_nome) 
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (agora, valor_b, "FIADO", "BANDEJA DIÁRIA", 0, n))
                        conn.execute("UPDATE clientes SET saldo_devedor = saldo_devedor + ? WHERE nome = ?", (valor_b, n))
                    conn.commit()
                st.success(f"Lançado para {len(selecionados)} pessoas!")
            else:
                st.warning("Ninguém selecionado.")

# --- ABA: HISTÓRICO ---
elif menu == "📜 Histórico":
    st.header("Histórico Recente")
    try:
        with get_connection() as conn:
            df_v = pd.read_sql_query("SELECT * FROM vendas ORDER BY id DESC LIMIT 50", conn)
        
        if not df_v.empty:
            # Converter timestamp para data legível
            df_v['Data'] = df_v['data_ms'].apply(lambda x: datetime.fromtimestamp(x/1000).strftime('%d/%m %H:%M'))
            # Exibir tabela limpa
            cols = ['id', 'Data', 'total', 'metodo', 'descricao_resumo', 'cliente_nome']
            st.dataframe(df_v[cols], use_container_width=True)
            
            # Opção de Excluir
            with st.expander("🗑️ Excluir Registro"):
                id_excluir = st.number_input("ID da venda", min_value=0, step=1)
                if st.button("Confirmar Exclusão"):
                    with get_connection() as conn:
                        conn.execute("DELETE FROM vendas WHERE id=?", (id_excluir,))
                        conn.commit()
                    st.rerun()
        else:
            st.info("Nenhuma venda registrada ainda.")
    except Exception as e:
        st.error(f"Erro ao carregar banco: {e}")

# --- ABA: RELATÓRIOS ---
elif menu == "📊 Relatórios":
    st.header("Resumo Financeiro")
    with get_connection() as conn:
        res_vendas = pd.read_sql_query("SELECT SUM(total) as Total FROM vendas", conn)
        res_fiado = pd.read_sql_query("SELECT SUM(saldo_devedor) as Total FROM clientes", conn)
    
    c1, c2 = st.columns(2)
    c1.metric("Faturamento Total", f"R$ {res_vendas['Total'][0] or 0:.2f}")
    c2.metric("Total em Aberto (Fiado)", f"R$ {res_fiado['Total'][0] or 0:.2f}")
