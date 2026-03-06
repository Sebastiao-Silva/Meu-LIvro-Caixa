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

    # --- 4. SIDEBAR (CADASTRO E EDIÇÃO) ---
    with st.sidebar:
        if st.button("🚪 SAIR"):
            st.session_state.logado = False
            st.rerun()
        st.divider()
        st.subheader("👤 Gerenciar Cliente")
        
        lista_clientes = ["-- Novo Cadastro --"] + sorted(df_c['Nome'].unique().tolist())
        cliente_para_editar = st.selectbox("🔍 Buscar/Editar Cliente:", options=lista_clientes)

        val_n, val_t, val_cat, val_lim = "", "", "Aluno", 50.0
        val_p, val_tur = "Manhã", "1ª Turma"
        editando = False

        if cliente_para_editar != "-- Novo Cadastro --":
            editando = True
            dados = df_c[df_c['Nome'] == cliente_para_editar].iloc[0]
            val_n, val_t, val_cat, val_lim = dados['Nome'], str(dados['Telefone']), dados['Categoria'], float(dados['Limite'])
            val_p, val_tur = dados['Periodo'], dados['Turma']
            st.warning(f"Editando: {cliente_para_editar}")

        n = st.text_input("Nome", value=val_n)
        t = st.text_input("WhatsApp", value=val_t)
        cat = st.selectbox("Tipo:", ["Aluno", "Funcionário"], index=0 if val_cat == "Aluno" else 1)
        lim = st.number_input("Limite R$", value=val_lim)
        
        p, tur = "N/A", "N/A"
        if cat == "Aluno":
            idx_p = ["Manhã", "Tarde"].index(val_p) if val_p in ["Manhã", "Tarde"] else 0
            idx_t = ["1ª Turma", "2ª Turma", "3ª Turma"].index(val_tur) if val_tur in ["1ª Turma", "2ª Turma", "3ª Turma"] else 0
            p = st.selectbox("Período:", ["Manhã", "Tarde"], index=idx_p)
            tur = st.selectbox("Turma:", ["1ª Turma", "2ª Turma", "3ª Turma"], index=idx_t)

        if st.button("SALVAR ALTERAÇÕES" if editando else "CADASTRAR"):
            if n:
                if editando: df_c = df_c[df_c['Nome'] != cliente_para_editar]
                new_row = pd.DataFrame([{'Nome': n, 'Telefone': t, 'Categoria': cat, 'Periodo': p, 'Turma': tur, 'Limite': lim}])
                df_c = pd.concat([df_c, new_row], ignore_index=True)
                df_c.to_csv(DB_CLIENTES, index=False)
                st.success("Sucesso!")
                st.rerun()

    # --- 5. TELA PRINCIPAL ---
    st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
    if os.path.exists("logo.png"): st.image("logo.png", width=100)
    else: st.title("🐻 Bear Snack")
    st.markdown("</div>", unsafe_allow_html=True)

    aba_selecionada = st.tabs(["🎓 ALUNOS", "💼 FUNCIONÁRIOS", "📊 DEVEDORES"])
    cliente_final, cat_final = None, None

    with aba_selecionada[0]:
        c1, c2 = st.columns(2)
        with c1: pf = st.selectbox("Período:", ["Manhã", "Tarde"], key="fa_p")
        with c2: tf = st.selectbox("Turma:", ["1ª Turma", "2ª Turma", "3ª Turma"], key="fa_t")
        df_fa = df_c[(df_c['Categoria'] == 'Aluno') & (df_c['Periodo'] == pf) & (df_c['Turma'] == tf)]
        sel_a = st.selectbox("Selecione o Aluno:", ["-- Selecionar --"] + list(df_fa['Nome'].unique()), key="sa_a")
        if sel_a != "-- Selecionar --": cliente_final, cat_final = sel_a, "Aluno"
        
    with aba_selecionada[1]:
        sel_f = st.selectbox("Selecione o Funcionário:", ["-- Selecionar --"] + list(df_c[df_c['Categoria'] == 'Funcionário']['Nome'].unique()), key="sf_f")
        if sel_f != "-- Selecionar --": cliente_final, cat_final = sel_f, "Funcionário"

    with aba_selecionada[2]:
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

    # --- 6. ÁREA DE LANÇAMENTO ---
    if cliente_final:
        v_c = df_v[(df_v['Cliente'] == cliente_final) & (df_v['Cat_Venda'] == cat_final)]
        divida = v_c[v_c['Tipo'] == 'Compra']['Valor'].sum() - v_c[v_c['Tipo'] == 'Pagamento']['Valor'].sum()
        row_cli = df_c[(df_c['Nome'] == cliente_final) & (df_c['Categoria'] == cat_final)].iloc[0]
        limite_cli, tel = row_cli['Limite'], row_cli['Telefone']

        st.markdown(f"""<div class="balance-card"><p style="margin:0; opacity:0.8;">Saldo de {cliente_final}</p><h1 style="color:white; margin:0; font-size:40px;">R$ {divida:,.2f}</h1><p style="margin:0; font-size:12px;">Limite: R$ {limite_cli:.2f}</p></div>""", unsafe_allow_html=True)

        col_c, col_p = st.columns(2)
        with col_c:
            if st.button("➕ COMPRA"): st.session_state.op = "Compra"
        with col_p:
            if st.button("💵 PAGOU"): st.session_state.op = "Pagamento"

        if 'op' in st.session_state:
            st.markdown(f"### Lançar {st.session_state.op}")
            if 'val_temp' not in st.session_state: st.session_state.val_temp = 0.0
            
            produtos = {
                "Água": 4.0, "Biscoito": 4.0, "Fruta": 4.0, "Pipoca": 7.0,
                "Refrigerante": 6.0, "Salgado": 8.0, "Suco": 6.0, "Suco Natural": 7.0
            }

            st.write("Selecione os itens para somar:")
            cols_prod = st.columns(2)
            for i, (p_nome, p_valor) in enumerate(produtos.items()):
                if cols_prod[i % 2].button(f"{p_nome} (R$ {p_valor:.2f})", key=f"p_{p_nome}"):
                    st.session_state.val_temp += p_valor
                    st.rerun()

            with st.form("form_final"):
                vf = st.number_input("Valor Total R$", min_value=0.0, value=st.session_state.val_temp)
                desc = st.text_input("Descrição (Ex: Itens consumidos)")
                
                c_limp, c_conf = st.columns(2)
                if c_limp.form_submit_button("🧹 ZERAR VALOR"):
                    st.session_state.val_temp = 0.0
                    st.rerun()
                if c_conf.form_submit_button("✅ CONFIRMAR REGISTRO"):
                    if vf > 0:
                        nid = datetime.now().strftime("%Y%m%d%H%M%S")
                        agora = datetime.now().strftime("%d/%m - %H:%M")
                        new_v = pd.DataFrame([{'ID': nid, 'Cliente': cliente_final, 'Cat_Venda': cat_final, 'Item': desc, 'Valor': vf, 'Data': agora, 'Tipo': st.session_state.op}])
                        pd.concat([df_v, new_v], ignore_index=True).to_csv(DB_VENDAS, index=False)
                        st.session_state.val_temp = 0.0
                        del st.session_state.op
                        st.rerun()

        # --- 7. WHATSAPP COM QR CODE E CHAVE PIX ---
        st.divider()
        if os.path.exists("QRcode.jpeg"):
            st.image("QRcode.jpeg", caption="Aponte a câmera para pagar via PIX", width=250)
            st.code("Chave PIX: (13) 97827-5300", language="text") #

        if divida > 0:
            # Texto personalizado para débito
            status_txt = f"possui um débito de R$ {divida:,.2f}"
            cor_zap = "#25D366"
            instrucao_pix = "\n\nVocê pode pagar via PIX usando a nossa chave: (13) 97827-5300 ou solicitando o QR Code." #
        elif divida < 0:
            # Texto personalizado para crédito
            status_txt = f"possui um crédito de R$ {abs(divida):,.2f}"
            cor_zap = "#075E54"
            instrucao_pix = ""
        else:
            status_txt = "está com o saldo zerado"
            cor_zap = "#25D366"
            instrucao_pix = ""

        msg = f"Olá {cliente_final}, informamos que você {status_txt} no Bear Snack.{instrucao_pix}"
        url = f"https://wa.me/{tel}?text={urllib.parse.quote(msg)}"
        
        st.markdown(f'''
            <a href="{url}" target="_blank" style="text-decoration:none;">
                <div style="background-color:{cor_zap}; color:white; padding:15px; border-radius:15px; text-align:center; font-weight:bold; margin-bottom:20px;">
                    📲 ENVIAR SALDO E CHAVE PIX
                </div>
            </a>
        ''', unsafe_allow_html=True)

        st.write("### Histórico Recente")
        for i, row in v_c.iloc[::-1].iterrows():
            cor = "#B03020" if row['Tipo'] == "Compra" else "#2e7d32"
            st.markdown(f"""<div class="item-card"><div><b>{row['Item'] if str(row['Item']) != 'nan' and row['Item'] != '' else row['Tipo']}</b><br><small>{row['Data']}</small></div><b style="color:{cor};">R$ {row['Valor']:.2f}</b></div>""", unsafe_allow_html=True)
            if st.button("🗑️", key=f"del_{row['ID']}"):
                df_v = df_v[df_v['ID'] != row['ID']]
                df_v.to_csv(DB_VENDAS, index=False)
                st.rerun()
