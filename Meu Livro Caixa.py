import streamlit as st
import pandas as pd
import os
import sqlite3
import re
from datetime import datetime
import urllib.parse

# --- 1. CONFIGURAÇÃO DE PÁGINA ---
st.set_page_config(page_title="Bear Snack Pro", layout="centered")

# Estilo Visual Fixo (Não altera o layout que você aprovou)
st.markdown("""
    <style>
    .stApp { background-color: #FDF5E6; }
    .balance-card {
        background: linear-gradient(135deg, #B03020 0%, #4E3620 100%);
        color: white; padding: 20px; border-radius: 20px;
        text-align: center; margin-bottom: 15px; border: 2px solid #D2B48C;
    }
    .stButton > button {
        width: 100%; border-radius: 12px !important;
        background-color: #4E3620 !important; color: #D2B48C !important;
        font-weight: bold !important;
    }
    </style>
    """, unsafe_allow_html=True)

# Nomes dos arquivos de persistência
DB_VENDAS = "vendas_bear_final.csv"
DB_CLIENTES = "clientes_bear_final.csv"
DB_SQLITE = "Livro Caixa.db"

# --- 2. FUNÇÃO DE MIGRAÇÃO (RODA APENAS SE O CSV NÃO EXISTIR) ---
def realizar_migracao():
    # SÓ executa se o banco antigo existir E o novo CSV de clientes ainda não existir
    if os.path.exists(DB_SQLITE) and not os.path.exists(DB_CLIENTES):
        try:
            conn = sqlite3.connect(DB_SQLITE)
            # Busca as descrições que contêm os nomes/horários
            query = "SELECT DISTINCT description FROM cashTransaction WHERE description IS NOT NULL"
            df_sql = pd.read_sql_query(query, conn)
            conn.close()

            novos_clientes = []
            for item in df_sql['description']:
                txt = str(item).strip()
                if not txt or txt.lower() == 'none': continue

                # Regra: Funcionário (@)
                if txt.startswith('@'):
                    nome = txt.replace('@', '').strip()
                    novos_clientes.append({'Nome': nome, 'Telefone': '', 'Categoria': 'Funcionário', 'Periodo': 'N/A', 'Turma': 'N/A', 'Limite': 100.0})
                
                # Regra: Alunos (Extração de Horário)
                else:
                    hora_match = re.search(r'(\d{2}:\d{2})', txt)
                    if hora_match:
                        hora = hora_match.group(1)
                        nome = txt.replace(hora, '').strip()
                        periodo, turma = "Manhã", "1ª Turma"
                        
                        # Classificação por horários conforme solicitado
                        h_prefix = int(hora.split(':')[0])
                        if hora in ['08:40', '09:00']: periodo, turma = "Manhã", "1ª Turma"
                        elif hora == '09:30': periodo, turma = "Manhã", "2ª Turma"
                        elif hora == '10:00': periodo, turma = "Manhã", "3ª Turma"
                        elif h_prefix >= 15: periodo, turma = "Tarde", "1ª Turma"
                        
                        novos_clientes.append({'Nome': nome, 'Telefone': '', 'Categoria': 'Aluno', 'Periodo': periodo, 'Turma': turma, 'Limite': 50.0})
            
            if novos_clientes:
                df_c_migrado = pd.DataFrame(novos_clientes).drop_duplicates(subset=['Nome'])
                df_c_migrado.to_csv(DB_CLIENTES, index=False, encoding='utf-8-sig')
                return True
        except Exception as e:
            st.error(f"Erro na migração técnica: {e}")
    return False

# --- 3. CARREGAMENTO DE DADOS ---
def carregar_bancos():
    # Garante que o arquivo de vendas sempre exista
    if not os.path.exists(DB_VENDAS):
        pd.DataFrame(columns=['ID', 'Cliente', 'Cat_Venda', 'Item', 'Valor', 'Data', 'Tipo']).to_csv(DB_VENDAS, index=False)
    
    # Executa a migração se necessário
    realizar_migracao()
    
    # Carrega os arquivos
    if os.path.exists(DB_CLIENTES):
        df_c = pd.read_csv(DB_CLIENTES)
    else:
        df_c = pd.DataFrame(columns=['Nome', 'Telefone', 'Categoria', 'Periodo', 'Turma', 'Limite'])
        
    df_v = pd.read_csv(DB_VENDAS)
    return df_c, df_v

df_c, df_v = carregar_bancos()

# --- 4. SISTEMA DE LOGIN ---
if 'logado' not in st.session_state: st.session_state.logado = False

if not st.session_state.logado:
    st.title("🐻 Bear Snack - Acesso")
    u = st.text_input("Usuário")
    p = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if u == "admin" and p == "bear123":
            st.session_state.logado = True
            st.rerun()
        else: st.error("Incorreto")
else:
    # --- 5. INTERFACE PRINCIPAL ---
    st.title("🐻 Bear Snack Pro")
    
    abas = st.tabs(["🎓 ALUNOS", "💼 FUNCIONÁRIOS", "📊 DEVEDORES"])
    cliente_ativo = None

    with abas[0]: # Alunos
        col1, col2 = st.columns(2)
        per = col1.selectbox("Período", ["Manhã", "Tarde"])
        df_f = df_c[(df_c['Categoria'] == 'Aluno') & (df_c['Periodo'] == per)]
        sel = st.selectbox("Escolha o Aluno", ["--"] + sorted(df_f['Nome'].unique().tolist()))
        if sel != "--": cliente_ativo = sel

    with abas[1]: # Funcionários
        df_func = df_c[df_c['Categoria'] == 'Funcionário']
        sel_f = st.selectbox("Escolha o Funcionário", ["--"] + sorted(df_func['Nome'].unique().tolist()))
        if sel_f != "--": cliente_ativo = sel_f

    with abas[2]: # Devedores
        st.subheader("Saldos Pendentes")
        for _, row in df_c.iterrows():
            v_cli = df_v[df_v['Cliente'] == row['Nome']]
            saldo = v_cli[v_cli['Tipo'] == 'Compra']['Valor'].sum() - v_cli[v_cli['Tipo'] == 'Pagamento']['Valor'].sum()
            if saldo > 0:
                st.warning(f"{row['Nome']}: R$ {saldo:.2f}")

    # --- 6. LANÇAMENTOS ---
    if cliente_ativo:
        v_cli = df_v[df_v['Cliente'] == cliente_ativo]
        saldo = v_cli[v_cli['Tipo'] == 'Compra']['Valor'].sum() - v_cli[v_cli['Tipo'] == 'Pagamento']['Valor'].sum()
        
        st.markdown(f'<div class="balance-card"><h2>{cliente_ativo}</h2><h1>R$ {saldo:,.2f}</h1></div>', unsafe_allow_html=True)

        if 'v_soma' not in st.session_state: st.session_state.v_soma = 0.0
        
        st.write("### Adicionar Itens")
        itens = {"Salgado": 8.0, "Suco": 6.0, "Refrigerante": 6.0, "Pipoca": 7.0, "Água": 4.0}
        c_i = st.columns(3)
        for i, (nome, preco) in enumerate(itens.items()):
            if c_i[i%3].button(f"{nome}\nR${preco}"):
                st.session_state.v_soma += preco
                st.rerun()

        with st.form("lanca"):
            valor_final = st.number_input("Valor total", value=st.session_state.v_soma)
            tipo_op = st.radio("Operação", ["Compra", "Pagamento"])
            if st.form_submit_button("Confirmar no Sistema"):
                nova_venda = pd.DataFrame([{
                    'ID': datetime.now().strftime("%Y%m%d%H%M%S"),
                    'Cliente': cliente_ativo, 'Cat_Venda': 'N/A',
                    'Item': tipo_op, 'Valor': valor_final,
                    'Data': datetime.now().strftime("%d/%m %H:%M"), 'Tipo': tipo_op
                }])
                pd.concat([df_v, nova_venda], ignore_index=True).to_csv(DB_VENDAS, index=False)
                st.session_state.v_soma = 0.0
                st.success("Registrado!")
                st.rerun()

    # Sidebar Admin
    with st.sidebar:
        if st.button("Sair"):
            st.session_state.logado = False
            st.rerun()
