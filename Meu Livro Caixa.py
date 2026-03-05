import streamlit as st
import pandas as pd
import os
from datetime import datetime
import urllib.parse

# --- 1. CONFIGURAÇÃO (PRESERVADA) ---
st.set_page_config(page_title="Bear Snack", layout="centered", initial_sidebar_state="collapsed")

# --- 2. O SEU CSS BEAR SNACK (BLOQUEADO) ---
st.markdown("""
    <style>
    .stApp { background-color: #FDF5E6; }
    .block-container { padding-top: 2rem !important; }
    
    .stTabs [data-baseweb="tab-list"] { gap: 10px; background-color: #FDF5E6; }
    .stTabs [data-baseweb="tab"] {
        height: 50px; background-color: #D2B48C; border-radius: 10px 10px 0px 0px;
        color: #4E3620; font-weight: bold; padding: 0px 20px;
    }
    .stTabs [aria-selected="true"] { background-color: #4E3620 !important; color: #D2B48C !important; }

    .balance-card {
        background: linear-gradient(135deg, #B03020 0%, #4E3620 100%);
        color: white; padding: 25px; border-radius: 20px;
        text-align: center; margin-bottom: 20px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.2); border: 2px solid #D2B48C;
    }

    .stButton > button {
        width: 100%; height: 60px !important; border-radius: 15px !important;
        background-color: #4E3620 !important; color: #D2B48C !important;
        font-weight: bold !important; border: 2px solid #D2B48C !important;
    }
    
    .item-card {
        background: white; padding: 15px; border-radius: 15px; margin-bottom: 12px;
        display: flex; justify-content: space-between; align-items: center;
        border-left: 8px solid #CD853F;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CONTROLE DE ACESSO ---
if 'logado' not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
    if os.path.exists("logo.png"):
        st.image("logo.png", width=180)
    else:
        st.title("🐻 BEAR SNACK")
    st.markdown("</div>", unsafe_allow_html=True)
    
    with st.container():
        user = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        if st.button("ACESSAR SISTEMA"):
            if user == "admin" and password == "bear123":
                st.session_state.logado = True
                st.rerun()
            else:
                st.error("Dados incorretos")

# --- 4. APP PRINCIPAL ---
else:
    DB_VENDAS = "vendas_bear_final.csv"
    DB_CLIENTES = "clientes_bear_final.csv"

    def load():
        if os.path.exists(DB_CLIENTES):
            c = pd.read_csv(DB_CLIENTES)
            # Garante que as novas colunas existam no arquivo CSV
            for col in ['Categoria', 'Periodo', 'Turma']:
                if col not in c.columns: c[col] = ""
        else:
            c = pd.DataFrame(columns=['Nome', 'Telefone', 'Categoria', 'Periodo', 'Turma'])
            
        v = pd.read_csv(DB_VENDAS) if os.path.exists(DB_VENDAS) else pd.DataFrame(columns=['ID', 'Cliente', 'Item', 'Valor', 'Data', 'Tipo'])
        return c, v

    df_c, df_v = load()

    with st.sidebar:
        if st.button("🚪 SAIR"):
            st.session_state.logado = False
            st.rerun()
        st.divider()
        st.subheader("👤 Novo Cadastro")
        n = st.text_input("Nome")
        t = st.text_input("WhatsApp")
        cat = st.selectbox("Tipo:", ["Aluno", "Funcionário"])
        
        # CAMPOS CONDICIONAIS PARA ALUNO
        periodo = ""
        turma = ""
        if cat == "Aluno":
            periodo = st.selectbox("Período:", ["Manhã", "Tarde"])
            turma = st.selectbox("Turma:", ["1ª Turma", "2ª Turma", "3ª Turma"])

        if st.button("CADASTRAR"):
            if n:
                novo_reg = {
                    'Nome': n, 
                    'Telefone': t, 
                    'Categoria': cat, 
                    'Periodo': periodo if cat == "Aluno" else "N/A", 
                    'Turma': turma if cat == "Aluno" else "N/A"
                }
                new_c = pd.concat([df_c, pd.DataFrame([novo_reg])], ignore_index=True)
                new_c.to_csv(DB_CLIENTES, index=False)
                st.success(f"{n} cadastrado com sucesso!")
                st.rerun()

    st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
    if os.path.exists("logo.png"):
        st.image("logo.png", width=120)
    else:
        st.title("🐻 Bear Snack")
    st.markdown("</div>", unsafe_allow_html=True)

    if df_c.empty:
        st.info("Cadastre alguém no menu lateral para começar.")
    else:
        aba_aluno, aba_func = st.tabs(["🎓 ALUNOS", "💼 FUNCIONÁRIOS"])
        
        with aba_aluno:
            # Lista alunos mostrando a turma para facilitar
            df_alunos = df_c[df_c['Categoria'] == 'Aluno']
            if not df_alunos.empty:
                df_alunos['Display'] = df_alunos['Nome'] + " (" + df_alunos['Periodo'] + " - " + df_alunos['Turma'] + ")"
                sel_a = st.selectbox("Selecione o Aluno:", ["-- Selecionar --"] + list(df_alunos['Display'].unique()), key="sel_aluno")
                cliente = sel_a.split(" (")[0] if sel_a != "-- Selecionar --" else "-- Selecionar --"
            else:
                st.write("Nenhum aluno cadastrado.")
                cliente = "-- Selecionar --"
            
        with aba_func:
            lista_funcs = df_c[df_c['Categoria'] == 'Funcionário']['Nome'].unique()
            cliente_f = st.selectbox("Selecione o Funcionário:", ["-- Selecionar --"] + list(lista_funcs), key="sel_func")
            
        cliente_final = cliente if cliente != "-- Selecionar --" else (cliente_f if cliente_f != "-- Selecionar --" else None)

        if cliente_final:
            v_c = df_v[df_v['Cliente'] == cliente_final]
            divida = v_c[v_c['Tipo'] == 'Compra']['Valor'].sum() - v_c[v_c['Tipo'] == 'Pagamento']['Valor'].sum()
            tel = df_c[df_c['Nome'] == cliente_final]['Telefone'].values[0]

            st.markdown(f"""
                <div class="balance-card">
                    <p style="margin:0; opacity:0.8;">Dívida de {cliente_final}</p>
                    <h1 style="color:white; margin:0; font-size:40px;">R$ {divida:,.2f}</h1>
                </div>
            """, unsafe_allow_html=True)

            c1, c2 = st.columns(2)
            with c1:
                if st.button("➕ COMPRA"): st.session_state.op = "Compra"
            with c2:
                if st.button("💵 PAGOU"): st.session_state.op = "Pagamento"

            if 'op' in st.session_state:
                with st.form("lanca"):
                    st.write(f"### Registrar {st.session_state.op}")
                    if 'valor_input' not in st.session_state: st.session_state.valor_input = 0.0
                    
                    val_final = st.number_input("Valor R$", min_value=0.0, step=1.0, value=st.session_state.valor_input)
                    
                    st.write("Valores sugeridos:")
                    col_v1, col_v2, col_v3, col_v4 = st.columns(4)
                    with col_v1:
                        if st.form_submit_button("R$ 4,00"): 
                            st.session_state.valor_input = 6.0
                            st.rerun()
                    with col_v2:
                        if st.form_submit_button("R$ 6,00"): 
                            st.session_state.valor_input = 7.0
                            st.rerun()
                    with col_v3:
                        if st.form_submit_button("R$ 7,00"): 
                            st.session_state.valor_input = 7.0
                            st.rerun()
                   with col_v4:
                        if st.form_submit_button("R$ 8,00"): 
                            st.session_state.valor_input = 8.0
                            st.rerun()        
                    
                    i_f = st.text_input("Descrição")
                    
                    if st.form_submit_button("CONFIRMAR"):
                        nid = datetime.now().strftime("%Y%m%d%H%M%S")
                        agora = datetime.now().strftime("%d/%m - %H:%M")
                        new_v = pd.DataFrame([{'ID': nid, 'Cliente': cliente_final, 'Item': i_f, 'Valor': val_final, 'Data': agora, 'Tipo': st.session_state.op}])
                        pd.concat([df_v, new_v], ignore_index=True).to_csv(DB_VENDAS, index=False)
                        st.session_state.valor_input = 0.0
                        del st.session_state.op
                        st.rerun()

            msg = f"Olá {cliente_final}, seu saldo no Bear Snack é R$ {divida:,.2f}"
            url = f"https://wa.me/{tel}?text={urllib.parse.quote(msg)}"
            st.markdown(f'<a href="{url}" target="_blank" style="text-decoration:none;"><div style="background-color:#25D366; color:white; padding:15px; border-radius:15px; text-align:center; font-weight:bold; margin-bottom:20px;">📲 COBRAR NO WHATSAPP</div></a>', unsafe_allow_html=True)

            st.write("### Histórico Recente")
            for i, row in v_c.iloc[::-1].iterrows():
                cor = "#B03020" if row['Tipo'] == "Compra" else "#2e7d32"
                st.markdown(f"""
                    <div class="item-card">
                        <div><b>{row['Item'] if str(row['Item']) != 'nan' and row['Item'] != '' else row['Tipo']}</b><br><small>{row['Data']}</small></div>
                        <b style="color:{cor}; font-size:18px;">R$ {row['Valor']:.2f}</b>
                    </div>
                """, unsafe_allow_html=True)
                if st.button("🗑️", key=f"del_{row['ID']}"):
                    df_v = df_v[df_v['ID'] != row['ID']]
                    df_v.to_csv(DB_VENDAS, index=False)
                    st.rerun()

