import streamlit as st
import pandas as pd
import os
from datetime import datetime
import urllib.parse

# --- 1. CONFIGURAÇÃO COM IDENTIDADE ---
st.set_page_config(
    page_title="Bear Snack - Gestão", 
    layout="centered", 
    initial_sidebar_state="collapsed"
)

# --- 2. CSS TEMÁTICO "URSO" ---
st.markdown("""
    <style>
    /* Fundo da Tela */
    .stApp { background-color: #FDF5E6; } 
    
    /* Cabeçalho e Sidebar */
    [data-testid="stSidebar"] { background-color: #4E3620 !important; }
    [data-testid="stSidebar"] * { color: #D2B48C !important; }
    
    /* Card de Saldo (Vermelho Chapéu + Marrom) */
    .balance-card {
        background: linear-gradient(135deg, #B03020 0%, #4E3620 100%);
        color: white;
        padding: 30px;
        border-radius: 25px;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.2);
        border: 2px solid #D2B48C;
    }

    /* Botões Bear Snack (Marrom com texto Bege) */
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
    
    /* Botão de WhatsApp (Verde mas arredondado) */
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

    /* Cards de Histórico (Bege com borda Marrom) */
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
    .item-card b { color: #4E3620; }
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

# --- 4. LOGO E MENU LATERAL ---
with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png")
    else:
        st.title("🐻 BEAR SNACK")
    
    st.write("### 👤 Novo Cliente")
    n = st.text_input("Nome")
    t = st.text_input("WhatsApp")
    if st.button("CADASTRAR"):
        if n:
            new_c = pd.concat([df_c, pd.DataFrame([{'Nome': n, 'Telefone': t}])], ignore_index=True)
            new_c.to_csv(DB_CLIENTES, index=False)
            st.rerun()

# --- 5. TELA PRINCIPAL ---
st.markdown("<h1 style='text-align:center; color:#4E3620;'>🐻 Bear Snack</h1>", unsafe_allow_html=True)

if df_c.empty:
    st.info("Toque no menu (seta >) para cadastrar clientes.")
else:
    cliente = st.selectbox("Quem é o cliente?", ["-- Selecionar --"] + list(df_c['Nome'].unique()))

    if cliente != "-- Selecionar --":
        # Dados do Cliente
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

        # Botões de Toque (Mobile Ready)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("➕ COMPRA"): st.session_state.op = "Compra"
        with col2:
            if st.button("💵 PAGOU"): st.session_state.op = "Pagamento"

        # Formulário Dinâmico
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

        # WhatsApp estilizado
        msg = f"Olá {cliente}, seu saldo no Bear Snack é de R$ {divida:,.2f}."
        wa_url = f"https://wa.me/{tel}?text={urllib.parse.quote(msg)}"
        st.markdown(f'<a href="{wa_url}" target="_blank" class="btn-wa">📲 COBRAR NO WHATSAPP</a>', unsafe_allow_html=True)

        # Histórico em Cards Bear
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
