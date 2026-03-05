import streamlit as st
import pandas as pd
import os
from datetime import datetime
import urllib.parse

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(
    page_title="Bear Snack", 
    layout="centered", 
    initial_sidebar_state="collapsed"
)

# --- 2. CSS PARA O BOTÃO DE MENU E LAYOUT ---
st.markdown("""
    <style>
    /* Fundo e Geral */
    .stApp { background-color: #FDF5E6; }
    
    /* CRIANDO O BOTÃO DE MENU ELEGANTE */
    .menu-button {
        position: fixed;
        top: 15px;
        left: 15px;
        background-color: #4E3620;
        color: #D2B48C;
        padding: 10px 15px;
        border-radius: 10px;
        font-weight: bold;
        z-index: 9999;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        border: 1px solid #D2B48C;
        cursor: pointer;
    }

    /* CARD DE SALDO */
    .balance-card {
        background: linear-gradient(135deg, #B03020 0%, #4E3620 100%);
        color: white;
        padding: 30px;
        border-radius: 25px;
        text-align: center;
        margin-top: 20px;
        margin-bottom: 20px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.2);
        border: 2px solid #D2B48C;
    }

    /* BOTÕES PRINCIPAIS */
    .stButton > button {
        width: 100%;
        height: 60px !important;
        border-radius: 15px !important;
        background-color: #4E3620 !important;
        color: #D2B48C !important;
        font-weight: bold !important;
        font-size: 18px !important;
        border: 2px solid #D2B48C !important;
    }

    /* BOTÃO WHATSAPP */
    .btn-wa {
        background-color: #25D366;
        color: white;
        padding: 15px;
        border-radius: 15px;
        text-align: center;
        text-decoration: none;
        display: block;
        font-weight: bold;
        margin-bottom: 20px;
    }

    /* CARDS DE HISTÓRICO */
    .item-card {
        background: white;
        padding: 15px;
        border-radius: 15px;
        margin-bottom: 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 4px 8px rgba(0,0,0,0.05);
        border-left: 8px solid #CD853F;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. BANCO DE DADOS ---
DB_VENDAS = "vendas_bear_final.csv"
DB_CLIENTES = "clientes_bear_final.csv"

def load():
    c = pd.read_csv(DB_CLIENTES) if os.path.exists(DB_CLIENTES) else pd.DataFrame(columns=['Nome', 'Telefone'])
    v = pd.read_csv(DB_VENDAS) if os.path.exists(DB_VENDAS) else pd.DataFrame(columns=['ID', 'Cliente', 'Item', 'Valor', 'Data', 'Tipo'])
    return c, v

df_c, df_v = load()

# --- 4. SIDEBAR (MENU DE CADASTRO) ---
with st.sidebar:
    st.markdown("<h2 style='color:#D2B48C;'>🐻 MENU</h2>", unsafe_allow_html=True)
    st.write("---")
    st.subheader("👤 Novo Cliente")
    n = st.text_input("Nome")
    t = st.text_input("WhatsApp")
    if st.button("CADASTRAR"):
        if n:
            new_c = pd.concat([df_c, pd.DataFrame([{'Nome': n, 'Telefone': t}])], ignore_index=True)
            new_c.to_csv(DB_CLIENTES, index=False)
            st.rerun()

# --- 5. TELA PRINCIPAL ---

# Botão visual de menu (apenas indicativo para o usuário clicar na seta original)
st.markdown('<div class="menu-button">☰ MENU</div>', unsafe_allow_html=True)

st.markdown("<h1 style='text-align:center; color:#4E3620; margin-top:40px;'>🐻 Bear Snack</h1>", unsafe_allow_html=True)

if df_c.empty:
    st.info("Clique no botão MENU acima para cadastrar seu primeiro cliente.")
else:
    cliente = st.selectbox("Quem é o cliente?", ["-- Selecionar --"] + list(df_c['Nome'].unique()))

    if cliente != "-- Selecionar --":
        v_c = df_v[df_v['Cliente'] == cliente]
        divida = v_c[v_c['Tipo'] == 'Compra']['Valor'].sum() - v_c[v_c['Tipo'] == 'Pagamento']['Valor'].sum()
        tel = df_c[df_c['Nome'] == cliente]['Telefone'].values[0]

        # Saldo Visual
        st.markdown(f"""
            <div class="balance-card">
                <p style="margin:0; opacity:0.8;">Dívida Ativa</p>
                <h1 style="color:white; margin:0; font-size:40px;">R$ {divida:,.2f}</h1>
                <p style="margin:0; font-weight:bold;">{cliente}</p>
            </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("➕ COMPRA"): st.session_state.op = "Compra"
        with col2:
            if st.button("💵 PAGOU"): st.session_state.op = "Pagamento"

        if 'op' in st.session_state:
            with st.form("form_lanca", clear_on_submit=True):
                st.write(f"### Lançar {st.session_state.op}")
                v_form = st.number_input("Valor R$", min_value=0.0, step=1.0)
                i_form = st.text_input("Descrição")
                if st.form_submit_button("SALVAR REGISTRO"):
                    nid = datetime.now().strftime("%f")
                    new_v = pd.DataFrame([{'ID': nid, 'Cliente': cliente, 'Item': i_form, 'Valor': v_form, 'Data': datetime.now().strftime("%d/%m"), 'Tipo': st.session_state.op}])
                    pd.concat([df_v, new_v], ignore_index=True).to_csv(DB_VENDAS, index=False)
                    del st.session_state.op
                    st.rerun()

        msg = f"Olá {cliente}, seu saldo no Bear Snack é de R$ {divida:,.2f}."
        wa_url = f"https://wa.me/{tel}?text={urllib.parse.quote(msg)}"
        st.markdown(f'<a href="{wa_url}" target="_blank" class="btn-wa">📲 COBRAR NO WHATSAPP</a>', unsafe_allow_html=True)

        st.write("---")
        st.write("### Histórico de Pedidos")
        for i, row in v_c.iloc[::-1].iterrows():
            cor_v = "#B03020" if row['Tipo'] == "Compra" else "#2e7d32"
            st.markdown(f"""
                <div class="item-card">
                    <div><b>{row['Item'] if row['Item'] else row['Tipo']}</b><br><small>{row['Data']}</small></div>
                    <div style="color:{cor_v}; font-weight:bold; font-size:18px;">R$ {row['Valor']:,.2f}</div>
                </div>
            """, unsafe_allow_html=True)
            if st.button("Apagar", key=f"del_{row['ID']}"):
                df_v = df_v[df_v['ID'] != row['ID']]
                df_v.to_csv(DB_VENDAS, index=False)
                st.rerun()
