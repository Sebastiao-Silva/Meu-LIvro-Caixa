import streamlit as st
import pandas as pd
import os
from datetime import datetime
import urllib.parse

# --- CONFIGURAÇÃO E ESTILO ---
st.set_page_config(page_title="Gestão de Fiados Pro", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #f0f2f5; }
    .status-card { padding: 20px; border-radius: 15px; text-align: center; color: white; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .devedor { background: linear-gradient(135deg, #d32f2f, #f44336); }
    .pago { background: linear-gradient(135deg, #2e7d32, #4caf50); }
    .card-item { background: white; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #075E54; display: flex; justify-content: space-between; align-items: center; }
    </style>
    """, unsafe_allow_html=True)

# --- BANCO DE DADOS ---
DB_CLIENTES = "clientes_v3.csv"
DB_VENDAS = "vendas_v3.csv"

def carregar():
    c = pd.read_csv(DB_CLIENTES) if os.path.exists(DB_CLIENTES) else pd.DataFrame(columns=['Nome', 'Telefone'])
    v = pd.read_csv(DB_VENDAS) if os.path.exists(DB_VENDAS) else pd.DataFrame(columns=['ID', 'Cliente', 'Item', 'Valor', 'Data', 'Tipo'])
    return c, v

df_c, df_v = carregar()

# --- SIDEBAR: CADASTRO ---
with st.sidebar:
    st.header("👤 Novo Cliente")
    n_nome = st.text_input("Nome completo")
    n_tel = st.text_input("WhatsApp (ex: 5511999999999)")
    if st.button("Cadastrar Cliente"):
        if n_nome:
            novo_c = pd.concat([df_c, pd.DataFrame([{'Nome': n_nome, 'Telefone': n_tel}])], ignore_index=True)
            novo_c.to_csv(DB_CLIENTES, index=False)
            st.success("Salvo!")
            st.rerun()

# --- TELA PRINCIPAL ---
st.title("📲 Meu Livro de Vendas")

if df_c.empty:
    st.info("Cadastre um cliente na barra lateral para começar.")
else:
    cliente_sel = st.selectbox("Selecione o Cliente:", ["-- Selecionar --"] + list(df_c['Nome'].unique()))

    if cliente_sel != "-- Selecionar --":
        # Dados do cliente
        dados_cliente = df_c[df_c['Nome'] == cliente_sel].iloc[0]
        vendas_c = df_v[df_v['Cliente'] == cliente_sel]
        
        # Cálculo de Saldo
        compras = vendas_c[vendas_c['Tipo'] == 'Compra']['Valor'].sum()
        pagamentos = vendas_c[vendas_c['Tipo'] == 'Pagamento']['Valor'].sum()
        saldo = compras - pagamentos

        # Card de Status
        cor_card = "devedor" if saldo > 0 else "pago"
        st.markdown(f"""<div class="status-card {cor_card}">
            <p style="margin:0; opacity:0.8;">Saldo Devedor</p>
            <h2 style="margin:0;">R$ {saldo:,.2f}</h2>
        </div>""", unsafe_allow_html=True)

        # Ações: Lançar e Cobrar
        col_l, col_w = st.columns(2)
        with col_l:
            with st.expander("➕ Novo Lançamento"):
                with st.form("add_venda", clear_on_submit=True):
                    t = st.selectbox("Tipo", ["Compra", "Pagamento"])
                    v = st.number_input("Valor R$", min_value=0.0, step=0.50)
                    i = st.text_input("O que foi?")
                    d = st.date_input("Data", datetime.now())
                    if st.form_submit_button("Salvar"):
                        novo_id = datetime.now().strftime("%Y%m%d%H%M%S")
                        nova_l = pd.DataFrame([{'ID': novo_id, 'Cliente': cliente_sel, 'Item': i, 'Valor': v, 'Data': d.strftime("%d/%m/%Y"), 'Tipo': t}])
                        pd.concat([df_v, nova_l], ignore_index=True).to_csv(DB_VENDAS, index=False)
                        st.rerun()
        
        with col_w:
            # BOTÃO WHATSAPP (A função de Recibo que você pediu)
            msg = f"Olá {cliente_sel}, segue seu extrato:\nSaldo devedor: R$ {saldo:,.2f}\nÚltima atualização: {datetime.now().strftime('%d/%m/%y')}"
            link_wa = f"https://wa.me/{dados_cliente['Telefone']}?text={urllib.parse.quote(msg)}"
            st.markdown(f'<a href="{link_wa}" target="_blank"><button style="width:100%; height:45px; border-radius:10px; background:#25D366; color:white; border:none; cursor:pointer; font-weight:bold;">✉️ ENVIAR COBRANÇA</button></a>', unsafe_allow_html=True)

        st.divider()

        # LISTA COM EXCLUSÃO (O que você pediu!)
        st.subheader("Histórico")
        for idx, row in vendas_c.iloc[::-1].iterrows():
            with st.container():
                col_info, col_del = st.columns([0.8, 0.2])
                with col_info:
                    cor_v = "red" if row['Tipo'] == "Compra" else "green"
                    st.markdown(f"""<div class="card-item">
                        <div><small>{row['Data']}</small><br><b>{row['Item']}</b></div>
                        <div style="color:{cor_v}; font-weight:bold;">R$ {row['Valor']:,.2f}</div>
                    </div>""", unsafe_allow_html=True)
                with col_del:
                    # Botão de Excluir individual
                    if st.button("🗑️", key=f"del_{row['ID']}"):
                        df_v = df_v[df_v['ID'] != row['ID']]
                        df_v.to_csv(DB_VENDAS, index=False)
                        st.rerun()
