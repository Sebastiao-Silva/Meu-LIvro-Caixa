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
    .btn-voltar > button {
        height: 35px !important; background-color: #D2B48C !important;
        color: #4E3620 !important; margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

DB_VENDAS = "vendas_bear_final.csv"
DB_CLIENTES = "clientes_bear_final.csv"
DB_ANTIGO = "Livro Caixa.db"

# --- 2. FUNÇÕES DE DADOS ---
def load_data():
    if os.path.exists(DB_CLIENTES): c = pd.read_csv(DB_CLIENTES)
    else: c = pd.DataFrame(columns=['Nome', 'Telefone', 'Categoria', 'Periodo', 'Turma', 'Limite'])
    
    if os.path.exists(DB_VENDAS): v = pd.read_csv(DB_VENDAS)
    else: v = pd.DataFrame(columns=['ID', 'Cliente', 'Cat_Venda', 'Item', 'Valor', 'Data', 'Tipo'])
    
    for col in ['Categoria', 'Periodo', 'Turma', 'Limite']:
        if col not in c.columns: c[col] = 50.0 if col == 'Limite' else "N/A"
    return c, v

df_c, df_v = load_data()

# --- 3. ESTADO DE NAVEGAÇÃO ---
if 'logado' not in st.session_state: st.session_state.logado = False
if 'tela_atual' not in st.session_state: st.session_state.tela_atual = "home"
if 'cliente_selecionado' not in st.session_state: st.session_state.cliente_selecionado = None

# --- 4. LOGIN ---
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
    # --- SIDEBAR (GESTÃO) ---
    with st.sidebar:
        if st.button("🚪 SAIR"):
            st.session_state.logado = False
            st.rerun()
        st.divider()
        st.subheader("👤 Gerenciar Cliente")
        lista_clientes_gestao = ["-- Novo Cadastro --"] + sorted(df_c['Nome'].unique().tolist())
        cliente_para_editar = st.selectbox("🔍 Buscar/Editar:", options=lista_clientes_gestao)
        
        # (Lógica de cadastro resumida para a sidebar)
        if st.button("IR PARA CADASTRO COMPLETO"):
            st.info("Função de cadastro ativo na sidebar.")

    # --- LOGO TOPO ---
    st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
    if os.path.exists("logo.png"): st.image("logo.png", width=100)
    else: st.title("🐻 Bear Snack")
    st.markdown("</div>", unsafe_allow_html=True)

    # --- TELA HOME (MENU PRINCIPAL) ---
    if st.session_state.tela_atual == "home":
        st.markdown("<br>", unsafe_allow_html=True)
        
        # BUSCA RÁPIDA POR DIGITAÇÃO
        st.write("🔍 **Buscar Cliente (digite o nome):**")
        nome_busca = st.text_input("", placeholder="Digite para buscar...", label_visibility="collapsed").strip()

        if nome_busca:
            matches = df_c[df_c['Nome'].str.contains(nome_busca, case=False, na=False)]
            if not matches.empty:
                for _, row in matches.head(3).iterrows():
                    if st.button(f"✅ Atender: {row['Nome']} ({row['Categoria']})", key=f"fast_{row['Nome']}"):
                        st.session_state.cliente_selecionado = (row['Nome'], row['Categoria'])
                        st.session_state.tela_atual = "vendas"
                        st.rerun()
            else:
                st.warning("Nenhum cliente encontrado.")

        st.divider()
        if st.button("🎓 ALUNOS"):
            st.session_state.tela_atual = "alunos"
            st.rerun()
        if st.button("💼 FUNCIONÁRIOS"):
            st.session_state.tela_atual = "funcionarios"
            st.rerun()
        if st.button("📊 DEVEDORES"):
            st.session_state.tela_atual = "devedores"
            st.rerun()

    # --- TELAS INTERNAS ---
    else:
        st.markdown('<div class="btn-voltar">', unsafe_allow_html=True)
        if st.button("⬅️ VOLTAR AO MENU"):
            st.session_state.tela_atual = "home"
            st.session_state.cliente_selecionado = None
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        if st.session_state.tela_atual == "alunos":
            st.subheader("🎓 Área dos Alunos")
            c1, c2 = st.columns(2)
            with c1: pf = st.selectbox("Período:", ["Manhã", "Tarde"])
            with c2: tf = st.selectbox("Turma:", ["1ª Turma", "2ª Turma", "3ª Turma"])
            df_fa = df_c[(df_c['Categoria'] == 'Aluno') & (df_c['Periodo'] == pf) & (df_c['Turma'] == tf)]
            sel_a = st.selectbox("Selecione o Aluno:", ["-- Selecionar --"] + sorted(df_fa['Nome'].unique().tolist()))
            if sel_a != "-- Selecionar --":
                st.session_state.cliente_selecionado = (sel_a, "Aluno")

        elif st.session_state.tela_atual == "funcionarios":
            st.subheader("💼 Área dos Funcionários")
            sel_f = st.selectbox("Selecione o Funcionário:", ["-- Selecionar --"] + sorted(df_c[df_c['Categoria'] == 'Funcionário']['Nome'].unique().tolist()))
            if sel_f != "-- Selecionar --":
                st.session_state.cliente_selecionado = (sel_f, "Funcionário")

        elif st.session_state.tela_atual == "devedores":
            st.subheader("📊 Relatório de Devedores")
            total_a_receber = 0
            devedores = []
            for _, r in df_c.iterrows():
                v_cli = df_v[(df_v['Cliente'] == r['Nome']) & (df_v['Cat_Venda'] == r['Categoria'])]
                saldo = v_cli[v_cli['Tipo'] == 'Compra']['Valor'].sum() - v_cli[v_cli['Tipo'] == 'Pagamento']['Valor'].sum()
                if saldo > 0:
                    devedores.append({'Nome': r['Nome'], 'Divida': saldo, 'Cat': r['Categoria']})
                    total_a_receber += saldo
            st.markdown(f'<div class="balance-card"><small>TOTAL A RECEBER</small><br><b style="font-size:24px;">R$ {total_a_receber:,.2f}</b></div>', unsafe_allow_html=True)
            for d in sorted(devedores, key=lambda x: x['Nome']):
                if st.button(f"{d['Nome']} ({d['Cat']}) ➔ R$ {d['Divida']:,.2f}", key=f"dev_{d['Nome']}"):
                    st.session_state.cliente_selecionado = (d['Nome'], d['Cat'])
                    st.rerun()

        # --- ÁREA DE LANÇAMENTOS (VISÍVEL SE CLIENTE SELECIONADO) ---
        if st.session_state.cliente_selecionado:
            cliente_final, cat_final = st.session_state.cliente_selecionado
            v_c = df_v[(df_v['Cliente'] == cliente_final) & (df_v['Cat_Venda'] == cat_final)]
            divida = v_c[v_c['Tipo'] == 'Compra']['Valor'].sum() - v_c[v_c['Tipo'] == 'Pagamento']['Valor'].sum()
            row_cli = df_c[(df_c['Nome'] == cliente_final) & (df_c['Categoria'] == cat_final)].iloc[0]
            limite_cli, tel = row_cli['Limite'], str(row_cli['Telefone'])

            st.markdown(f"""<div class="balance-card"><p style="margin:0;">Saldo de {cliente_final}</p><h1 style="color:white; margin:0; font-size:40px;">R$ {divida:,.2f}</h1><p style="margin:0; font-size:12px;">Limite: R$ {limite_cli:.2f}</p></div>""", unsafe_allow_html=True)

            col_c, col_p = st.columns(2)
            with col_c: 
                if st.button("➕ COMPRA"): st.session_state.op = "Compra"
            with col_p: 
                if st.button("💵 PAGOU"): st.session_state.op = "Pagamento"

            if 'op' in st.session_state:
                if 'val_temp' not in st.session_state: st.session_state.val_temp = 0.0
                st.subheader(f"Lançar {st.session_state.op}")
                produtos = {"Água": 4.0, "Biscoito": 4.0, "Fruta": 4.0, "Pipoca": 7.0, "Refrigerante": 6.0, "Salgado": 8.0, "Suco": 6.0, "Suco Natural": 7.0}
                cols = st.columns(2)
                for i, (prod, preco) in enumerate(produtos.items()):
                    if cols[i%2].button(f"{prod} (R$ {preco:.2f})", key=f"btn_{prod}"):
                        st.session_state.val_temp += preco
                        st.rerun()

                with st.form("lanca_venda"):
                    vf = st.number_input("Valor Final R$", min_value=0.0, value=st.session_state.val_temp)
                    desc = st.text_input("Observação")
                    if st.form_submit_button("✅ CONFIRMAR"):
                        if vf > 0:
                            _, df_v_up = load_data()
                            nid = datetime.now().strftime("%Y%m%d%H%M%S")
                            agora = datetime.now().strftime("%d/%m - %H:%M")
                            new_row = pd.DataFrame([{'ID': nid, 'Cliente': cliente_final, 'Cat_Venda': cat_final, 'Item': desc, 'Valor': vf, 'Data': agora, 'Tipo': st.session_state.op}])
                            pd.concat([df_v_up, new_row], ignore_index=True).to_csv(DB_VENDAS, index=False)
                            st.session_state.val_temp = 0.0
                            del st.session_state.op
                            st.rerun()

            st.divider()
            if os.path.exists("QRcode.jpeg"):
                st.image("QRcode.jpeg", caption="PIX: (13) 97827-5300", width=200)

            url = f"https://wa.me/{tel}?text=Olá {cliente_final}, seu saldo no Bear Snack é R$ {divida:,.2f}"
            st.markdown(f'<a href="{url}" target="_blank" style="text-decoration:none;"><div style="background-color:#25D366; color:white; padding:15px; border-radius:15px; text-align:center; font-weight:bold;">📲 WHATSAPP</div></a>', unsafe_allow_html=True)

            st.write("### Histórico")
            for i, row in v_c.iloc[::-1].iterrows():
                cor_hist = "#B03020" if row['Tipo'] == "Compra" else "#2e7d32"
                st.markdown(f'<div class="item-card"><div><b>{row["Item"] if str(row["Item"]) != "nan" and row["Item"] != "" else row["Tipo"]}</b><br><small>{row["Data"]}</small></div><b style="color:{cor_hist};">R$ {row["Valor"]:.2f}</b></div>', unsafe_allow_html=True)
                if st.button("🗑️", key=f"del_{row['ID']}"):
                    _, df_v_del = load_data()
                    df_v_del = df_v_del[df_v_del['ID'] != row['ID']]
                    df_v_del.to_csv(DB_VENDAS, index=False)
                    st.rerun()
