import streamlit as st
import pandas as pd
import os
import sqlite3
import re
from datetime import datetime
import urllib.parse

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="Bear Snack Pro", layout="centered", initial_sidebar_state="collapsed")

# Estilo visual mantido
st.markdown("""
    <style>
    .stApp { background-color: #FDF5E6; }
    .balance-card {
        background: linear-gradient(135deg, #B03020 0%, #4E3620 100%);
        color: white; padding: 20px; border-radius: 20px;
        text-align: center; margin-bottom: 15px; border: 2px solid #D2B48C;
    }
    .stButton > button {
        width: 100%; height: 50px !important; border-radius: 12px !important;
        background-color: #4E3620 !important; color: #D2B48C !important;
        font-weight: bold !important; border: 1px solid #D2B48C !important;
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

# --- 2. FUNÇÃO DE MIGRAÇÃO COM DIAGNÓSTICO ---
def migrar_dados():
    # Se o CSV já existe, não migra de novo para não duplicar
    if os.path.exists(DB_CLIENTES):
        return False, "O ficheiro de clientes já existe."

    # Verifica se o arquivo .db está presente
    if not os.path.exists(DB_ANTIGO):
        return False, f"Ficheiro '{DB_ANTIGO}' não encontrado na pasta."

    try:
        conn = sqlite3.connect(DB_ANTIGO)
        # Tenta ler da tabela 'cashTransaction'
        query = "SELECT DISTINCT description FROM cashTransaction WHERE description IS NOT NULL"
        df_bruto = pd.read_sql_query(query, conn)
        conn.close()

        clientes_migrados = []
        for item in df_bruto['description']:
            original = str(item).strip()
            if not original or original == 'None': continue

            # Regra Funcionários (@)
            if original.startswith('@'):
                nome = original.replace('@', '').strip()
                clientes_migrados.append({
                    'Nome': nome, 'Telefone': '', 'Categoria': 'Funcionário', 
                    'Periodo': 'N/A', 'Turma': 'N/A', 'Limite': 100.0
                })
            
            # Regra Alunos (Horários)
            else:
                hora_match = re.search(r'(\d{2}:\d{2})', original)
                if hora_match:
                    hora = hora_match.group(1)
                    nome = original.replace(hora, '').strip()
                    periodo, turma = "Manhã", "1ª Turma"
                    
                    # Classificação por horários
                    h_int = int(hora.split(':')[0])
                    if hora in ['08:40', '09:00']: periodo, turma = "Manhã", "1ª Turma"
                    elif hora == '09:30': periodo, turma = "Manhã", "2ª Turma"
                    elif hora == '10:00': periodo, turma = "Manhã", "3ª Turma"
                    elif h_int >= 15: periodo, turma = "Tarde", "1ª Turma"
                    
                    clientes_migrados.append({
                        'Nome': nome, 'Telefone': '', 'Categoria': 'Aluno', 
                        'Periodo': periodo, 'Turma': turma, 'Limite': 50.0
                    })

        if clientes_migrados:
            df_final = pd.DataFrame(clientes_migrados).drop_duplicates(subset=['Nome'])
            df_final.to_csv(DB_CLIENTES, index=False, encoding='utf-8-sig')
            return True, f"Sucesso! {len(df_final)} clientes importados."
        else:
            return False, "O banco de dados antigo está vazio ou não tem nomes válidos."
            
    except Exception as e:
        return False, f"Erro ao ler o banco de dados: {e}"

# --- 3. CARGA DE DADOS ---
def load_data():
    if os.path.exists(DB_CLIENTES):
        c = pd.read_csv(DB_CLIENTES)
    else:
        c = pd.DataFrame(columns=['Nome', 'Telefone', 'Categoria', 'Periodo', 'Turma', 'Limite'])
    
    if os.path.exists(DB_VENDAS):
        v = pd.read_csv(DB_VENDAS)
    else:
        v = pd.DataFrame(columns=['ID', 'Cliente', 'Cat_Venda', 'Item', 'Valor', 'Data', 'Tipo'])
    
    return c, v

df_c, df_v = load_data()

# --- 4. INTERFACE DE LOGIN E MENSAGENS ---
if 'logado' not in st.session_state: st.session_state.logado = False

if not st.session_state.logado:
    st.title("🐻 BEAR SNACK LOGIN")
    user = st.text_input("Usuário")
    pw = st.text_input("Senha", type="password")
    
    if st.button("ACESSAR"):
        if user == "admin" and pw == "bear123":
            st.session_state.logado = True
            st.rerun()
        else: st.error("Dados incorretos")
    
    # Botão de Importação Manual (Caso o automático falhe)
    st.divider()
    st.info("Se os dados não apareceram, clique abaixo:")
    if st.button("🔄 TENTAR IMPORTAR LIVRO CAIXA.DB AGORA"):
        sucesso, msg = migrar_dados()
        if sucesso: st.success(msg)
        else: st.warning(msg)

else:
    # --- RESTANTE DO SISTEMA (TABS E LANÇAMENTOS) ---
    st.markdown("<div style='text-align:center;'><h1>🐻 Bear Snack</h1></div>", unsafe_allow_html=True)
    
    aba_selecionada = st.tabs(["🎓 ALUNOS", "💼 FUNCIONÁRIOS", "📊 DEVEDORES"])
    cliente_final, cat_final = None, None

    with aba_selecionada[0]:
        c1, c2 = st.columns(2)
        with c1: pf = st.selectbox("Período:", ["Manhã", "Tarde"], key="fa_p")
        with c2: tf = st.selectbox("Turma:", ["1ª Turma", "2ª Turma", "3ª Turma"], key="fa_t")
        df_fa = df_c[(df_c['Categoria'] == 'Aluno') & (df_c['Periodo'] == pf)] # Simplificado para teste
        sel_a = st.selectbox("Selecione o Aluno:", ["-- Selecionar --"] + sorted(df_fa['Nome'].unique().tolist()), key="sa_a")
        if sel_a != "-- Selecionar --": cliente_final, cat_final = sel_a, "Aluno"

    with aba_selecionada[1]:
        df_f = df_c[df_c['Categoria'] == 'Funcionário']
        sel_f = st.selectbox("Selecione o Funcionário:", ["-- Selecionar --"] + sorted(df_f['Nome'].unique().tolist()), key="sf_f")
        if sel_f != "-- Selecionar --": cliente_final, cat_final = sel_f, "Funcionário"

    # --- ÁREA DE LANÇAMENTO (Igual ao anterior) ---
    if cliente_final:
        # Lógica de cálculo de saldo e botões de produtos...
        v_c = df_v[(df_v['Cliente'] == cliente_final)]
        divida = v_c[v_c['Tipo'] == 'Compra']['Valor'].sum() - v_c[v_c['Tipo'] == 'Pagamento']['Valor'].sum()
        
        st.markdown(f"""<div class="balance-card"><h2>{cliente_final}</h2><h1>R$ {divida:,.2f}</h1></div>""", unsafe_allow_html=True)
        
        # Botões de produtos em grade
        produtos = {"Água": 4.0, "Biscoito": 4.0, "Fruta": 4.0, "Pipoca": 7.0, "Refrigerante": 6.0, "Salgado": 8.0, "Suco": 6.0, "Suco Natural": 7.0}
        
        if 'val_temp' not in st.session_state: st.session_state.val_temp = 0.0
        
        cols = st.columns(2)
        for i, (prod, preco) in enumerate(produtos.items()):
            if cols[i%2].button(f"{prod} (R$ {preco:.2f})"):
                st.session_state.val_temp += preco
                st.rerun()
        
        with st.form("confirmar"):
            vf = st.number_input("Total", value=st.session_state.val_temp)
            if st.form_submit_button("Confirmar Compra"):
                nid = datetime.now().strftime("%Y%m%d%H%M%S")
                new_v = pd.DataFrame([{'ID': nid, 'Cliente': cliente_final, 'Cat_Venda': cat_final, 'Item': 'Compra', 'Valor': vf, 'Data': datetime.now().strftime("%d/%m"), 'Tipo': 'Compra'}])
                pd.concat([df_v, new_row], ignore_index=True).to_csv(DB_VENDAS, index=False)
                st.session_state.val_temp = 0.0
                st.rerun()

    # Barra lateral para gerir clientes
    with st.sidebar:
        st.write("### Painel Administrativo")
        if st.button("LIMPAR TODOS OS CLIENTES E TENTAR IMPORTAR NOVAMENTE"):
            if os.path.exists(DB_CLIENTES): os.remove(DB_CLIENTES)
            st.rerun()
