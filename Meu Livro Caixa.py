import streamlit as st
import pandas as pd
import os
from datetime import datetime
import urllib.parse

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(
    page_title="Bear Snack - Login", 
    layout="centered", 
    initial_sidebar_state="collapsed"
)

# --- 2. CSS TEMÁTICO ---
st.markdown("""
    <style>
    .stApp { background-color: #FDF5E6; }
    .block-container { padding-top: 2rem !important; }
    
    /* Card de Login */
    .login-box {
        background-color: white;
        padding: 30px;
        border-radius: 20px;
        border: 2px solid #4E3620;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        text-align: center;
    }

    /* Card de Saldo */
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

    /* Botões Bear Snack */
    .stButton > button {
        width: 100%;
        height: 55px !important;
        border-radius: 15px !important;
        background-color: #4E3620 !important;
        color: #D2B48C !important;
        font-weight: bold !important;
        border: 2px solid #D2B48C !important;
    }
    
    .item-card {
        background: white;
        padding: 15px;
        border-radius: 15px;
        margin-bottom: 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-left: 8px solid #CD853F;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. FUNÇÃO DE LOGIN ---
def tela_login():
    st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
    if os.path.exists("logo.png"):
        st.image("logo.png", width=180)
    else:
        st.title("🐻 BEAR SNACK")
    st.markdown("</div>", unsafe_allow_html=True)

    with st.container():
        st.subheader("Acesso Restrito")
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        
        if st.button("ENTRAR"):
            # DEFINA SEU USUÁRIO E SENHA AQUI
            if usuario == "admin" and senha == "bear123":
                st.session_state.autenticado = True
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos")

# --- 4. INICIALIZAÇÃO DO ESTADO ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

# --- LÓGICA DE EXIBIÇÃO ---
if not st.session_state.autenticado:
    tela_login()
else:
    # --- CÓDIGO DO APP QUE VOCÊ JÁ TEM ---
    
    # Banco de Dados
    DB_VENDAS = "vendas_bear_final.csv"
    DB_CLIENTES = "clientes_bear_final.csv"

    def load():
        c = pd.read_csv(DB_CLIENTES) if os.path.exists(DB_CLIENTES) else pd.DataFrame(columns=['Nome', 'Telefone'])
        v = pd.read_csv(DB_VENDAS) if os.path.exists(DB_VENDAS) else pd.DataFrame(columns=['ID', 'Cliente', 'Item', 'Valor', 'Data', 'Tipo'])
        return c, v

    df_c, df_v = load()

    # Botão Sair na Lateral
    with st.sidebar:
        if os.path.exists("logo.png"): st.image("logo.png")
        if st.button("🚪 LOGOUT"):
            st.session_state.autenticado = False
            st.rerun()
        st.divider()
        st.subheader("👤 Novo Cliente")
        nome_n = st.text_input("Nome")
        tel_n = st.text_input("WhatsApp")
        if st.button("CADASTRAR"):
            if nome_n:
                new_c = pd.concat([df_c, pd.DataFrame([{'Nome': nome_n, 'Telefone': tel_n}])], ignore_index=True)
                new_c.to_csv(DB_CLIENTES, index=False)
                st.rerun()

    # Tela Principal
    st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
    if os.path.exists("logo.png"):
        st.image("logo.png", width=120)
    else:
        st.title("🐻 Bear Snack")
    st.markdown("</div>", unsafe_allow_html=True)

    if df_c.empty:
        st.info("Toque na seta no canto superior para cadastrar clientes.")
    else:
        cliente = st.selectbox("Selecione o Cliente:", ["-- Selecionar --"] + list(df_c['Nome'].unique()))

        if cliente != "-- Selecionar --":
            v_c = df_v[df_v['Cliente'] == cliente]
            divida = v_c[v_c['Tipo'] == 'Compra']['Valor'].sum() - v_c[v_c['Tipo'] == 'Pagamento']['Valor'].sum()
            tel = df_c[df_c['Nome'] == cliente]['Telefone'].values[0]

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
                    st.write(f"### Registrar {st.session_state.op}")
                    v_f = st.number_input("Valor R$", min_value=0.0)
                    i_f = st.text_input("O que comprou?")
                    if st.form_submit_button("SALVAR"):
                        nid = datetime.now().strftime("%f")
                        new_v = pd.DataFrame([{'ID': nid, 'Cliente': cliente, 'Item': i_f, 'Valor': v_f, 'Data': datetime.now().strftime("%d/%m"), 'Tipo': st.session_state.op}])
                        pd.concat([df_v, new_v], ignore_index=True).to_csv(DB_VENDAS, index=False)
                        del st.session_state.op
                        st.rerun()

            # WhatsApp
            msg = f"Olá {cliente}, seu saldo no Bear Snack é de R$ {divida:,.2f}."
            wa_url = f"https://wa.me/{tel}?text={urllib.parse.quote(msg)}"
            st.markdown(f'<a href="{wa_url}" target="_blank" style="text-decoration:none;"><div style="background-color:#25D366; color:white; padding:15px; border-radius:15px; text-align:center; font-weight:bold; margin-bottom:20px;">📲 COBRAR NO WHATSAPP</div></a>', unsafe_allow_html=True)

            # Histórico
            st.write("### Histórico")
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
