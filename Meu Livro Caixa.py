import streamlit as st
import pandas as pd
import os
import sqlite3
import re
from datetime import datetime
import urllib.parse

# --- 1. CONFIGURAÇÃO E ESTILO ---
st.set_page_config(page_title="Bear Snack Pro", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .stApp { background-color: #FDF5E6; }
    
    /* CONFIGURAÇÃO MANUAL DE ALINHAMENTO DO LOGO */
    [data-testid="stImage"] {
        display: flex;
        justify-content: center;
        margin-left: auto;
        margin-right: auto;
        text-align: center;
    }
    
    [data-testid="stHeader"] { background: rgba(0,0,0,0); }

    .centered-header {
        text-align: center;
        width: 100%;
        margin-top: -20px; 
        margin-bottom: 20px;
    }

    /* Estilização das Abas */
    .stTabs [data-baseweb="tab-list"] { 
        display: flex;
        justify-content: center;
        gap: 8px; 
        background-color: #FDF5E6; 
    }
    .stTabs [data-baseweb="tab"] {
        height: 45px; background-color: #D2B48C; border-radius: 10px 10px 0px 0px;
        color: #4E3620; font-weight: bold; padding: 0px 15px; font-size: 12px;
    }
    .stTabs [aria-selected="true"] { background-color: #4E3620 !important; color: #D2B48C !important; }
    
    /* Cartão de Saldo */
    .balance-card {
        background: linear-gradient(135deg, #B03020 0%, #4E3620 100%);
        color: white; padding: 20px; border-radius: 20px;
        text-align: center; margin-bottom: 15px; border: 2px solid #D2B48C;
    }
    
    /* Botões */
    .stButton > button {
        width: 100%; height: 50px !important; border-radius: 12px !important;
        background-color: #4E3620 !important; color: #D2B48C !important;
        font-weight: bold !important; border: 1px solid #D2B48C !important;
        font-size: 14px !important;
    }
    
    /* Cards do Histórico */
    .item-card {
        background: white; padding: 12px; border-radius: 12px; margin-bottom: 8px;
        display: flex; justify-content: space-between; align-items: center;
        border-left: 6px solid #CD853F;
    }
    </style>
    """, unsafe_allow_html=True)

DB_VENDAS = "vendas_bear_final.csv"
DB_CLIENTES = "clientes_bear_final.csv"
DB_ANTIGO = "Livro Caixa.db"

# --- 2. FUNÇÕES DE DADOS E MIGRAÇÃO ---
def migrar_dados_antigos():
    if os.path.exists(DB_ANTIGO) and not os.path.exists(DB_CLIENTES):
        try:
            conn = sqlite3.connect(DB_ANTIGO)
            query = "SELECT DISTINCT description FROM cashTransaction WHERE description IS NOT NULL"
            df_bruto = pd.read_sql_query(query, conn)
            conn.close()

            clientes_migrados = []
            for item in df_bruto['description']:
                original = str(item).strip()
                if not original: continue

                if original.startswith('@'):
                    nome = original.replace('@', '').strip()
                    clientes_migrados.append({'Nome': nome, 'Telefone': '', 'Categoria': 'Funcionário', 'Periodo': 'N/A', 'Turma': 'N/A', 'Limite': 100.0})
                else:
                    hora_match = re.search(r'(\d{2}:\d{2})', original)
                    if hora_match:
                        hora = hora_match.group(1)
                        nome = original.replace(hora, '').strip()
                        periodo, turma = "Manhã", "1ª Turma"
                        if int(hora.split(':')[0]) >= 12: periodo = "Tarde"
                        clientes_migrados.append({'Nome': nome, 'Telefone': '', 'Categoria': 'Aluno', 'Periodo': periodo, 'Turma': turma, 'Limite': 50.0})
            
            if clientes_migrados:
                pd.DataFrame(clientes_migrados).to_csv(DB_CLIENTES, index=False, encoding='utf-8-sig')
                return True
        except: return False
    return False

def load_data():
    migrar_dados_antigos()
    c = pd.read_csv(DB_CLIENTES) if os.path.exists(DB_CLIENTES) else pd.DataFrame(columns=['Nome', 'Telefone', 'Categoria', 'Periodo', 'Turma', 'Limite'])
    v = pd.read_csv(DB_VENDAS) if os.path.exists(DB_VENDAS) else pd.DataFrame(columns=['ID', 'Cliente', 'Cat_Venda', 'Item', 'Valor', 'Data', 'Tipo'])
    return c, v

df_c, df_v = load_data()

# --- 3. LOGIN ---
if 'logado' not in st.session_state: st.session_state.logado = False

if not st.session_state.logado:
    # CENTRALIZAÇÃO DO LOGO NO LOGIN
    if os.path.exists("logo.png"): 
        st.image("logo.png", width=200)
    else: 
        st.markdown('<h1 class="centered-header">🐻 BEAR SNACK</h1>', unsafe_allow_html=True)
    
    user = st.text_input("Usuário")
    pw = st.text_input("Senha", type="password")
    if st.button("ACESSAR SISTEMA"):
        if user == "admin" and pw == "bear123":
            st.session_state.logado = True
            st.rerun()
        else: st.error("Dados incorretos")
else:
    # --- 4. SIDEBAR ---
    with st.sidebar:
        if st.button("🚪 SAIR"):
            st.session_state.logado = False
            st.rerun()
        st.divider()
        st.subheader("👤 Gerenciar Cliente")
        lista_clientes = ["-- Novo Cadastro --"] + sorted(df_c['Nome'].unique().tolist())
        cliente_para_editar = st.selectbox("🔍 Buscar/Editar Cliente:", options=lista_clientes)

        # Lógica de edição/cadastro simplificada
        val_n, val_t, val_cat, val_lim = "", "", "Aluno", 50.0
        if cliente_para_editar != "-- Novo Cadastro --":
            dados = df_c[df_c['Nome'] == cliente_para_editar].iloc[0]
            val_n, val_t, val_cat, val_lim = dados['Nome'], str(dados['Telefone']), dados['Categoria'], float(dados['Limite'])

        n = st.text_input("Nome", value=val_n)
        t = st.text_input("WhatsApp", value=val_t)
        cat = st.selectbox("Tipo:", ["Aluno", "Funcionário"], index=0 if val_cat == "Aluno" else 1)
        lim = st.number_input("Limite R$", value=val_lim)

        if st.button("SALVAR"):
            if n:
                df_temp = df_c[df_c['Nome'] != cliente_para_editar] if cliente_para_editar != "-- Novo Cadastro --" else df_c
                new_row = pd.DataFrame([{'Nome': n, 'Telefone': t, 'Categoria': cat, 'Periodo': 'Manhã', 'Turma': '1ª Turma', 'Limite': lim}])
                pd.concat([df_temp, new_row], ignore_index=True).to_csv(DB_CLIENTES, index=False)
                st.success("Salvo!")
                st.rerun()

    # --- 5. INTERFACE PRINCIPAL ---
    # CENTRALIZAÇÃO DO LOGO NO TOPO DO SISTEMA
    if os.path.exists("logo.png"): 
        st.image("logo.png", width=150)
    else: 
        st.markdown('<h1 class="centered-header">🐻 Bear Snack</h1>', unsafe_allow_html=True)

    aba_selecionada = st.tabs(["🎓 ALUNOS", "💼 FUNCIONÁRIOS", "📊 DEVEDORES"])
    cliente_final, cat_final = None, None

    with aba_selecionada[0]: # ALUNOS
        c1, c2 = st.columns(2)
        pf = c1.selectbox("Período:", ["Manhã", "Tarde"])
        tf = c2.selectbox("Turma:", ["1ª Turma", "2ª Turma", "3ª Turma"])
        df_fa = df_c[(df_c['Categoria'] == 'Aluno') & (df_c['Periodo'] == pf)]
        sel_a = st.selectbox("Selecione o Aluno:", ["-- Selecionar --"] + sorted(df_fa['Nome'].unique().tolist()))
        if sel_a != "-- Selecionar --": cliente_final, cat_final = sel_a, "Aluno"
        
    with aba_selecionada[1]: # FUNCIONÁRIOS
        sel_f = st.selectbox("Selecione o Funcionário:", ["-- Selecionar --"] + sorted(df_c[df_c['Categoria'] == 'Funcionário']['Nome'].unique().tolist()))
        if sel_f != "-- Selecionar --": cliente_final, cat_final = sel_f, "Funcionário"

    with aba_selecionada[2]: # DEVEDORES
        devedores = []
        for _, r in df_c.iterrows():
            v_cli = df_v[df_v['Cliente'] == r['Nome']]
            saldo = v_cli[v_cli['Tipo'] == 'Compra']['Valor'].sum() - v_cli[v_cli['Tipo'] == 'Pagamento']['Valor'].sum()
            if saldo > 0: devedores.append({'Nome': r['Nome'], 'Divida': saldo})
        
        for d in sorted(devedores, key=lambda x: x['Nome']):
            st.warning(f"{d['Nome']} ➔ R$ {d['Divida']:,.2f}")

    # --- 6. LANÇAMENTOS ---
    if cliente_final:
        v_c = df_v[df_v['Cliente'] == cliente_final]
        divida = v_c[v_c['Tipo'] == 'Compra']['Valor'].sum() - v_c[v_c['Tipo'] == 'Pagamento']['Valor'].sum()
        
        st.markdown(f"""<div class="balance-card">
            <p style="margin:0;">{cliente_final}</p>
            <h1 style="color:white; margin:0;">R$ {divida:,.2f}</h1>
        </div>""", unsafe_allow_html=True)

        col_c, col_p = st.columns(2)
        if col_c.button("➕ COMPRA"): st.session_state.op = "Compra"
        if col_p.button("💵 PAGOU"): st.session_state.op = "Pagamento"

        if 'op' in st.session_state:
            st.subheader(f"Lançar {st.session_state.op}")
            with st.form("lanca_venda"):
                vf = st.number_input("Valor R$", min_value=0.0)
                desc = st.text_input("Item/Obs")
                if st.form_submit_button("CONFIRMAR"):
                    if vf > 0:
                        new_row = pd.DataFrame([{'ID': datetime.now().strftime("%H%M%S"), 'Cliente': cliente_final, 'Cat_Venda': cat_final, 'Item': desc, 'Valor': vf, 'Data': datetime.now().strftime("%d/%m %H:%M"), 'Tipo': st.session_state.op}])
                        pd.concat([df_v, new_row], ignore_index=True).to_csv(DB_VENDAS, index=False)
                        del st.session_state.op
                        st.rerun()
