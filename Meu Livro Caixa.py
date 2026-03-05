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

# --- 2. CSS PARA O LAYOUT BEAR SNACK (SEM CONFLITO) ---
st.markdown("""
    <style>
    /* Fundo Creme e Geral */
    .stApp { background-color: #FDF5E6; }
    
    /* Ajuste de Respiro no Topo para não bater na barra do Streamlit */
    .block-container { padding-top: 3rem !important; }
    
    /* Estilização da Sidebar (Menu Lateral) */
    [data-testid="stSidebar"] {
        background-color: #4E3620 !important;
        border-right: 2px solid #D2B48C;
    }
    [data-testid="stSidebar"] * { color: #D2B48C !important; }

    /* CARD DE SALDO - TEMA URSO */
    .balance-card {
        background: linear-gradient(135deg, #B03020 0%, #4E3620 100%);
        color: white;
        padding: 25px;
        border-radius: 20px;
        text-align: center;
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
        color: white !important;
        padding: 15px;
        border-radius: 15px;
        text-align: center;
        text-decoration: none;
        display: block;
        font-weight: bold;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
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
    if os.path.exists("logo.png"):
        st.image("logo.png")
    else:
        st.markdown("<h2 style='text-align:center;'>🐻 MENU</h2>", unsafe_allow_html=True)
    
    st.markdown("---")
    st.subheader("👤 Novo Cliente")
    nome_n = st.text_input("Nome", key="cad_nome")
    tel_n = st.text_input("WhatsApp", key="cad_tel")
    if st.button("CADASTRAR", key="btn_cad"):
        if nome_n:
            new_c = pd.concat([df_c, pd.DataFrame([{'Nome': nome_n, 'Telefone': tel_n}])], ignore_index=True)
            new_c.to_csv(DB_CLIENTES, index=False)
            st.rerun()

# --- 5. TELA PRINCIPAL ---

# TÍTULO / LOGO CENTRALIZADO
st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
if os.path.exists("logo.png"):
    st.image("logo.png", width=150)
else:
    st.markdown("<h1 style='color:#4E3620;'>🐻 Bear Snack</h1>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# BOTÃO DE MENU VISUAL (Indica onde clicar na barra nativa)
st.markdown("<p style='text-align:center; font-size:14px; color:#4E3620; font-weight:bold;'>☰ TOQUE NA SETA NO CANTO SUPERIOR PARA CADASTRAR</p>", unsafe_allow_html=True)

if df_c.empty:
    st.info("Abra o menu lateral para começar.")
else:
    cliente = st.selectbox("Selecione o Cliente:", ["-- Selecionar --"] + list(df_c['Nome'].unique()))

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

        # Botão WhatsApp
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
