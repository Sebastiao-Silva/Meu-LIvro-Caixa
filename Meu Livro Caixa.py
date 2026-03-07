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
        width: 100%; height: 50px !important; border-radius: 12px !important;
        background-color: #4E3620 !important; color: #D2B48C !important;
        font-weight: bold !important; border: 1px solid #D2B48C !important;
        font-size: 14px !important;
    }
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

# --- 2. FUNÇÕES DE DADOS ---
def migrar_banco_sqlite():
    if os.path.exists(DB_ANTIGO) and not os.path.exists(DB_CLIENTES):
        try:
            conn = sqlite3.connect(DB_ANTIGO)
            # Busca todas as descrições únicas
            df_sql = pd.read_sql_query("SELECT DISTINCT description FROM cashTransaction", conn)
            conn.close()

            importados = []
            for desc in df_sql['description']:
                nome_bruto = str(desc).strip()
                if not nome_bruto or nome_bruto == 'None': continue

                # Identifica Funcionário
                if nome_bruto.startswith('@'):
                    nome_limpo = nome_bruto.replace('@', '').strip()
                    importados.append({'Nome': nome_limpo, 'Categoria': 'Funcionário', 'Periodo': 'N/A', 'Turma': 'N/A', 'Limite': 100.0, 'Telefone': ''})
                
                # Identifica Aluno (procura horário no texto)
                else:
                    hora_match = re.search(r'(\d{2}:\d{2})', nome_bruto)
                    if hora_match:
                        hora = hora_match.group(1)
                        # Remove o horário e termos como "Bebe" para pegar o nome
                        nome_limpo = nome_bruto.replace(hora, '').replace('bebe', '').replace('Bebe', '').replace('(', '').replace(')', '').strip()
                        
                        periodo = "Manhã"
                        h_int = int(hora.split(':')[0])
                        if h_int >= 12: periodo = "Tarde"
                        
                        importados.append({'Nome': nome_limpo, 'Categoria': 'Aluno', 'Periodo': periodo, 'Turma': '1ª Turma', 'Limite': 50.0, 'Telefone': ''})

            if importados:
                df_final = pd.DataFrame(importados).drop_duplicates(subset=['Nome'])
                df_final.to_csv(DB_CLIENTES, index=False, encoding='utf-8-sig')
                return True
        except: return False
    return False

def carregar_dados():
    migrar_banco_sqlite()
    c = pd.read_csv(DB_CLIENTES) if os.path.exists(DB_CLIENTES) else pd.DataFrame(columns=['Nome', 'Categoria', 'Periodo', 'Turma', 'Limite', 'Telefone'])
    v = pd.read_csv(DB_VENDAS) if os.path.exists(DB_VENDAS) else pd.DataFrame(columns=['ID', 'Cliente', 'Item', 'Valor', 'Data', 'Tipo'])
    return c, v

df_c, df_v = carregar_dados()

# --- 3. LOGIN ---
if 'logado' not in st.session_state: st.session_state.logado = False

if not st.session_state.logado:
    st.markdown("<h2 style='text-align:center;'>🐻 BEAR SNACK LOGIN</h2>", unsafe_allow_html=True)
    u = st.text_input("Usuário")
    p = st.text_input("Senha", type="password")
    if st.button("ACESSAR"):
        if u == "admin" and p == "bear123":
            st.session_state.logado = True
            st.rerun()
        else: st.error("Dados incorretos")
else:
    # --- 4. INTERFACE ---
    st.markdown("<h1 style='text-align:center;'>🐻 Bear Snack</h1>", unsafe_allow_html=True)
    
    # Sidebar para gerir novos clientes ou sair
    with st.sidebar:
        if st.button("🚪 SAIR"):
            st.session_state.logado = False
            st.rerun()
        st.divider()
        st.write("### Novo Cadastro")
        novo_n = st.text_input("Nome")
        novo_cat = st.selectbox("Tipo", ["Aluno", "Funcionário"])
        if st.button("Salvar"):
            nova_linha = pd.DataFrame([{'Nome': novo_n, 'Categoria': novo_cat, 'Periodo': 'Manhã', 'Turma': '1ª Turma', 'Limite': 50.0, 'Telefone': ''}])
            df_c = pd.concat([df_c, nova_linha], ignore_index=True)
            df_c.to_csv(DB_CLIENTES, index=False)
            st.rerun()

    # ABAS PRINCIPAIS
    abas = st.tabs(["🎓 ALUNOS", "💼 FUNCIONÁRIOS", "📊 DEVEDORES"])
    cliente_selecionado = None

    with abas[0]: # ALUNOS
        per = st.selectbox("Período", ["Manhã", "Tarde"])
        filtro_a = df_c[(df_c['Categoria'] == 'Aluno') & (df_c['Periodo'] == per)]
        sel_a = st.selectbox("Escolha o Aluno", ["--"] + sorted(filtro_a['Nome'].unique().tolist()))
        if sel_a != "--": cliente_selecionado = sel_a

    with abas[1]: # FUNCIONÁRIOS
        filtro_f = df_c[df_c['Categoria'] == 'Funcionário']
        sel_f = st.selectbox("Escolha o Funcionário", ["--"] + sorted(filtro_f['Nome'].unique().tolist()))
        if sel_f != "--": cliente_selecionado = sel_f

    with abas[2]: # DEVEDORES
        st.write("### Lista de Saldos")
        for _, r in df_c.iterrows():
            v_cli = df_v[df_v['Cliente'] == r['Nome']]
            saldo = v_cli[v_cli['Tipo'] == 'Compra']['Valor'].sum() - v_cli[v_cli['Tipo'] == 'Pagamento']['Valor'].sum()
            if saldo > 0:
                st.warning(f"{r['Nome']}: R$ {saldo:.2f}")

    # --- 5. OPERAÇÕES ---
    if cliente_selecionado:
        v_cli = df_v[df_v['Cliente'] == cliente_selecionado]
        saldo = v_cli[v_cli['Tipo'] == 'Compra']['Valor'].sum() - v_cli[v_cli['Tipo'] == 'Pagamento']['Valor'].sum()
        
        st.markdown(f'<div class="balance-card"><h2>{cliente_selecionado}</h2><h1>R$ {saldo:,.2f}</h1></div>', unsafe_allow_html=True)

        if 'v_soma' not in st.session_state: st.session_state.v_soma = 0.0
        
        # Botões de produtos rápidos
        st.write("### Lançar Compra")
        c1, c2, c3 = st.columns(3)
        precos = {"Salgado": 8.0, "Suco": 6.0, "Refri": 6.0, "Pipoca": 7.0, "Água": 4.0, "Biscoito": 4.0}
        for i, (item, valor) in enumerate(precos.items()):
            col = [c1, c2, c3][i % 3]
            if col.button(f"{item}\nR${valor}"):
                st.session_state.v_soma += valor
                st.rerun()

        with st.form("form_lanca"):
            v_total = st.number_input("Valor Final", value=st.session_state.v_soma)
            tipo = st.radio("Tipo de Lançamento", ["Compra", "Pagamento"])
            if st.form_submit_button("CONFIRMAR"):
                nova_v = pd.DataFrame([{
                    'ID': datetime.now().strftime("%Y%m%d%H%M%S"),
                    'Cliente': cliente_selecionado, 'Item': tipo,
                    'Valor': v_total, 'Data': datetime.now().strftime("%d/%m %H:%M"), 'Tipo': tipo
                }])
                pd.concat([df_v, nova_v], ignore_index=True).to_csv(DB_VENDAS, index=False)
                st.session_state.v_soma = 0.0
                st.success("Salvo com sucesso!")
                st.rerun()
