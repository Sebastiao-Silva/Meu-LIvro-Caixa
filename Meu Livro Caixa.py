import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- CONFIGURAÇÃO VISUAL ---
st.set_page_config(page_title="Gestão de Vendas", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .header-azul { background: #075E54; color: white; padding: 20px; border-radius: 10px; text-align: center; margin-bottom: 20px; }
    .card-cliente { background: white; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #075E54; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- BANCO DE DADOS ---
DB_CLIENTES = "clientes.csv"
DB_VENDAS = "vendas.csv"

def carregar_dados():
    c = pd.read_csv(DB_CLIENTES) if os.path.exists(DB_CLIENTES) else pd.DataFrame(columns=['Nome', 'Telefone'])
    v = pd.read_csv(DB_VENDAS) if os.path.exists(DB_VENDAS) else pd.DataFrame(columns=['Cliente', 'Produto', 'Valor', 'Data', 'Tipo'])
    return c, v

df_clientes, df_vendas = carregar_dados()

# --- INTERFACE ---
st.markdown('<div class="header-azul"><h1>Sistema de Cobrança</h1></div>', unsafe_allow_html=True)

aba_clientes, aba_novo_lancamento = st.tabs(["👥 Meus Clientes", "➕ Novo Lançamento"])

# --- ABA 1: LISTA DE CLIENTES E SALDOS ---
with aba_clientes:
    st.subheader("Resumo de Dívidas")
    if df_clientes.empty:
        st.info("Nenhum cliente cadastrado.")
    else:
        for nome in df_clientes['Nome'].unique():
            # Calcular quanto esse cliente deve
            vendas_c = df_vendas[df_vendas['Cliente'] == nome]
            total_devido = vendas_c[vendas_c['Tipo'] == 'Compra']['Valor'].sum()
            total_pago = vendas_c[vendas_c['Tipo'] == 'Pagamento']['Valor'].sum()
            saldo_devedor = total_devido - total_pago
            
            with st.container():
                st.markdown(f"""
                <div class="card-cliente">
                    <div style="display: flex; justify-content: space-between;">
                        <b>{nome}</b>
                        <span style="color: {'red' if saldo_devedor > 0 else 'green'};">
                            Dívida: R$ {saldo_devedor:,.2f}
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"Ver Detalhes de {nome}", key=nome):
                    st.session_state.detalhe_cliente = nome

    # Se clicar no detalhe, mostra o histórico
    if 'detalhe_cliente' in st.session_state:
        st.divider()
        st.write(f"### Histórico: {st.session_state.detalhe_cliente}")
        historico = df_vendas[df_vendas['Cliente'] == st.session_state.detalhe_cliente]
        st.table(historico[['Data', 'Produto', 'Valor', 'Tipo']])
        if st.button("Fechar Detalhes"):
            del st.session_state.detalhe_cliente
            st.rerun()

# --- ABA 2: NOVO LANÇAMENTO (TELA QUE VOCÊ PEDIU) ---
with aba_novo_lancamento:
    col_cad, col_lan = st.columns(2)
    
    with col_cad:
        st.subheader("Cadastrar Novo Cliente")
        novo_n = st.text_input("Nome do Cliente")
        if st.button("Salvar Cliente"):
            if novo_n:
                novo_c = pd.DataFrame([{'Nome': novo_n}])
                pd.concat([df_clientes, novo_c], ignore_index=True).to_csv(DB_CLIENTES, index=False)
                st.success("Cadastrado!")
                st.rerun()

    st.divider()
    
    st.subheader("Inserir Dados de Venda/Pagamento")
    if not df_clientes.empty:
        with st.form("form_venda", clear_on_submit=True):
            # CAIXA DE SELEÇÃO DO CLIENTE (O que você pediu!)
            cliente_sel = st.selectbox("Selecione o Cliente", df_clientes['Nome'].unique())
            tipo_mov = st.selectbox("O que ele fez?", ["Compra", "Pagamento"])
            item = st.text_input("O que ele comprou? (ou Descrição do pagamento)")
            valor = st.number_input("Valor R$", min_value=0.01)
            data_v = st.date_input("Data", datetime.now())
            
            if st.form_submit_button("Registrar no Livro"):
                nova_v = pd.DataFrame([{
                    'Cliente': cliente_sel, 
                    'Produto': item, 
                    'Valor': valor, 
                    'Data': data_v.strftime("%d/%m/%Y"),
                    'Tipo': tipo_mov
                }])
                pd.concat([df_vendas, nova_v], ignore_index=True).to_csv(DB_VENDAS, index=False)
                st.success(f"Registrado para {cliente_sel}!")
                st.rerun()
    else:
        st.warning("Cadastre um cliente primeiro para fazer lançamentos.")