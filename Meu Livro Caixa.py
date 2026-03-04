import streamlit as st
import pandas as pd
import os
from datetime import datetime
import plotly.express as px

# --- CONFIGURAÇÕES E ESTILO ---
st.set_page_config(page_title="Livro Caixa Pro", layout="wide")

# CSS Avançado para esconder menus do Streamlit e parecer App Nativo
st.markdown("""
    <style>
    .stApp { background-color: #f0f2f5; }
    [data-testid="stMetricValue"] { font-size: 24px; }
    .main-card { background: white; padding: 20px; border-radius: 15px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
    .entrada-txt { color: #2e7d32; font-weight: bold; }
    .saida-txt { color: #d32f2f; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES DE DADOS (BANCO DE DADOS) ---
DB_FILE = "dados_caixa.csv"

def carregar_dados():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=['ID', 'Data', 'Descricao', 'Categoria', 'Valor', 'Tipo'])

def salvar_dados(df):
    df.to_csv(DB_FILE, index=False)

# Inicialização
if 'df' not in st.session_state:
    st.session_state.df = carregar_dados()

# --- NAVEGAÇÃO POR ABAS (COMO NO APP) ---
aba1, aba2, aba3 = st.tabs(["📊 Resumo", "📝 Lançamentos", "📑 Relatório Detalhado"])

# --- ABA 1: RESUMO E GRÁFICOS ---
with aba1:
    df = st.session_state.df
    total_in = df[df['Tipo'] == 'Entrada']['Valor'].sum()
    total_out = df[df['Tipo'] == 'Saída']['Valor'].sum()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Entradas", f"R$ {total_in:,.2f}")
    col2.metric("Total Saídas", f"R$ {total_out:,.2f}")
    col3.metric("Saldo em Caixa", f"R$ {(total_in - total_out):,.2f}")

    if not df.empty:
        st.subheader("Fluxo de Caixa")
        fig = px.pie(df, values='Valor', names='Tipo', color='Tipo',
                     color_discrete_map={'Entrada':'#4CAF50', 'Saída':'#F44336'}, hole=.4)
        st.plotly_chart(fig, use_container_width=True)

# --- ABA 2: NOVO LANÇAMENTO ---
with aba2:
    st.subheader("Novo Registro")
    with st.container():
        col_a, col_b = st.columns(2)
        with col_a:
            tipo = st.radio("Tipo de Movimentação", ["Entrada", "Saída"], horizontal=True)
            valor = st.number_input("Valor (R$)", min_value=0.01, step=0.50)
        with col_b:
            data = st.date_input("Data do Evento", datetime.now())
            cat = st.selectbox("Categoria", ["Venda", "Serviço", "Aluguel", "Salário", "Fornecedor", "Impostos", "Outros"])
        
        desc = st.text_area("Descrição / Detalhes")
        
        if st.button("💾 SALVAR NO LIVRO CAIXA", use_container_width=True):
            novo_id = len(st.session_state.df) + 1
            novo_dado = pd.DataFrame([[novo_id, data.strftime("%Y-%m-%d"), desc, cat, valor, tipo]], 
                                     columns=['ID', 'Data', 'Descricao', 'Categoria', 'Valor', 'Tipo'])
            st.session_state.df = pd.concat([st.session_state.df, novo_dado], ignore_index=True)
            salvar_dados(st.session_state.df)
            st.success("Lançamento salvo com sucesso!")
            st.rerun()

# --- ABA 3: HISTÓRICO E EXCLUSÃO ---
with aba3:
    st.subheader("Histórico de Movimentações")
    # Filtro rápido
    busca = st.text_input("Buscar por descrição...")
    df_filtrado = st.session_state.df
    if busca:
        df_filtrado = df_filtrado[df_filtrado['Descricao'].str.contains(busca, case=False)]
    
    st.dataframe(df_filtrado.sort_values(by="Data", ascending=False), use_container_width=True)
    
    if st.checkbox("Preciso apagar um erro"):
        id_del = st.number_input("Digite o ID do registro para excluir", min_value=1)
        if st.button("Confirmar Exclusão"):
            st.session_state.df = st.session_state.df[st.session_state.df.ID != id_del]
            salvar_dados(st.session_state.df)
            st.rerun()