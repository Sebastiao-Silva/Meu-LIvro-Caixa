import streamlit as st
import sqlite3
from datetime import datetime, timedelta
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import os

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
        sub_metodo TEXT,
        pago REAL,
        troco REAL,
        descricao_resumo TEXT,
        cliente_id INTEGER
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS itens_venda (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        venda_id INTEGER,
        descricao TEXT,
        valor REAL,
        cliente_id INTEGER,
        data_ms INTEGER,
        FOREIGN KEY(venda_id) REFERENCES vendas(id)
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
# 2. FUNÇÕES AUXILIARES
# ==========================================
def listar_clientes():
    conn = sqlite3.connect('livro_caixa.db')
    cur = conn.cursor()
    cur.execute("SELECT id, nome, perfil, contato, limite, saldo_devedor FROM clientes ORDER BY nome")
    dados = cur.fetchall()
    conn.close()
    return dados

def listar_vendas():
    conn = sqlite3.connect('livro_caixa.db')
    cur = conn.cursor()
    cur.execute("SELECT id, data_ms, total, metodo, descricao_resumo, cliente_id FROM vendas ORDER BY data_ms DESC")
    dados = cur.fetchall()
    conn.close()
    return dados

# ==========================================
# 3. INTERFACE STREAMLIT
# ==========================================
st.set_page_config(page_title="Livro Caixa", layout="wide")
st.title("📒 Livro Caixa - Bear Snack")

menu = st.sidebar.radio("Navegação", ["Início", "Clientes", "Vendas", "Extrato", "Movimentação", "Exclusão", "Relatórios"])

# ==========================================
# 4. INÍCIO
# ==========================================
if menu == "Início":
    st.write("Bem-vindo ao sistema de Livro Caixa!")

# ==========================================
# 5. CLIENTES (CADERNETA)
# ==========================================
elif menu == "Clientes":
    st.subheader("Lista de Clientes")
    clientes = listar_clientes()
    st.table(clientes)

    st.subheader("Adicionar / Alterar Cliente")
    nome = st.text_input("Nome")
    perfil = st.selectbox("Perfil", ["ALUNO", "FUNCIONÁRIO", "CLIENTE"])
    contato = st.text_input("Contato")
    limite = st.number_input("Limite de Crédito", min_value=0.0)
    if st.button("Salvar Cliente"):
        conn = sqlite3.connect('livro_caixa.db')
        cur = conn.cursor()
        cur.execute("INSERT INTO clientes (nome, perfil, contato, limite) VALUES (?,?,?,?)",
                    (nome.upper(), perfil, contato, limite))
        conn.commit()
        conn.close()
        st.success("Cliente salvo com sucesso!")

# ==========================================
# 6. VENDAS (PDV)
# ==========================================
elif menu == "Vendas":
    st.subheader("Registro de Vendas")
    vendas = listar_vendas()
    dados_formatados = []
    for v in vendas:
        dt = datetime.fromtimestamp(v[1]/1000).strftime('%d/%m/%Y %H:%M')
        dados_formatados.append([v[0], dt, v[2], v[3], v[4], v[5]])
    st.table(dados_formatados)

    st.subheader("Nova Venda")
    descricao = st.text_input("Descrição")
    valor = st.number_input("Valor R$", min_value=0.0)
    metodo = st.selectbox("Método", ["DINHEIRO", "CARTÃO", "PIX", "FIADO"])
    if st.button("Registrar Venda"):
        conn = sqlite3.connect('livro_caixa.db')
        cur = conn.cursor()
        now = int(datetime.now().timestamp()*1000)
        cur.execute("INSERT INTO vendas (data_ms, total, metodo, descricao_resumo) VALUES (?,?,?,?)",
                    (now, valor, metodo, descricao))
        conn.commit()
        conn.close()
        st.success("Venda registrada!")

# ==========================================
# 7. EXTRATO INDIVIDUAL
# ==========================================
elif menu == "Extrato":
    st.subheader("Extrato de Cliente")
    clientes = listar_clientes()
    nomes = {c[0]: c[1] for c in clientes}
    cliente_id = st.selectbox("Selecione Cliente", list(nomes.keys()), format_func=lambda x: nomes[x])
    periodo = st.selectbox("Período", ["Hoje", "7 dias", "15 dias", "30 dias", "Tudo"])
    limite_ms = 0
    agora = datetime.now()
    if periodo == "Hoje": limite_ms = agora.replace(hour=0, minute=0, second=0).timestamp()*1000
    elif periodo == "7 dias": limite_ms = (agora - timedelta(days=7)).timestamp()*1000
    elif periodo == "15 dias": limite_ms = (agora - timedelta(days=15)).timestamp()*1000
    elif periodo == "30 dias": limite_ms = (agora - timedelta(days=30)).timestamp()*1000

    conn = sqlite3.connect('livro_caixa.db')
    cur = conn.cursor()
    cur.execute("""SELECT data_ms, descricao, valor FROM itens_venda 
                   WHERE cliente_id = ? AND data_ms >= ?""", (cliente_id, limite_ms))
    dados = cur.fetchall()
    conn.close()
    extrato = []
    total = 0
    for r in dados:
        dt = datetime.fromtimestamp(r[0]/1000).strftime('%d/%m/%Y %H:%M')
        extrato.append([dt, r[1], r[2]])
        total += r[2]
    st.table(extrato)
    st.write(f"**Total no Período: R$ {total:.2f}**")

# ==========================================
# 8. MOVIMENTAÇÃO (SANGRIA / SUPRIMENTO)
# ==========================================
elif menu == "Movimentação":
    st.subheader("Registrar Movimentação")
    tipo = st.selectbox("Tipo", ["SANGRIA", "SUPRIMENTO"])
    valor = st.number_input("Valor R$", min_value=0.0)
    motivo = st.text_input("Motivo")
    if st.button("Salvar Movimentação"):
        if tipo == "SANGRIA": valor = -valor
        conn = sqlite3.connect('livro_caixa.db')
        cur = conn.cursor()
        cur.execute("INSERT INTO vendas (data_ms, total, metodo, descricao_resumo) VALUES (?,?,?,?)",
                    (int(datetime.now().timestamp()*1000), valor, "MOV. CAIXA", motivo))
        conn.commit()
        conn.close()
        st.success("Movimentação registrada!")

# ==========================================
# 9. EXCLUSÃO
# ==========================================
elif menu == "Exclusão":
    st.subheader("Excluir Venda")
    vendas = listar_vendas()
    ids = [v[0] for v in vendas]
    venda_id = st.selectbox("Selecione Venda", ids)
    if st.button("Excluir Venda"):
        conn = sqlite3.connect('livro_caixa.db')
        cur = conn.cursor()
        cur.execute("DELETE FROM itens_venda WHERE venda_id = ?", (venda_id,))
        cur.execute("DELETE FROM vendas WHERE id = ?", (venda_id,))
        conn.commit()
        conn.close()
        st.success("Venda excluída!")

# ==========================================
# 10. RELATÓRIOS
# ==========================================
elif menu == "Relatórios":
    st.subheader("Relatório Geral")
    vendas = listar_vendas()
    total = sum(v[2] for v in vendas)
    st.write(f"**Total de Vendas: R$ {total:.2f}**")

    if st.button("Gerar PDF"):
        nome_arquivo = "Relatorio.pdf"
        pdf = canvas.Canvas(nome_arquivo, pagesize=A4)
        largura, altura = A4
        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(50, altura - 50, "Relatório de Vendas - Bear Snack")
        pdf.setFont("Helvetica", 12)
        y = altura - 100
        for v in vendas[:30]:
            dt = datetime.fromtimestamp(v[1]/1000).strftime('%d/%m/%Y %H:%M')
            pdf.drawString(50, y, f"{dt} - R$ {v[2]:.2f} - Método: {v[3]} - {v[4]}")
            y -= 20
        pdf.drawString(50, y-40, f"TOTAL: R$ {total:.2f}")
        pdf.save()
        st.success(f"PDF gerado: {nome_arquivo}")
