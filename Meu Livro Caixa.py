import streamlit as st
import sqlite3
import pandas as pd
import urllib.parse
from datetime import datetime, timedelta
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import os

# ==========================================
# 1. CONFIGURAÇÕES E BANCO DE DADOS
# ==========================================
st.set_page_config(page_title="Bear Snack - Gestão", layout="wide")

def iniciar_banco():
    conn = sqlite3.connect('livro_caixa.db')
    cursor = conn.cursor()
    # Tabela de Vendas (unificada)
    cursor.execute('''CREATE TABLE IF NOT EXISTS vendas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data_ms INTEGER,
        total REAL,
        metodo TEXT,
        descricao_resumo TEXT,
        baixada INTEGER DEFAULT 1,
        cliente_nome TEXT
    )''')
    # Tabela de Clientes (com colunas do Flet)
    cursor.execute('''CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        tipo TEXT DEFAULT 'CLIENTE',
        telefone TEXT,
        documento TEXT,
        classe TEXT,
        periodo TEXT,
        limite REAL DEFAULT 0.0,
        saldo_devedor REAL DEFAULT 0.0
    )''')
    conn.commit()
    conn.close()

iniciar_banco()

# ==========================================
# 2. SISTEMA DE LOGIN
# ==========================================
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.title("🔒 Área Restrita - Bear Snack")
    senha = st.text_input("Digite a senha de acesso", type="password")
    if st.button("Entrar"):
        if senha == "Hillary2010":
            st.session_state.autenticado = True
            st.rerun()
        else:
            st.error("Senha incorreta!")
    st.stop()

# ==========================================
# 3. FUNÇÕES DE APOIO
# ==========================================
def listar_clientes():
    conn = sqlite3.connect('livro_caixa.db')
    df = pd.read_sql_query("SELECT * FROM clientes ORDER BY nome", conn)
    conn.close()
    return df

def registrar_venda(total, metodo, descricao, cliente_nome=None, baixada=1):
    conn = sqlite3.connect('livro_caixa.db')
    cur = conn.cursor()
    agora = int(datetime.now().timestamp() * 1000)
    cur.execute("""INSERT INTO vendas (data_ms, total, metodo, descricao_resumo, baixada, cliente_nome) 
                   VALUES (?,?,?,?,?,?)""", (agora, total, metodo, descricao, baixada, cliente_nome))
    if baixada == 0 and cliente_nome:
        cur.execute("UPDATE clientes SET saldo_devedor = saldo_devedor + ? WHERE nome = ?", (total, cliente_nome))
    conn.commit()
    conn.close()

# ==========================================
# 4. INTERFACE PRINCIPAL
# ==========================================
st.sidebar.title("🐻 Bear Snack")
menu = st.sidebar.radio("Navegação", ["PDV (Vender)", "Histórico de Vendas", "Caderneta (Clientes)", "Bandeja do Dia", "Relatórios"])

# ------------------------------------------
# ABA: PDV (VENDER)
# ------------------------------------------
if menu == "PDV (Vender)":
    st.header("🛒 Ponto de Venda")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Atalhos")
        atalhos = {
            "SUCO": 5.00, "FRUTA": 4.00, "REFRI": 6.00, "SALGADO": 8.00,
            "SUCO NAT.": 8.00, "PIPOCA": 7.00, "BISCOITO": 4.00, "P. QUEIJO": 7.00,
            "SANDUÍCHE": 8.00, "BOLO": 8.00
        }
        
        c_btn = st.columns(5)
        for i, (item, preco) in enumerate(atalhos.items()):
            if c_btn[i % 5].button(f"{item}\nR$ {preco:.2f}"):
                st.session_state.desc_venda = item
                st.session_state.valor_venda = preco

    with col2:
        st.subheader("Dados da Venda")
        desc = st.text_input("Descrição", value=st.session_state.get('desc_venda', ""))
        valor = st.number_input("Valor R$", min_value=0.0, value=st.session_state.get('valor_venda', 0.0), step=0.50)
        metodo = st.selectbox("Método de Pagamento", ["DINHEIRO", "PIX", "CARTÃO", "FIADO", "CRÉDITO"])
        
        cliente_nome = None
        if metodo in ["FIADO", "CRÉDITO"]:
            df_c = listar_clientes()
            cliente_nome = st.selectbox("Selecione o Cliente", df_c['nome'].tolist())

        if st.button("FINALIZAR VENDA", use_container_width=True):
            status_baixa = 0 if metodo in ["FIADO", "CRÉDITO"] else 1
            registrar_venda(valor, metodo, desc, cliente_nome, status_baixa)
            st.success("Venda registrada com sucesso!")
            if 'desc_venda' in st.session_state: del st.session_state.desc_venda
            if 'valor_venda' in st.session_state: del st.session_state.valor_venda

# ------------------------------------------
# ABA: HISTÓRICO DE VENDAS
# ------------------------------------------
elif menu == "Histórico de Vendas":
    st.header("📜 Histórico Recente")
    conn = sqlite3.connect('livro_caixa.db')
    query = "SELECT id, data_ms, total, metodo, descricao_resumo, cliente_nome FROM vendas ORDER BY data_ms DESC LIMIT 50"
    df_vendas = pd.read_sql_query(query, conn)
    conn.close()
    
    if not df_vendas.empty:
        df_vendas['Data'] = df_vendas['data_ms'].apply(lambda x: datetime.fromtimestamp(x/1000).strftime('%d/%m/%Y %H:%M'))
        st.dataframe(df_vendas[['Data', 'total', 'metodo', 'descricao_resumo', 'cliente_nome']], use_container_width=True)
        
        id_excluir = st.number_input("ID para excluir", min_value=0, step=1)
        if st.button("Excluir Registro"):
            conn = sqlite3.connect('livro_caixa.db')
            cur = conn.cursor()
            # Ajusta saldo se for venda não baixada
            venda = cur.execute("SELECT total, cliente_nome, baixada FROM vendas WHERE id=?", (id_excluir,)).fetchone()
            if venda and venda[2] == 0 and venda[1]:
                cur.execute("UPDATE clientes SET saldo_devedor = saldo_devedor - ? WHERE nome = ?", (venda[0], venda[1]))
            cur.execute("DELETE FROM vendas WHERE id=?", (id_excluir,))
            conn.commit()
            conn.close()
            st.rerun()

# ------------------------------------------
# ABA: CADERNETA (CLIENTES)
# ------------------------------------------
elif menu == "Caderneta (Clientes)":
    st.header("👥 Gestão de Caderneta")
    tab1, tab2 = st.tabs(["Lista de Devedores", "Novo Cadastro"])
    
    with tab1:
        df_c = listar_clientes()
        search = st.text_input("Pesquisar Cliente")
        if search:
            df_c = df_c[df_c['nome'].str.contains(search.upper())]
        
        st.dataframe(df_c[['nome', 'tipo', 'periodo', 'saldo_devedor', 'telefone']], use_container_width=True)
        
        sel_c = st.selectbox("Ações para Cliente:", df_c['nome'].tolist())
        c1, c2, c3 = st.columns(3)
        
        if c1.button("Quitar Dívida"):
            conn = sqlite3.connect('livro_caixa.db')
            cur = conn.cursor()
            cur.execute("UPDATE clientes SET saldo_devedor = 0 WHERE nome = ?", (sel_c,))
            cur.execute("UPDATE vendas SET baixada = 1 WHERE cliente_nome = ?", (sel_c,))
            conn.commit()
            conn.close()
            st.success(f"Dívida de {sel_c} zerada!")
            st.rerun()
            
        if c2.button("Enviar WhatsApp"):
            cli_data = df_c[df_c['nome'] == sel_c].iloc[0]
            msg = f"*BEAR SNACK*\nOlá {sel_c}, seu saldo pendente é R$ {cli_data['saldo_devedor']:.2f}"
            url = f"https://wa.me/{cli_data['telefone']}?text={urllib.parse.quote(msg)}"
            st.link_button("Abrir Conversa", url)

    with tab2:
        with st.form("form_cliente"):
            n_nome = st.text_input("Nome Completo").upper()
            n_tipo = st.selectbox("Tipo", ["CLIENTE", "ALUNO", "BANDEJA"])
            n_tel = st.text_input("Telefone (Ex: 5511999999999)")
            n_per = st.selectbox("Período", ["MANHÃ", "TARDE"])
            if st.form_submit_button("Cadastrar"):
                conn = sqlite3.connect('livro_caixa.db')
                cur = conn.cursor()
                cur.execute("INSERT INTO clientes (nome, tipo, telefone, periodo) VALUES (?,?,?,?)", (n_nome, n_tipo, n_tel, n_per))
                conn.commit()
                conn.close()
                st.success("Cadastrado!")
                st.rerun()

# ------------------------------------------
# ABA: BANDEJA DO DIA
# ------------------------------------------
elif menu == "Bandeja do Dia":
    st.header("🍱 Consumo em Massa (Bandeja)")
    
    cardapio = st.text_area("Cardápio do Dia")
    valor_b = st.number_input("Valor da Bandeja R$", min_value=0.0, step=1.0)
    
    df_c = listar_clientes()
    lista_bandeja = df_c[df_c['tipo'] == 'BANDEJA']['nome'].tolist()
    
    st.write("Quem consumiu hoje?")
    selecionados = []
    col_b = st.columns(3)
    for i, nome in enumerate(lista_bandeja):
        if col_b[i % 3].checkbox(nome, key=f"chk_{nome}"):
            selecionados.append(nome)
            
    if st.button("Confirmar Consumo para Todos", use_container_width=True):
        if selecionados and valor_b > 0:
            for nome in selecionados:
                registrar_venda(valor_b, "FIADO", f"BANDEJA: {cardapio[:30]}", nome, 0)
            st.success(f"Registrado para {len(selecionados)} pessoas!")
        else:
            st.error("Selecione os clientes e defina o valor.")

# ------------------------------------------
# ABA: RELATÓRIOS
# ------------------------------------------
elif menu == "Relatórios":
    st.header("📊 Relatórios e Backups")
    
    c1, c2 = st.columns(2)
    
    with c1:
        if st.button("Exportar Backup Excel"):
            conn = sqlite3.connect('livro_caixa.db')
            df_v = pd.read_sql_query("SELECT * FROM vendas", conn)
            df_cl = pd.read_sql_query("SELECT * FROM clientes", conn)
            conn.close()
            
            with pd.ExcelWriter("Backup_BearSnack.xlsx") as writer:
                df_v.to_excel(writer, sheet_name="Vendas")
                df_cl.to_excel(writer, sheet_name="Clientes")
            
            with open("Backup_BearSnack.xlsx", "rb") as f:
                st.download_button("Baixar Arquivo Excel", f, "Backup_BearSnack.xlsx")

    with c2:
        if st.button("Gerar Relatório PDF (Resumo)"):
            conn = sqlite3.connect('livro_caixa.db')
            cur = conn.cursor()
            total = cur.execute("SELECT SUM(total) FROM vendas").fetchone()[0] or 0
            vendas = cur.execute("SELECT data_ms, total, metodo FROM vendas ORDER BY id DESC LIMIT 20").fetchall()
            conn.close()

            c = canvas.Canvas("Relatorio_Simples.pdf", pagesize=A4)
            c.drawString(100, 800, "RELATÓRIO BEAR SNACK")
            y = 750
            for v in vendas:
                dt = datetime.fromtimestamp(v[0]/1000).strftime('%d/%m %H:%M')
                c.drawString(100, y, f"{dt} - R$ {v[1]:.2f} ({v[2]})")
                y -= 20
            c.drawString(100, y-20, f"TOTAL ACUMULADO: R$ {total:.2f}")
            c.save()
            st.success("PDF Gerado no servidor!")

st.sidebar.divider()
st.sidebar.write(f"Usuário: Sebas")
