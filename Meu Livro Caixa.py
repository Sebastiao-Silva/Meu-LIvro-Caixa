import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- ESTILO E CONFIGURAÇÃO ---
st.set_page_config(page_title="Controle de Clientes", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #f4f7f6; }
    .status-divida { padding: 20px; border-radius: 15px; text-align: center; margin-bottom: 20px; color: white; }
    .devedor { background-color: #e53935; }
    .limpo { background-color: #43a047; }
    .card-item { background: white; padding: 10px; border-radius: 8px; margin-bottom: 5px; border-left: 4px solid #075E54; }
    </style>
    """, unsafe_allow_html=True)

# --- SISTEMA DE ARQUIVOS ---
DB_CLIENTES = "meus_clientes.csv"
DB_VENDAS = "minhas_vendas.csv"

def carregar():
    c = pd.read_csv(DB_CLIENTES) if os.path.exists(DB_CLIENTES) else pd.DataFrame(columns=['Nome'])
    v = pd.read_csv(DB_VENDAS) if os.path.exists(DB_VENDAS) else pd.DataFrame(columns=['Cliente', 'Item', 'Valor', 'Data', 'Tipo'])
    return c, v

df_c, df_v = carregar()

# --- BARRA LATERAL: CADASTRO RÁPIDO ---
with st.sidebar:
    st.header("⚙️ Configurações")
    novo_nome = st.text_input("Cadastrar Novo Cliente")
    if st.button("Adicionar Cliente"):
        if novo_nome and novo_nome not in df_c['Nome'].values:
            novo_df = pd.concat([df_c, pd.DataFrame([{'Nome': novo_nome}])], ignore_index=True)
            novo_df.to_csv(DB_CLIENTES, index=False)
            st.success("Cliente salvo!")
            st.rerun()

# --- TELA PRINCIPAL ---
st.title("📑 Livro de Fiados")

if df_c.empty:
    st.warning("Use a barra lateral para cadastrar seu primeiro cliente!")
else:
    # 1. ESCOLHA DO CLIENTE (A caixa de seleção que você pediu)
    cliente_atual = st.selectbox("👤 Selecione a pessoa para gerenciar:", ["-- Selecione --"] + list(df_c['Nome'].unique()))

    if cliente_atual != "-- Selecione --":
        # Calcular Saldo do Cliente Selecionado
        vendas_selecionado = df_v[df_v['Cliente'] == cliente_atual]
        compras = vendas_selecionado[vendas_selecionado['Tipo'] == 'Compra']['Valor'].sum()
        pagamentos = vendas_selecionado[vendas_selecionado['Tipo'] == 'Pagamento']['Valor'].sum()
        saldo_final = compras - pagamentos

        # Exibir Status Visual
        classe_status = "devedor" if saldo_final > 0 else "limpo"
        st.markdown(f"""
            <div class="status-divida {classe_status}">
                <p style="margin:0; opacity: 0.8;">Dívida Atual de {cliente_atual}</p>
                <h2 style="margin:0;">R$ {saldo_final:,.2f}</h2>
            </div>
            """, unsafe_allow_html=True)

        # 2. LANÇAMENTO DE DADOS (A tela de inserção)
        with st.expander("➕ Lançar Nova Compra ou Pagamento", expanded=True):
            with st.form("registro_venda", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    tipo = st.selectbox("Operação", ["Compra", "Pagamento"])
                    valor = st.number_input("Valor R$", min_value=0.0, step=0.50)
                with col2:
                    data = st.date_input("Data", datetime.now())
                    item = st.text_input("O que comprou? (Descrição)")
                
                if st.form_submit_button("Confirmar Lançamento"):
                    if valor > 0:
                        nova_linha = pd.DataFrame([{
                            'Cliente': cliente_atual, 'Item': item, 
                            'Valor': valor, 'Data': data.strftime("%d/%m/%Y"), 'Tipo': tipo
                        }])
                        pd.concat([df_v, nova_linha], ignore_index=True).to_csv(DB_VENDAS, index=False)
                        st.success("Lançado com sucesso!")
                        st.rerun()

        # 3. HISTÓRICO DO CLIENTE
        st.subheader(f"📜 Últimos registros de {cliente_atual}")
        if vendas_selecionado.empty:
            st.info("Nenhum histórico para este cliente.")
        else:
            for i, row in vendas_selecionado.iloc[::-1].iterrows():
                cor = "red" if row['Tipo'] == "Compra" else "green"
                st.markdown(f"""
                    <div class="card-item">
                        <small>{row['Data']}</small> | <b>{row['Item']}</b> 
                        <span style="float: right; color: {cor}; font-weight: bold;">
                            {row['Tipo']}: R$ {row['Valor']:,.2f}
                        </span>
                    </div>
                    """, unsafe_allow_html=True)