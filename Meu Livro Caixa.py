import streamlit as st
import pandas as pd
import os
from datetime import datetime
import urllib.parse

# --- 1. CONFIGURAÇÃO (PRESERVADA) ---
st.set_page_config(page_title="Bear Snack", layout="centered", initial_sidebar_state="collapsed")

# --- 2. O SEU CSS BEAR SNACK (BLOQUEADO) ---
st.markdown("""
    <style>
    .stApp { background-color: #FDF5E6; }
    .block-container { padding-top: 2rem !important; }
    
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

    .stButton > button {
        width: 100%;
        height: 60px !important;
        border-radius: 15px !important;
        background-color: #4E3620 !important;
        color: #D2B48C !important;
        font-weight: bold !important;
        border: 2px solid #D2B48C !important;
    }
    
    /* Estilo específico para botões de valor rápido */
    .val-btn > div > button {
        height: 45px !important;
        font-size: 14px !important;
        background-color: #D2B48C !important;
        color: #4E3620 !important;
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

# --- 3. CONTROLE DE ACESSO ---
if 'logado' not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
    if os.path.exists("logo.png"):
        st.image("logo.png", width=180)
    else:
        st.title("🐻 BEAR SNACK")
    st.markdown("</div>", unsafe_allow_html=True)
    
    with st.container():
        user = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        if st.button("ACESSAR SISTEMA"):
            if user == "admin" and password == "bear123":
                st.session_state.logado = True
                st.rerun()
            else:
                st.error("Dados incorretos")

# --- 4. APP PRINCIPAL ---
else:
    DB_VENDAS = "vendas_bear_final.csv"
    DB_CLIENTES = "clientes_bear_final.csv"

    def load():
        c = pd.read_csv(DB_CLIENTES) if os.path.exists(DB_CLIENTES) else pd.DataFrame(columns=['Nome', 'Telefone'])
        v = pd.read_csv(DB_VENDAS) if os.path.exists(DB_VENDAS) else pd.DataFrame(columns=['ID', 'Cliente', 'Item', 'Valor', 'Data', 'Tipo'])
        return c, v

    df_c, df_v = load()

    with st.sidebar:
        if st.button("🚪 SAIR DO APP"):
            st.session_state.logado = False
            st.rerun()
        st.divider()
        st.subheader("👤 Novo Cliente")
        n = st.text_input("Nome")
        t = st.text_input("WhatsApp")
        if st.button("CADASTRAR"):
            if n:
                new_c = pd.concat([df_c, pd.DataFrame([{'Nome': n, 'Telefone': t}])], ignore_index=True)
                new_c.to_csv(DB_CLIENTES, index=False)
                st.rerun()

    st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
    if os.path.exists("logo.png"):
        st.image("logo.png", width=120)
    else:
        st.title("🐻 Bear Snack")
    st.markdown("</div>", unsafe_allow_html=True)

    if df_c.empty:
        st.info("Acesse o menu lateral para cadastrar clientes.")
    else:
        cliente = st.selectbox("Cliente:", ["-- Selecionar --"] + list(df_c['Nome'].unique()))

        if cliente != "-- Selecionar --":
            v_c = df_v[df_v['Cliente'] == cliente]
            divida = v_c[v_c['Tipo'] == 'Compra']['Valor'].sum() - v_c[v_c['Tipo'] == 'Pagamento']['Valor'].sum()
            tel = df_c[df_c['Nome'] == cliente]['Telefone'].values[0]

            st.markdown(f"""
                <div class="balance-card">
                    <p style="margin:0; opacity:0.8;">Dívida de {cliente}</p>
                    <h1 style="color:white; margin:0; font-size:40px;">R$ {divida:,.2f}</h1>
                </div>
            """, unsafe_allow_html=True)

            c1, c2 = st.columns(2)
            with c1:
                if st.button("➕ COMPRA"): st.session_state.op = "Compra"
            with c2:
                if st.button("💵 PAGOU"): st.session_state.op = "Pagamento"

            if 'op' in st.session_state:
                with st.form("lanca"):
                    st.write(f"### Registrar {st.session_state.op}")
                    
                    # Inicializa o valor no estado se não existir
                    if 'valor_input' not in st.session_state:
                        st.session_state.valor_input = 0.0
                    
                    val_final = st.number_input("Valor R$", min_value=0.0, step=1.0, value=st.session_state.valor_input)
                    
                    # Botões de valores rápidos
                    st.write("Valores sugeridos:")
                    col_v1, col_v2, col_v3 = st.columns(3)
                    with col_v1:
                        if st.form_submit_button("R$ 6,00"): 
                            st.session_state.valor_input = 6.0
                            st.rerun()
                    with col_v2:
                        if st.form_submit_button("R$ 7,00"): 
                            st.session_state.valor_input = 7.0
                            st.rerun()
                    with col_v3:
                        if st.form_submit_button("R$ 8,00"): 
                            st.session_state.valor_input = 8.0
                            st.rerun()
                    
                    i_f = st.text_input("Descrição (Ex: Coxinha, Suco...)")
                    
                    if st.form_submit_button("CONFIRMAR E SALVAR"):
                        nid = datetime.now().strftime("%Y%m%d%H%M%S")
                        # Agora salva Data + Horário
                        agora = datetime.now().strftime("%d/%m - %H:%M")
                        new_v = pd.DataFrame([{'ID': nid, 'Cliente': cliente, 'Item': i_f, 'Valor': val_final, 'Data': agora, 'Tipo': st.session_state.op}])
                        pd.concat([df_v, new_v], ignore_index=True).to_csv(DB_VENDAS, index=False)
                        st.session_state.valor_input = 0.0 # Reseta o valor
                        del st.session_state.op
                        st.rerun()

            # WhatsApp
            msg = f"Olá {cliente}, seu saldo no Bear Snack é R$ {divida:,.2f}"
            url = f"https://wa.me/{tel}?text={urllib.parse.quote(msg)}"
            st.markdown(f'<a href="{url}" target="_blank" style="text-decoration:none;"><div style="background-color:#25D366; color:white; padding:15px; border-radius:15px; text-align:center; font-weight:bold; margin-bottom:20px;">📲 COBRAR NO WHATSAPP</div></a>', unsafe_allow_html=True)

            # Histórico com Data e Hora
            st.write("### Extrato Detalhado")
            for i, row in v_c.iloc[::-1].iterrows():
                cor = "#B03020" if row['Tipo'] == "Compra" else "#2e7d32"
                st.markdown(f"""
                    <div class="item-card">
                        <div>
                            <b>{row['Item'] if str(row['Item']) != 'nan' and row['Item'] != '' else row['Tipo']}</b><br>
                            <small>{row['Data']}</small>
                        </div>
                        <b style="color:{cor}; font-size:18px;">R$ {row['Valor']:.2f}</b>
                    </div>
                """, unsafe_allow_html=True)
                if st.button("🗑️", key=f"del_{row['ID']}"):
                    df_v = df_v[df_v['ID'] != row['ID']]
                    df_v.to_csv(DB_VENDAS, index=False)
                    st.rerun()
