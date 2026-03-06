import streamlit as st
import pandas as pd
import os
from datetime import datetime
import urllib.parse

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="Bear Snack Pro", layout="centered", initial_sidebar_state="collapsed")

# --- 2. CSS BEAR SNACK ---
st.markdown("""
    <style>
    .stApp { background-color: #FDF5E6; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; background-color: #FDF5E6; }
    .stTabs [data-baseweb="tab"] {
        height: 45px; background-color: #D2B48C; border-radius: 10px 10px 0px 0px;
        color: #4E3620; font-weight: bold; padding: 0px 15px; font-size: 12px;
    }
    .stTabs [aria-selected="true"] { background-color: #4E3620 !important; color: #D2B48C !important; }
    .balance-card {
        background: linear-gradient(135deg, #B03020 0%, #4E3620 100%);
        color: white; padding: 20px; border-radius: 20px;
        text-align: center; margin-bottom: 15px; border: 2px solid #D2B48C;
    }
    .stButton > button {
        width: 100%; height: 55px !important; border-radius: 15px !important;
        background-color: #4E3620 !important; color: #D2B48C !important;
        font-weight: bold !important; border: 2px solid #D2B48C !important;
    }
    .item-card {
        background: white; padding: 12px; border-radius: 12px; margin-bottom: 8px;
        display: flex; justify-content: space-between; align-items: center;
        border-left: 6px solid #CD853F;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. LOGIN ---
if 'logado' not in st.session_state: st.session_state.logado = False
if not st.session_state.logado:
    st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
    if os.path.exists("logo.png"): st.image("logo.png", width=180)
    else: st.title("🐻 BEAR SNACK")
    st.markdown("</div>", unsafe_allow_html=True)
    user = st.text_input("Usuário")
    pw = st.text_input("Senha", type="password")
    if st.button("ACESSAR SISTEMA"):
        if user == "admin" and pw == "bear123":
            st.session_state.logado = True
            st.rerun()
        else: st.error("Dados incorretos")
else:
    DB_VENDAS, DB_CLIENTES = "vendas_bear_final.csv", "clientes_bear_final.csv"

    def load():
        if os.path.exists(DB_CLIENTES):
            c = pd.read_csv(DB_CLIENTES)
            for col in ['Categoria', 'Periodo', 'Turma', 'Limite']:
                if col not in c.columns: c[col] = 50.0 if col == 'Limite' else "N/A"
        else: c = pd.DataFrame(columns=['Nome', 'Telefone', 'Categoria', 'Periodo', 'Turma', 'Limite'])
        if os.path.exists(DB_VENDAS):
            v = pd.read_csv(DB_VENDAS)
            if 'Cat_Venda' not in v.columns: v['Cat_Venda'] = 'Aluno'
        else: v = pd.DataFrame(columns=['ID', 'Cliente', 'Cat_Venda', 'Item', 'Valor', 'Data', 'Tipo'])
        return c, v

    df_c, df_v = load()

    with st.sidebar:
        if st.button("🚪 SAIR"):
            st.session_state.logado = False
            st.rerun()
        st.divider()
        st.subheader("👤 Novo Cadastro")
        n, t = st.text_input("Nome"), st.text_input("WhatsApp")
        cat = st.selectbox("Tipo:", ["Aluno", "Funcionário"])
        lim = st.number_input("Limite R$", value=50.0)
        p, tur = "N/A", "N/A"
        if cat == "Aluno":
            p = st.selectbox("Período:", ["Manhã", "Tarde"])
            tur = st.selectbox("Turma:", ["1ª Turma", "2ª Turma", "3ª Turma"])
        if st.button("CADASTRAR"):
            if n:
                new_c = pd.concat([df_c, pd.DataFrame([{'Nome': n, 'Telefone': t, 'Categoria': cat, 'Periodo': p, 'Turma': tur, 'Limite': lim}])], ignore_index=True)
                new_c.to_csv(DB_CLIENTES, index=False)
                st.rerun()

    st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
    if os.path.exists("logo.png"): st.image("logo.png", width=100)
    else: st.title("🐻 Bear Snack")
    st.markdown("</div>", unsafe_allow_html=True)

    # --- CONTROLE DE ABAS ---
    # Usamos o index para saber em qual aba o usuário está
    aba_selecionada = st.tabs(["🎓 ALUNOS", "💼 FUNCIONÁRIOS", "📊 DEVEDORES"])
    
    cliente_final, cat_final = None, None

    # ABA ALUNOS
    with aba_selecionada[0]:
        c1, c2 = st.columns(2)
        with c1: pf = st.selectbox("Período:", ["Manhã", "Tarde"], key="fa_p")
        with c2: tf = st.selectbox("Turma:", ["1ª Turma", "2ª Turma", "3ª Turma"], key="fa_t")
        df_fa = df_c[(df_c['Categoria'] == 'Aluno') & (df_c['Periodo'] == pf) & (df_c['Turma'] == tf)]
        sel_a = st.selectbox("Selecione o Aluno:", ["-- Selecionar --"] + list(df_fa['Nome'].unique()), key="sa_a")
        if sel_a != "-- Selecionar --":
            cliente_final, cat_final = sel_a, "Aluno"
        
    # ABA FUNCIONÁRIOS
    with aba_selecionada[1]:
        sel_f = st.selectbox("Selecione o Funcionário:", ["-- Selecionar --"] + list(df_c[df_c['Categoria'] == 'Funcionário']['Nome'].unique()), key="sf_f")
        if sel_f != "-- Selecionar --":
            cliente_final, cat_final = sel_f, "Funcionário"

    # ABA DEVEDORES
    with aba_selecionada[2]:
        # Aqui NUNCA preenchemos cliente_final, garantindo que os botões sumam
        devedores_lista = []
        total_geral = 0
        for _, r in df_c.iterrows():
            v_cli = df_v[(df_v['Cliente'] == r['Nome']) & (df_v['Cat_Venda'] == r['Categoria'])]
            saldo = v_cli[v_cli['Tipo'] == 'Compra']['Valor'].sum() - v_cli[v_cli['Tipo'] == 'Pagamento']['Valor'].sum()
            if saldo > 0:
                devedores_lista.append({'Nome': r['Nome'], 'Divida': saldo, 'Cat': r['Categoria']})
                total_geral += saldo
        
        st.markdown(f"""<div style="background-color:#4E3620; color:#D2B48C; padding:15px; border-radius:15px; text-align:center; margin-bottom:20px;"><small>TOTAL A RECEBER</small><br><b style="font-size:24px;">R$ {total_geral:,.2f}</b></div>""", unsafe_allow_html=True)
        
        dev_ord = sorted(devedores_lista, key=lambda x: x['Nome'])
        for idx, d in enumerate(dev_ord):
            if st.button(f"{d['Nome']} ({d['Cat']}) ➔ R$ {d['Divida']:,.2f}", key=f"d_btn_{idx}"):
                st.session_state.dev_sel_relatorio = d
        
        if 'dev_sel_relatorio' in st.session_state:
            ds = st.session_state.dev_sel_relatorio
            st.markdown(f"""<div class="balance-card"><p style="margin:0;">{ds['Nome']} ({ds['Cat']})</p><h1 style="color:white; margin:0;">R$ {ds['Divida']:,.2f}</h1></div>""", unsafe_allow_html=True)
            if st.button("FECHAR DETALHES"):
                del st.session_state.dev_sel_relatorio
                st.rerun()

    # --- ÁREA DE LANÇAMENTO (RESTAURADA PARA ALUNOS E FUNCIONÁRIOS) ---
    
