import streamlit as st
import pandas as pd
import os
from datetime import datetime
import urllib.parse

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
# O parâmetro 'initial_sidebar_state' garante que o menu lateral seja acessível
st.set_page_config(
    page_title="Bear Snack Pro", 
    layout="centered", 
    initial_sidebar_state="expanded"
)

# --- 2. ESTILIZAÇÃO CSS CUSTOMIZADA ---
st.markdown("""
    <style>
    .stApp { background-color: #FDFBF9; }
    .balance-card {
        background: linear-gradient(135deg, #4E3620, #B03020);
        color: white;
        padding: 25px;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .stButton > button {
        width: 100%;
        height: 55px !important;
        border-radius: 12px !important;
        font-weight: bold !important;
        font-size: 16px !important;
    }
    /* Estilo para os cards de histórico */
    .hist-card {
        background: white;
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 10px;
        border-left: 5px solid #CD853F;
        display: flex;
        justify-content: space-between;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. LÓGICA DE DADOS (PERSISTÊNCIA) ---
DB_VENDAS = "vendas_bear.csv"
DB_CLIENTES = "clientes_bear.csv"

def carregar_banco():
    c = pd.read_csv(DB_CLIENTES) if os.path.exists(DB_CLIENTES) else pd.DataFrame(columns=['Nome', 'Telefone'])
    v = pd.read_csv(DB_VENDAS) if os.path.exists(DB_VENDAS) else pd.DataFrame(columns=['ID', 'Cliente', 'Item', 'Valor', 'Data', 'Tipo'])
    return c, v

df_c, df_v = carregar_banco()

# --- 4. BARRA LATERAL (SIDEBAR) ---
# Usando o método sidebar para organizar o cadastro
with st.sidebar:
    st.header("🐻 Bear Snack")
    st.subheader("Painel de Controle")
    
    with st.expander("👤 Cadastrar Novo Cliente", expanded=False):
        nome_novo = st.text_input("Nome do Cliente")
        tel_novo = st.text_input("WhatsApp (DDD+Número)")
        if st.button("Salvar Cadastro"):
            if nome_novo:
                novo_df = pd.concat([df_c, pd.DataFrame([{'Nome': nome_novo, 'Telefone': tel_novo}])], ignore_index=True)
                novo_df.to_csv(DB_CLIENTES, index=False)
                st.success("Cliente cadastrado!")
                st.rerun()
    
    st.divider()
    st.caption("Versão Final Mobile v2.0")

# --- 5. TELA PRINCIPAL (MAIN) ---
st.markdown("<h2 style='text-align: center; color: #4E3620;'>Livro de Fiados</h2>", unsafe_allow_html=True)

if df_c.empty:
    st.warning("Toque na seta (>) no topo esquerdo para cadastrar seu primeiro cliente!")
else:
    # Seleção de Cliente (selectbox)
    cliente_ativo = st.selectbox("Selecione o Cliente:", ["-- Selecionar --"] + list(df_c['Nome'].unique()))

    if cliente_ativo != "-- Selecionar --":
        # Filtragem de dados do cliente selecionado
        dados_v = df_v[df_v['Cliente'] == cliente_ativo]
        total_compra = dados_v[dados_v['Tipo'] == 'Compra']['Valor'].sum()
        total_pago = dados_v[dados_v['Tipo'] == 'Pagamento']['Valor'].sum()
        saldo_atual = total_compra - total_pago
        tel_cliente = df_c[df_c['Nome'] == cliente_ativo]['Telefone'].values[0]

        # Resumo de Saldo
        st.markdown(f"""
            <div class='balance-card'>
                <p style='margin:0; opacity:0.8;'>Saldo Devedor de {cliente_ativo}</p>
                <h1 style='margin:0; color:white;'>R$ {saldo_atual:,.2f}</h1>
            </div>
        """, unsafe_allow_html=True)

        # Botões de Lançamento Rápido
        col1, col2 = st.columns(2)
        with col1:
            if st.button("➕ COMPRA"): st.session_state.tipo = "Compra"
        with col2:
            if st.button("💵 PAGOU"): st.session_state.tipo = "Pagamento"

        # Formulário de Inserção
        if 'tipo' in st.session_state:
            with st.form("lancamento_venda", clear_on_submit=True):
                st.write(f"### Registrar {st.session_state.tipo}")
                valor_f = st.number_input("Valor (R$)", min_value=0.0, step=1.0)
                item_f = st.text_input("Descrição do Item")
                if st.form_submit_button("SALVAR REGISTRO"):
                    novo_id = datetime.now().strftime("%H%M%S%f")
                    nova_linha = pd.DataFrame([{
                        'ID': novo_id, 'Cliente': cliente_ativo, 'Item': item_f, 
                        'Valor': valor_f, 'Data': datetime.now().strftime("%d/%m"), 'Tipo': st.session_state.tipo
                    }])
                    pd.concat([df_v, nova_linha], ignore_index=True).to_csv(DB_VENDAS, index=False)
                    del st.session_state.tipo
                    st.rerun()

        # Botão de Cobrança WhatsApp
        texto_wa = f"Olá {cliente_ativo}, seu saldo no Bear Snack é de R$ {saldo_atual:,.2f}."
        link_wa = f"https://wa.me/{tel_cliente}?text={urllib.parse.quote(texto_wa)}"
        st.markdown(f'<a href="{link_wa}" target="_blank"><button style="width:100%; background:#25D366; color:white; border:none; padding:15px; border-radius:12px; font-weight:bold; cursor:pointer;">📲 Cobrar no WhatsApp</button></a>', unsafe_allow_html=True)

        # Histórico Detalhado em Cards
        st.write("### Extrato Recente")
        for i, row in dados_v.iloc[::-1].iterrows():
            cor_valor = "#B03020" if row['Tipo'] == "Compra" else "#2e7d32"
            st.markdown(f"""
                <div class="hist-card">
                    <div><b>{row['Item'] if row['Item'] else row['Tipo']}</b><br><small>{row['Data']}</small></div>
                    <div style="color:{cor_valor}; font-weight:bold;">R$ {row['Valor']:,.2f}</div>
                </div>
            """, unsafe_allow_html=True)
            
            # Botão de Excluir Registro Individual
            if st.button("🗑️ Apagar", key=f"del_{row['ID']}"):
                df_v = df_v[df_v['ID'] != row['ID']]
                df_v.to_csv(DB_VENDAS, index=False)
                st.rerun()
