import streamlit as st
import pandas as pd
import os
from datetime import datetime
import urllib.parse

# --- CONFIGURAÇÃO DE UI MOBILE ---
st.set_page_config(page_title="Bear Snack", layout="centered")

# CSS para transformar o site em um App de Celular
st.markdown(f"""
    <style>
    /* Esconder menus do Streamlit para parecer App Nativo */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    
    /* Container Principal Estreito */
    .block-container {{
        padding-top: 1rem;
        max-width: 450px;
    }}

    /* Cabeçalho com Logo */
    .app-header {{
        text-align: center;
        padding: 10px;
        margin-bottom: 15px;
    }}

    /* Card de Saldo Estilo Nubank/Inter */
    .balance-card {{
        background: linear-gradient(135deg, #4E3620 0%, #CD853F 100%);
        color: white;
        padding: 25px;
        border-radius: 20px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.1);
        margin-bottom: 20px;
        text-align: left;
    }}
    .balance-label {{ font-size: 14px; opacity: 0.8; margin-bottom: 5px; }}
    .balance-value {{ font-size: 32px; font-weight: bold; }}

    /* Cards de Transação Profissionais */
    .item-card {{
        background: white;
        padding: 15px;
        border-radius: 15px;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        border-left: 5px solid #D2B48C;
    }}
    .item-info {{ display: flex; flex-direction: column; }}
    .item-title {{ font-weight: bold; color: #4E3620; font-size: 16px; }}
    .item-date {{ font-size: 12px; color: #888; }}
    .item-price {{ font-weight: bold; font-size: 16px; }}
    
    /* Botões Flutuantes de Ação */
    .stButton > button {{
        width: 100%;
        border-radius: 12px;
        height: 50px;
        background-color: #4E3620 !important;
        color: white !important;
        border: none;
        font-weight: 600;
        margin-top: 10px;
    }}
    
    /* Input Style */
    input {{
        border-radius: 10px !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- BANCO DE DADOS ---
DB_VENDAS = "vendas_final.csv"
DB_CLIENTES = "clientes_final.csv"

def load_data():
    c = pd.read_csv(DB_CLIENTES) if os.path.exists(DB_CLIENTES) else pd.DataFrame(columns=['Nome', 'Telefone'])
    v = pd.read_csv(DB_VENDAS) if os.path.exists(DB_VENDAS) else pd.DataFrame(columns=['ID', 'Cliente', 'Item', 'Valor', 'Data', 'Tipo'])
    return c, v

df_c, df_v = load_data()

# --- CONTEÚDO DO APP ---

# 1. LOGO
st.markdown('<div class="app-header">', unsafe_allow_html=True)
if os.path.exists("logo.png"):
    st.image("logo.png", width=120)
else:
    st.title("🐻 BEAR SNACK")
st.markdown('</div>', unsafe_allow_html=True)

# 2. SELEÇÃO DE CLIENTE (Simples e Direta)
cliente = st.selectbox("Escolha o Cliente", ["-- Selecionar --"] + list(df_c['Nome'].unique()))

if cliente != "-- Selecionar --":
    vendas_c = df_v[df_v['Cliente'] == cliente]
    saldo = vendas_c[vendas_c['Tipo'] == 'Compra']['Valor'].sum() - vendas_c[vendas_c['Tipo'] == 'Pagamento']['Valor'].sum()
    tel = df_c[df_c['Nome'] == cliente]['Telefone'].values[0]

    # 3. CARD DE SALDO PROFISSIONAL
    st.markdown(f"""
        <div class="balance-card">
            <div class="balance-label">Total em aberto:</div>
            <div class="balance-value">R$ {saldo:,.2f}</div>
            <div style="font-size:12px; margin-top:10px;">Cliente: {cliente}</div>
        </div>
    """, unsafe_allow_html=True)

    # 4. BOTÕES DE AÇÃO RÁPIDA
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Nova Compra"): st.session_state.mode = "Compra"
    with col2:
        if st.button("💵 Receber"): st.session_state.mode = "Pagamento"

    # Formulário de Lançamento (Só aparece se clicar nos botões acima)
    if 'mode' in st.session_state:
        with st.expander(f"Registrar {st.session_state.mode}", expanded=True):
            with st.form("form_entry", clear_on_submit=True):
                val = st.number_input("Valor", min_value=0.0, step=1.0)
                desc = st.text_input("Descrição (O que foi?)")
                if st.form_submit_button("Confirmar"):
                    new_id = datetime.now().strftime("%H%M%S")
                    new_row = pd.DataFrame([{'ID': new_id, 'Cliente': cliente, 'Item': desc, 'Valor': val, 'Data': datetime.now().strftime("%d/%m"), 'Tipo': st.session_state.mode}])
                    df_v = pd.concat([df_v, new_row], ignore_index=True)
                    df_v.to_csv(DB_VENDAS, index=False)
                    del st.session_state.mode
                    st.rerun()

    # 5. WHATSAPP (Botão Único)
    msg = f"Olá {cliente}, seu saldo no Bear Snack é de R$ {saldo:,.2f}."
    wa_url = f"https://wa.me/{tel}?text={urllib.parse.quote(msg)}"
    st.markdown(f'<a href="{wa_url}" target="_blank"><button style="width:100%; background:#25D366; color:white; border:none; padding:12px; border-radius:12px; font-weight:bold; cursor:pointer; margin-bottom:20px;">📲 Cobrar via WhatsApp</button></a>', unsafe_allow_html=True)

    # 6. HISTÓRICO EM CARDS (Limpo e profissional)
    st.write("---")
    st.write("### Histórico")
    for i, row in vendas_c.iloc[::-1].iterrows():
        color = "#B03020" if row['Tipo'] == "Compra" else "#2e7d32"
        symbol = "+" if row['Tipo'] == "Compra" else "-"
        
        st.markdown(f"""
            <div class="item-card">
                <div class="item-info">
                    <span class="item-title">{row['Item'] if row['Item'] else row['Tipo']}</span>
                    <span class="item-date">{row['Data']}</span>
                </div>
                <div style="display:flex; align-items:center; gap:10px;">
                    <span class="item-price" style="color:{color}">{symbol} R$ {row['Valor']:,.2f}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
        # Botão de excluir discreto abaixo do card se necessário
        if st.button("Excluir", key=f"del_{row['ID']}"):
            df_v = df_v[df_v['ID'] != row['ID']].to_csv(DB_VENDAS, index=False)
            st.rerun()

# ABA DE CADASTRO (Fica escondida até precisar)
with st.sidebar:
    st.header("Novo Cliente")
    n = st.text_input("Nome")
    t = st.text_input("WhatsApp")
    if st.button("Salvar"):
        new_c = pd.concat([df_c, pd.DataFrame([{'Nome': n, 'Telefone': t}])], ignore_index=True)
        new_c.to_csv(DB_CLIENTES, index=False)
        st.success("Cliente salvo!")
