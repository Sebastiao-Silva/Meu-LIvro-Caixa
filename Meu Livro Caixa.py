import streamlit as st
import sqlite3
import pandas as pd
import urllib.parse
import os
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

# ==========================================
# 1. CONFIGURAÇÕES INICIAIS (ESSENCIAL PARA DEPLOY)
# ==========================================
st.set_page_config(
    page_title="Bear Snack - Sistema de Cantina",
    page_icon="🐻",
    layout="wide"
)

# Inicialização de estados do Streamlit para evitar erros de recarregamento
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
if 'desc_venda' not in st.session_state:
    st.session_state.desc_venda = ""
if 'valor_venda' not in st.session_state:
    st.session_state.valor_venda = 0.0

# ==========================================
# 2. BANCO DE DADOS (SQLite com Path Dinâmico)
# ==========================================
DB_PATH = 'livro_caixa.db'

def iniciar_banco():
    conn = sqlite3.connect(DB_PATH)
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
        documento TEXT,
        classe TEXT,
        periodo TEXT,
        saldo_devedor REAL DEFAULT 0.0
    )''')
    conn.commit()
    conn.close()

iniciar_banco()

# ==========================================
# 3. FUNÇÕES DE NEGÓCIO
# ==========================================
def get_connection():
    return sqlite3.connect(DB_PATH)

def listar_clientes():
    with get_connection() as conn:
        return pd.read_sql_query("SELECT * FROM clientes ORDER BY nome", conn)

def registrar_venda(total, metodo, descricao, cliente_nome=None, baixada=1):
    with get_connection() as conn:
        cur = conn.cursor()
        agora = int(datetime.now().timestamp() * 1000)
        cur.execute("""INSERT INTO vendas (data_ms, total, metodo, descricao_resumo, baixada, cliente_nome) 
                       VALUES (?,?,?,?,?,?)""", (agora, total, metodo, descricao, baixada, cliente_nome))
        if baixada == 0 and cliente_nome:
            cur.execute("UPDATE clientes SET saldo_devedor = saldo_devedor + ? WHERE nome = ?", (total, cliente_nome))
        conn.commit()

# ==========================================
# 4. SISTEMA DE ACESSO
# ==========================================
if not st.session_state.autenticado:
    st.markdown("<h1 style='text-align: center;'>🐻 Bear Snack Admin</h1>", unsafe_allow_html=True)
    col_login, _ = st.columns([1, 2])
    with col_login:
        senha = st.text_input("Senha de Acesso", type="password")
        if st.button("Entrar", use_container_width=True):
            if senha == "Hillary2010":
                st.session_state.autenticado = True
                st.rerun()
            else:
                st.error("Senha incorreta!")
    st.stop()

# ==========================================
# 5. INTERFACE (SIDEBAR E NAVEGAÇÃO)
# ==========================================
st.sidebar.image("logo.png", width=150) if os.path.exists("logo.png") else st.sidebar.title("🐻 Bear Snack")
st.sidebar.markdown("---")
menu = st.sidebar.radio("Navegação", ["🛒 PDV", "👥 Caderneta", "🍱 Bandeja", "📜 Histórico", "📊 Relatórios"])

# ------------------------------------------
# ABA: PDV (PONTO DE VENDA)
# ------------------------------------------
if menu == "🛒 PDV":
    st.header("Ponto de Venda")
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Atalhos Rápidos")
        atalhos = {
            "SUCO": 5.0, "FRUTA": 4.0, "REFRI": 6.0, "SALGADO": 8.0,
            "SUCO NAT.": 8.0, "PIPOCA": 7.0, "BISCOITO": 4.0, "P. QUEIJO": 7.0,
            "SANDUÍCHE": 8.0, "BOLO": 8.0
        }
        
        c_atalho = st.columns(4)
        for i, (item, preco) in enumerate(atalhos.items()):
            if c_atalho[i % 4].button(f"{item}\nR$ {preco:.2f}", key=f"btn_{item}", use_container_width=True):
                st.session_state.desc_venda = item
                st.session_state.valor_venda = preco
                st.rerun()

    with col2:
        st.subheader("Finalizar Venda")
        with st.container(border=True):
            desc = st.text_input("Descrição", value=st.session_state.desc_venda)
            valor = st.number_input("Valor R$", min_value=0.0, value=st.session_state.valor_venda, step=0.5)
            metodo = st.selectbox("Forma de Pagamento", ["DINHEIRO", "PIX", "CARTÃO", "FIADO", "CRÉDITO"])
            
            cliente_nome = None
            if metodo in ["FIADO", "CRÉDITO"]:
                clientes_list = listar_clientes()['nome'].tolist()
                cliente_nome = st.selectbox("Selecione o Devedor", clientes_list)

            if st.button("CONFIRMAR VENDA", use_container_width=True, type="primary"):
                status_baixa = 0 if metodo in ["FIADO", "CRÉDITO"] else 1
                registrar_venda(valor, metodo, desc, cliente_nome, status_baixa)
                st.success("Registrado!")
                st.session_state.desc_venda = ""
                st.session_state.valor_venda = 0.0
                st.rerun()

# ------------------------------------------
# ABA: CADERNETA (CLIENTES)
# ------------------------------------------
elif menu == "👥 Caderneta":
    st.header("Controle de Clientes (Caderneta)")
    t1, t2 = st.tabs(["Listagem e Cobrança", "Novo Cadastro"])
    
    with t1:
        df_c = listar_clientes()
        filtro = st.text_input("🔍 Buscar Cliente (Nome)").upper()
        if filtro:
            df_c = df_c[df_c['nome'].str.contains(filtro)]
        
        st.dataframe(df_c[['nome', 'tipo', 'saldo_devedor', 'telefone', 'periodo']], use_container_width=True)
        
        if not df_c.empty:
            sel_nome = st.selectbox("Ação rápida para:", df_c['nome'].tolist())
            c1, c2 = st.columns(2)
            
            if c1.button("Quitar Dívida Total", use_container_width=True):
                with get_connection() as conn:
                    conn.execute("UPDATE clientes SET saldo_devedor = 0 WHERE nome = ?", (sel_nome,))
                    conn.execute("UPDATE vendas SET baixada = 1 WHERE cliente_nome = ?", (sel_nome,))
                st.success(f"Dívida de {sel_nome} paga!")
                st.rerun()
                
            if c2.button("Cobrar via WhatsApp", use_container_width=True):
                dados = df_c[df_c['nome'] == sel_nome].iloc[0]
                msg = f"*BEAR SNACK*\nOlá {sel_nome}! Passando para informar seu saldo pendente: *R$ {dados['saldo_devedor']:.2f}*."
                st.link_button("Abrir WhatsApp", f"https://wa.me/{dados['telefone']}?text={urllib.parse.quote(msg)}")

    with t2:
        with st.form("cadastro_cliente"):
            st.write("Dados Pessoais")
            c_nome = st.text_input("Nome Completo").upper()
            c_tipo = st.selectbox("Categoria", ["ALUNO", "FUNCIONÁRIO", "BANDEJA", "OUTROS"])
            c_tel = st.text_input("WhatsApp (ex: 5511999998888)")
            c_per = st.selectbox("Período", ["MANHÃ", "TARDE", "INTEGRAL"])
            if st.form_submit_button("Salvar Cadastro"):
                try:
                    with get_connection() as conn:
                        conn.execute("INSERT INTO clientes (nome, tipo, telefone, periodo) VALUES (?,?,?,?)", (c_nome, c_tipo, c_tel, c_per))
                    st.success("Cadastrado com sucesso!")
                except:
                    st.error("Erro: Este nome já existe no sistema.")

# ------------------------------------------
# ABA: BANDEJA (CONSUMO EM MASSA)
# ------------------------------------------
elif menu == "🍱 Bandeja":
    st.header("Consumo Bandeja (Diário)")
    st.info("Lance o valor para vários alunos ao mesmo tempo.")
    
    cardapio_txt = st.text_input("O que foi servido hoje?")
    valor_bandeja = st.number_input("Preço da Bandeja R$", min_value=0.0, value=15.0)
    
    df_all = listar_clientes()
    lista_bandeja = df_all[df_all['tipo'] == 'BANDEJA']['nome'].tolist()
    
    if not lista_bandeja:
        st.warning("Nenhum cliente cadastrado com o tipo 'BANDEJA'.")
    else:
        selecionados = []
        cols = st.columns(4)
        for i, nome in enumerate(lista_bandeja):
            if cols[i % 4].checkbox(nome):
                selecionados.append(nome)
        
        if st.button("Lançar Dívida para Selecionados", type="primary"):
            if selecionados:
                for n in selecionados:
                    registrar_venda(valor_bandeja, "FIADO", f"BANDEJA: {cardapio_txt}", n, 0)
                st.success(f"Lançado para {len(selecionados)} clientes!")
            else:
                st.error("Ninguém selecionado.")

# ------------------------------------------
# ABA: HISTÓRICO (COM TRATAMENTO DE ERRO)
# ------------------------------------------
elif menu == "📜 Histórico":
    st.header("Últimas Movimentações")
    
    try:
        with get_connection() as conn:
            df_v = pd.read_sql_query("SELECT * FROM vendas ORDER BY id DESC LIMIT 100", conn)
        
        if not df_v.empty:
            # Garanta que a coluna data_ms existe antes de converter
            df_v['Data'] = df_v['data_ms'].apply(lambda x: datetime.fromtimestamp(x/1000).strftime('%d/%m %H:%M'))
            st.dataframe(df_v[['id', 'Data', 'total', 'metodo', 'descricao_resumo', 'cliente_nome']], use_container_width=True)
        else:
            st.info("O banco de dados está sendo inicializado ou está vazio. Faça uma venda no PDV primeiro!")
    except Exception as e:
        # Se der erro, ele mostra o aviso amarelo, mas NÃO a lista de métodos
        st.warning("Aguardando registros no banco de dados...")
# ------------------------------------------
# ABA: RELATÓRIOS E EXPORTAÇÃO
# ------------------------------------------
elif menu == "📊 Relatórios":
    st.header("Relatórios de Gestão")
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Exportar Dados")
        if st.button("Gerar Planilha Excel"):
            with get_connection() as conn:
                v = pd.read_sql_query("SELECT * FROM vendas", conn)
                c = pd.read_sql_query("SELECT * FROM clientes", conn)
            
            with pd.ExcelWriter("Gestao_BearSnack.xlsx") as writer:
                v.to_excel(writer, sheet_name="Vendas")
                c.to_excel(writer, sheet_name="Clientes")
            
            with open("Gestao_BearSnack.xlsx", "rb") as f:
                st.download_button("Baixar Excel", f, "Gestao_BearSnack.xlsx")

    with c2:
        st.subheader("Resumo Financeiro")
        with get_connection() as conn:
            tot_vendas = conn.execute("SELECT SUM(total) FROM vendas").fetchone()[0] or 0
            tot_devedor = conn.execute("SELECT SUM(saldo_devedor) FROM clientes").fetchone()[0] or 0
        
        st.metric("Total em Vendas", f"R$ {tot_vendas:.2f}")
        st.metric("Total a Receber (Fiado)", f"R$ {tot_devedor:.2f}")

st.sidebar.markdown("---")
st.sidebar.caption(f"Bear Snack v2.0 | Logado como: Sebas")
