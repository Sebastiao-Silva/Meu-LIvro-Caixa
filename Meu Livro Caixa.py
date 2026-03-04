import streamlit as st
import pandas as pd
import os
from datetime import datetime
import urllib.parse

# --- CONFIGURAÇÃO DE UI MOBILE ---
st.set_page_config(page_title="Bear Snack", layout="centered", initial_sidebar_state="expanded")

# CSS Ajustado para Profissionalismo e Visibilidade
st.markdown(f"""
    <style>
    /* Garante que a Sidebar e o Header sejam visíveis */
    [data-testid="stSidebar"] {{
        background-color: #4E3620 !important;
    }}
    [data-testid="stSidebar"] * {{
        color: white !important;
    }}
    
    /* Botões Grandes para Celular */
    .stButton > button {{
        width: 100%;
        height: 55px !important;
        border-radius: 12px !important;
        font-weight: bold !important;
        margin-bottom: 10px;
    }}

    /* Card de Saldo Central */
    .balance-card {{
        background: linear-gradient(135deg, #B03020 0%, #4E3620 100%);
        color: white;
        padding: 25px;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }}

    /* Cards de Histórico Estilo App */
    .item-card {{
        background: white;
        padding: 15px;
        border-radius: 15px;
        margin-bottom: 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        border-left: 5px solid #D2B48C;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- BANCO DE DADOS ---
DB_VENDAS = "vendas_v5.csv"
DB_CLIENTES = "clientes_v5.csv"

def load_data():
    c = pd.read_csv(DB_CLIENTES) if os.path.exists(DB_CLIENTES) else pd.DataFrame(columns=['Nome', 'Telefone'])
    v = pd.read_csv(DB_VENDAS) if os.path.exists(DB_VENDAS) else pd.DataFrame(columns=['ID', 'Cliente', 'Item', 'Valor', 'Data', 'Tipo'])
    return c, v

df_c, df_v = load_data()

# --- BARRA LATERAL (BOTÃO AGORA APARECE) ---
with st.sidebar:
    st.image("logo.png") if os.path.exists("logo.png") else st.title("🐻 BEAR SNACK")
    st.divider()
    st.subheader("👤 Gestão de Clientes")
    with st.expander("Cadastrar Novo Cliente"):
        n = st.text_input("Nome")
        t = st.text_input("WhatsApp")
        if st.button("SALVAR CLIENTE"):
            if n:
                new_c = pd.concat([df_c, pd.DataFrame([{'Nome': n, 'Telefone': t}])], ignore_index=True)
                new_c.to_csv(DB_CLIENTES, index=False)
                st.success("Salvo!")
                st.rerun()
    
    st.divider()
    st.write("Versão 1.5 - Mobile")

# --- TELA PRINCIPAL ---
st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
if os.path.exists("logo.png"):
    st.image("logo.png", width=120)
else:
    st.title("🐻 BEAR SNACK")
st.markdown("</div>", unsafe_allow_html=True)

if df_c.empty:
    st.info("Abra o menu lateral (setinha no topo) para cadastrar clientes.")
else:
    cliente = st.selectbox("Selecione o Cliente:", ["-- Escolher --"] + list(df_c['Nome'].unique()))

    if cliente != "-- Escolher --":
        vendas_c = df_v[df_v['Cliente'] == cliente]
        saldo = vendas_c[vendas_c['Tipo'] == 'Compra']['Valor'].sum() - vendas_c[vendas_c['Tipo'] == 'Pagamento']['Valor'].sum()
        tel = df_c[df_c['Nome'] == cliente]['Telefone'].values[0]

        # Card de Saldo
        st.markdown(f"""
            <div class="balance-card">
                <small style="opacity:0.8">Valor em aberto: {cliente}</small>
                <h1 style="color:white; margin:0; font-size: 35px;">R$ {saldo:,.2f}</h1>
            </div>
        """, unsafe_allow_html=True)

        # Ações Rápidas
        col1, col2 = st.columns(2)
        with col1:
            if st.button("➕ COMPRA"): st.session_state.op = "Compra"
        with col2:
            if st.button("💵 RECEBER"): st.session_state.op = "Pagamento"

        # Formulário Dinâmico
        if 'op' in st.session_state:
            with st.form("lançamento", clear_on_submit=True):
                st.write(f"### Registrar {st.session_state.op}")
                val = st.number_input("Valor", min_value=0.0)
                desc = st.text_input("Descrição")
                if st.form_submit_button("CONFIRMAR"):
                    new_id = datetime.now().strftime("%f")
                    new_row = pd.DataFrame([{'ID': new_id, 'Cliente': cliente, 'Item': desc, 'Valor': val, 'Data': datetime.now().strftime("%d/%m"), 'Tipo': st.session_state.op}])
                    df_v = pd.concat([df_v, new_row], ignore_index=True)
                    df_v.to_csv(DB_VENDAS, index=False)
                    del st.session_state.op
                    st.rerun()

        # Botão WhatsApp
        msg = f"Olá {cliente}, seu saldo no Bear Snack é de R$ {saldo:,.2f}."
        wa_url = f"https://wa.me/{tel}?text={urllib.parse.quote(msg)}"
        st.markdown(f'<a href="{wa_url}" target="_blank"><button style="width:100%; background:#25D366; color:white; border:none; padding:15px; border-radius:12px; font-weight:bold; cursor:pointer; margin-top:5px; margin-bottom:20px;">📲 COBRAR NO WHATSAPP</button></a>', unsafe_allow_html=True)

        # Histórico
        st.write("---")
        st.subheader("Histórico")
        for i, row in vendas_c.iloc[::-1].iterrows():
            cor = "#B03020" if row['Tipo'] == "Compra" else "#2e7d32"
            st.markdown(f"""
                <div class="item-card">
                    <div><b>{row['Item']}</b><br><small>{row['Data']}</small></div>
                    <div style="text-align:right;">
                        <b style="color:{cor}; font-size:18px;">R$ {row['Valor']:,.2f}</b><br>
                        <small style="color:#888;">{row['Tipo']}</small>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            if st.button("Excluir", key=f"del_{row['ID']}"):
                df_v = df_v[df_v['ID'] != row['ID']]
                df_v.to_csv(DB_VENDAS, index=False)
                st.rerun()
