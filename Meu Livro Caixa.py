import streamlit as st
import sqlite3
from datetime import datetime

# ==========================================
# 1. BANCO DE DADOS
# ==========================================
def iniciar_banco():
    conn = sqlite3.connect('livro_caixa.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS vendas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data_ms INTEGER,
        total REAL,
        metodo TEXT,
        descricao_resumo TEXT,
        cliente_id INTEGER
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        perfil TEXT,
        contato TEXT,
        limite REAL DEFAULT 0.0,
        saldo_devedor REAL DEFAULT 0.0
    )''')
    conn.commit()
    conn.close()

iniciar_banco()

# ==========================================
# 2. INTERFACE STREAMLIT
# ==========================================
st.title("📒 Livro Caixa - Bear Snack")

menu = st.sidebar.radio("Navegação", ["Início", "Clientes", "Vendas"])

if menu == "Início":
    st.write("Bem-vindo ao sistema de Livro Caixa!")

elif menu == "Clientes":
    st.subheader("Lista de Clientes")
    conn = sqlite3.connect('livro_caixa.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM clientes")
    dados = cur.fetchall()
    conn.close()
    for c in dados:
        st.write(f"**{c[1]}** - Perfil: {c[2]} - Dívida: R$ {c[5]:.2f}")

    st.subheader("Adicionar Cliente")
    nome = st.text_input("Nome")
    perfil = st.selectbox("Perfil", ["ALUNO", "FUNCIONÁRIO", "CLIENTE"])
    contato = st.text_input("Contato")
    limite = st.number_input("Limite de Crédito", min_value=0.0)
    if st.button("Salvar Cliente"):
        conn = sqlite3.connect('livro_caixa.db')
        cur = conn.cursor()
        cur.execute("INSERT INTO clientes (nome, perfil, contato, limite) VALUES (?,?,?,?)",
                    (nome, perfil, contato, limite))
        conn.commit()
        conn.close()
        st.success("Cliente adicionado com sucesso!")

elif menu == "Vendas":
    st.subheader("Registro de Vendas")
    conn = sqlite3.connect('livro_caixa.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM vendas")
    dados = cur.fetchall()
    conn.close()
    for v in dados:
        dt = datetime.fromtimestamp(v[1]/1000).strftime('%d/%m/%Y %H:%M')
        st.write(f"{dt} - Total: R$ {v[2]:.2f} - Método: {v[3]}")
