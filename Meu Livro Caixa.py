import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- CONFIGURAÇÃO VISUAL NATIVA ---
st.set_page_config(page_title="Livro Caixa", layout="centered")

# CSS para clonar o visual do App da Play Store
st.markdown("""
    <style>
    /* Fundo cinza claro padrão de app */
    .stApp { background-color: #F0F2F5; }
    
    /* Cabeçalho Azul do Livro Caixa */
    .header-caixa {
        background-color: #1976D2;
        color: white;
        padding: 25px;
        border-radius: 0 0 20px 20px;
        text-align: center;
        margin: -60px -20px 20px -20px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    }
    
    /* Cards de Transação */
    .card {
        background: white;
        padding: 12px 18px;
        border-radius: 12px;
        margin-bottom: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-left: 5px solid #DDD;
    }
    .card-entrada { border-left: 5px solid #4CAF50; }
    .card-saida { border-left: 5px solid #F44336; }
    
    .valor-entrada { color: #4CAF50; font-weight: bold; font-size: 1.1em; }
    .valor-saida { color: #F44336; font-weight: bold; font-size: 1.1em; }
    
    /* Botões Flutuantes/Grandes */
    .stButton>button {
        border-radius: 10px;
        height: 3em;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- LÓGICA DE DADOS ---
DB_FILE = "caixa_storage.csv"
if 'df' not in st.session_state:
    if os.path.exists(DB_FILE):
        st.session_state.df = pd.read_csv(DB_FILE)
    else:
        st.session_state.df = pd.DataFrame(columns=['Data', 'Desc', 'Valor', 'Tipo'])

def salvar(df):
    df.to_csv(DB_FILE, index=False)
    st.session_state.df = df

# --- INTERFACE ---
df = st.session_state.df
total_in = df[df['Tipo'] == 'Entrada']['Valor'].sum()
total_out = df[df['Tipo'] == 'Saída']['Valor'].sum()
saldo = total_in - total_out

# 1. Topo Azul (Saldo)
st.markdown(f"""
    <div class="header-caixa">
        <p style="margin:0; font-size: 0.9em; opacity: 0.9;">Saldo Atual</p>
        <h1 style="margin:0; font-size: 2.2em;">R$ {saldo:,.2f}</h1>
    </div>
    """, unsafe_allow_html=True)

# 2. Botões de Ação Rápida (Entrada/Saída)
col1, col2 = st.columns(2)
with col1:
    btn_in = st.button("➕ ENTRADA", use_container_width=True)
with col2:
    btn_out = st.button("➖ SAÍDA", use_container_width=True)

# Lógica dos formulários (aparecem ao clicar nos botões)
if btn_in or st.session_state.get('show_in'):
    st.session_state.show_in = True
    with st.form("form_in", clear_on_submit=True):
        st.subheader("Registrar Entrada")
        v = st.number_input("Valor", min_value=0.01)
        d = st.text_input("Descrição")
        if st.form_submit_button("Confirmar"):
            novo = pd.DataFrame([{'Data': datetime.now().strftime("%d/%m/%y"), 'Desc': d, 'Valor': v, 'Tipo': 'Entrada'}])
            salvar(pd.concat([df, novo], ignore_index=True))
            st.session_state.show_in = False
            st.rerun()

if btn_out or st.session_state.get('show_out'):
    st.session_state.show_out = True
    with st.form("form_out", clear_on_submit=True):
        st.subheader("Registrar Saída")
        v = st.number_input("Valor", min_value=0.01)
        d = st.text_input("Descrição")
        if st.form_submit_button("Confirmar"):
            novo = pd.DataFrame([{'Data': datetime.now().strftime("%d/%m/%y"), 'Desc': d, 'Valor': v, 'Tipo': 'Saída'}])
            salvar(pd.concat([df, novo], ignore_index=True))
            st.session_state.show_out = False
            st.rerun()

st.write("### Movimentações Recentes")

# 3. Lista Estilizada (Cards)
if df.empty:
    st.info("Nenhum lançamento hoje.")
else:
    # Mostra os últimos 20 lançamentos
    for i, row in df.iloc[::-1].head(20).iterrows():
        classe_card = "card-entrada" if row['Tipo'] == "Entrada" else "card-saida"
        classe_valor = "valor-entrada" if row['Tipo'] == "Entrada" else "valor-saida"
        simbolo = "+" if row['Tipo'] == "Entrada" else "-"
        
        st.markdown(f"""
            <div class="card {classe_card}">
                <div>
                    <span style="color: #888; font-size: 0.8em;">{row['Data']}</span><br>
                    <span style="font-weight: 500;">{row['Desc']}</span>
                </div>
                <div class="{classe_valor}">
                    {simbolo} R$ {row['Valor']:,.2f}
                </div>
            </div>
            """, unsafe_allow_html=True)