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
    .block-container { padding-top: 1.5rem !important; }
    
    .stTabs [data-baseweb="tab-list"] { gap: 8px; background-color: #FDF5E6; }
    .stTabs [data-baseweb="tab"] {
        height: 45px; background-color: #D2B48C; border-radius: 10px 10px 0px 0px;
        color: #4E3620; font-weight: bold; padding: 0px 15px; font-size: 12px;
    }
    .stTabs [aria-selected="true"] { background-color: #4E3620 !important; color: #D2B48C !important; }

    .balance-card {
        background: linear-gradient(135deg, #B03020 0%, #4E3620 100%);
        color: white; padding: 20px; border-radius: 20px;
        text-align: center; margin-bottom: 15px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.2); border: 2px solid #D2B48C;
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
    with st.container():
        user = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        if st.button("ACESSAR SISTEMA"):
            if user == "admin" and password == "bear123":
                st.session_state.logado = True
                st.rerun()
            else: st.error("Dados incorretos")

else:
    DB_VENDAS = "vendas_bear_final.csv"
    DB_CLIENTES = "clientes_bear_final.csv"

    def load():
        if os.path.exists(DB_CLIENTES):
            c = pd.read_csv(DB_CLIENTES)
            for col in ['Categoria', 'Periodo', 'Turma', 'Limite']:
                if col not in c.columns: c[col] = 50.0 if col == 'Limite' else "N/A"
        else: c = pd.DataFrame(columns=['Nome', 'Telefone', 'Categoria', 'Periodo', 'Turma', 'Limite'])
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

    tab_a, tab_f, tab_r = st.tabs(["🎓 ALUNOS", "💼 FUNCIONÁRIOS", "📊 DEVEDORES"])
    
    cliente_selecionado = None

    # ABA ALUNOS
    with tab_a:
        col_p, col_t = st.columns(2)
        with col_p: p_f = st.selectbox("Período:", ["Manhã", "Tarde"], key="f_p")
        with col_t: t_f = st.selectbox("Turma:", ["1ª Turma", "2ª Turma", "3ª Turma"], key="f_t")
        df_filtro = df_c[(df_c['Categoria'] == 'Aluno') & (df_c['Periodo'] == p_f) & (df_c['Turma'] == t_f)]
        sel_a = st.selectbox("Selecione o Aluno:", ["-- Selecionar --"] + list(df_filtro['Nome'].unique()), key="s_a")
        if sel_a != "-- Selecionar --": cliente_selecionado = sel_a
        
    # ABA FUNCIONÁRIOS
    with tab_f:
        sel_f = st.selectbox("Selecione o Funcionário:", ["-- Selecionar --"] + list(df_c[df_c['Categoria'] == 'Funcionário']['Nome'].unique()), key="s_f")
        if sel_f != "-- Selecionar --": cliente_selecionado = sel_f

    # ABA RELATÓRIO DE DEVEDORES
    with tab_r:
        devedores_lista = []
        total_geral = 0
        for _, row in df_c.iterrows():
            v_cli = df_v[df_v['Cliente'] == row['Nome']]
            saldo = v_cli[v_cli['Tipo'] == 'Compra']['Valor'].sum() - v_cli[v_cli['Tipo'] == 'Pagamento']['Valor'].sum()
            if saldo > 0:
                devedores_lista.append({'Nome': row['Nome'], 'Divida': saldo})
                total_geral += saldo
        
        st.markdown(f"""<div style="background-color:#4E3620; color:#D2B48C; padding:15px; border-radius:15px; text-align:center; margin-bottom:20px;"><small>TOTAL A RECEBER</small><br><b style="font-size:24px;">R$ {total_geral:,.2f}</b></div>""", unsafe_allow_html=True)
        
        devedores_ordenados = sorted(devedores_lista, key=lambda x: x['Nome'])
        for d in devedores_ordenados:
            if st.button(f"{d['Nome']} ➔ R$ {d['Divida']:,.2f}", key=f"btn_dev_{d['Nome']}"):
                st.session_state.devedor_selecionado = d['Nome']
        
        if 'devedor_selecionado' in st.session_state:
            d_nome = st.session_state.devedor_selecionado
            v_d = df_v[df_v['Cliente'] == d_nome]
            s_d = v_d[v_d['Tipo'] == 'Compra']['Valor'].sum() - v_d[v_d['Tipo'] == 'Pagamento']['Valor'].sum()
            st.markdown(f"""<div class="balance-card"><p style="margin:0;">{d_nome}</p><h1 style="color:white; margin:0;">R$ {s_d:,.2f}</h1></div>""", unsafe_allow_html=True)
            if st.button("FECHAR DETALHES"):
                del st.session_state.devedor_selecionado
                st.rerun()

    # --- ÁREA DE LANÇAMENTO (RESTAURADA PARA AS ABAS DE CLIENTES) ---
    if cliente_selecionado:
        v_c = df_v[df_v['Cliente'] == cliente_selecionado]
        divida = v_c[v_c['Tipo'] == 'Compra']['Valor'].sum() - v_c[v_c['Tipo'] == 'Pagamento']['Valor'].sum()
        row_cli = df_c[df_c['Nome'] == cliente_selecionado].iloc[0]
        limite_cli = row_cli['Limite']
        tel = row_cli['Telefone']

        st.markdown(f"""<div class="balance-card"><p style="margin:0; opacity:0.8;">Dívida de {cliente_selecionado}</p><h1 style="color:white; margin:0; font-size:40px;">R$ {divida:,.2f}</h1><p style="margin:0; font-size:12px;">Limite: R$ {limite_cli:.2f}</p></div>""", unsafe_allow_html=True)

        col_c, col_p = st.columns(2)
        with col_c:
            if st.button("➕ COMPRA"): st.session_state.op = "Compra"
        with col_p:
            if st.button("💵 PAGOU"): st.session_state.op = "Pagamento"

        if 'op' in st.session_state:
            with st.form("lanca_form"):
                st.write(f"### Registrar {st.session_state.op}")
                if 'valor_input' not in st.session_state: st.session_state.valor_input = 0.0
                val_final = st.number_input("Valor R$", min_value=0.0, value=st.session_state.valor_input)
                
                c_v1, c_v2, c_v3 = st.columns(3)
                with c_v1: 
                    if st.form_submit_button("R$ 6,00"): 
                        st.session_state.valor_input = 6.0
                        st.rerun()
                with c_v2:
                    if st.form_submit_button("R$ 7,00"):
                        st.session_state.valor_input = 7.0
                        st.rerun()
                with c_v3:
                    if st.form_submit_button("R$ 8,00"):
                        st.session_state.valor_input = 8.0
                        st.rerun()
                
                i_f = st.text_input("Descrição")
                if st.form_submit_button("SALVAR"):
                    nid = datetime.now().strftime("%Y%m%d%H%M%S")
                    agora = datetime.now().strftime("%d/%m - %H:%M")
                    new_v = pd.DataFrame([{'ID': nid, 'Cliente': cliente_selecionado, 'Item': i_f, 'Valor': val_final, 'Data': agora, 'Tipo': st.session_state.op}])
                    pd.concat([df_v, new_v], ignore_index=True).to_csv(DB_VENDAS, index=False)
                    st.session_state.valor_input = 0.0
                    del st.session_state.op
                    st.rerun()

        # WhatsApp e Histórico (Só nas abas Alunos/Funcionários)
        msg = f"Olá {cliente_selecionado}, seu saldo no Bear Snack é R$ {divida:,.2f}"
        url = f"https://wa.me/{tel}?text={urllib.parse.quote(msg)}"
        st.markdown(f'<a href="{url}" target="_blank" style="text-decoration:none;"><div style="background-color:#25D366; color:white; padding:15px; border-radius:15px; text-align:center; font-weight:bold; margin-bottom:20px;">📲 COBRAR NO WHATSAPP</div></a>', unsafe_allow_html=True)

        st.write("### Histórico Recente")
        for i, row in v_c.iloc[::-1].iterrows():
            cor = "#B03020" if row['Tipo'] == "Compra" else "#2e7d32"
            st.markdown(f"""<div class="item-card"><div><b>{row['Item'] if str(row['Item']) != 'nan' and row['Item'] != '' else row['Tipo']}</b><br><small>{row['Data']}</small></div><b style="color:{cor};">R$ {row['Valor']:.2f}</b></div>""", unsafe_allow_html=True)
            if st.button("🗑️", key=f"del_{row['ID']}"):
                df_v = df_v[df_v['ID'] != row['ID']]
                df_v.to_csv(DB_VENDAS, index=False)
                st.rerun()
