from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

app = Flask(__name__)

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
# 2. ROTAS PRINCIPAIS
# ==========================================
@app.route("/")
def index():
    return "<h1>Livro Caixa - Bear Snack</h1><p><a href='/clientes'>Clientes</a> | <a href='/vendas'>Vendas</a></p>"

@app.route("/clientes")
def clientes():
    conn = sqlite3.connect('livro_caixa.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM clientes")
    dados = cur.fetchall()
    conn.close()
    html = "<h2>Clientes</h2><ul>"
    for c in dados:
        html += f"<li>{c[1]} - Perfil: {c[2]} - Dívida: R$ {c[5]}</li>"
    html += "</ul><a href='/'>Voltar</a>"
    return html

@app.route("/vendas")
def vendas():
    conn = sqlite3.connect('livro_caixa.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM vendas")
    dados = cur.fetchall()
    conn.close()
    html = "<h2>Vendas</h2><ul>"
    for v in dados:
        dt = datetime.fromtimestamp(v[1]/1000).strftime('%d/%m/%Y %H:%M')
        html += f"<li>{dt} - Total: R$ {v[2]} - Método: {v[3]}</li>"
    html += "</ul><a href='/'>Voltar</a>"
    return html

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
