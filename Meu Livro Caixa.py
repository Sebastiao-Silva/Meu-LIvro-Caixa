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
    /* Estilo para a Tabela de Impressão */
    .print-table {
        width: 100%; border-collapse: collapse; background-color: white; color: black;
    }
    .print-table th, .print-table td {
        border: 1px solid #ddd; padding: 8px; text-align: left;
    }
    .print-table th { background-color: #f2f2f2; }
    </style>
    """, unsafe_allow_html=True)

DB_VENDAS = "vendas_bear_final.csv"
DB_CLIENTES = "clientes_bear_final.csv"

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
    # --- 5. SIDEBAR (CADASTRO) ---
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
        if st.button("SALVAR"):
            if n:
                df_temp, _ = load_data()
                if editando: df_temp = df_temp[df_temp['Nome'] != cliente_para_editar]
                new_row = pd.DataFrame([{'Nome': n, 'Telefone': t, 'Categoria': cat, 'Periodo': p, 'Turma': tur, 'Limite': lim}])
                pd.concat([df_temp, new_row], ignore_index=True).to_csv(DB_CLIENTES, index=False)
                st.success("Salvo!")
                st.rerun()

    # --- 6. TELA HOME ---
    if st.session_state.tela_atual == "home":
        st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
        if os.path.exists("logo.png"): st.image("logo.png", width=100)
        else: st.title("🐻 Bear Snack")
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.write("🔍 **Buscar Cliente:**")
        nome_busca = st.text_input("", placeholder="Digite para buscar...", label_visibility="collapsed").strip()
        if nome_busca:
            matches = df_c[df_c['Nome'].str.contains(nome_busca, case=False, na=False)]
            for _, row in matches.head(3).iterrows():
                if st.button(f"✅ Atender: {row['Nome']}", key=f"f_{row['Nome']}"):
                    st.session_state.cliente_selecionado = (row['Nome'], row['Categoria'])
                    st.session_state.tela_atual = "vendas"
                    st.rerun()

        st.divider()
        if st.button("🎓 ALUNOS"): st.session_state.tela_atual = "alunos"; st.rerun()
        if st.button("💼 FUNCIONÁRIOS"): st.session_state.tela_atual = "funcionarios"; st.rerun()
        if st.button("📊 DEVEDORES"): st.session_state.tela_atual = "devedores"; st.rerun()
        if st.button("📄 IMPRIMIR RELATÓRIO"): st.session_state.tela_atual = "imprimir"; st.rerun()

    # --- 7. NOVA TELA DE IMPRESSÃO (RELATÓRIOS) ---
    elif st.session_state.tela_atual == "imprimir":
        st.markdown('<div class="btn-voltar">', unsafe_allow_html=True)
        if st.button("⬅️ VOLTAR AO MENU"): st.session_state.tela_atual = "home"; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.subheader("Configurar Relatório")
        opcao = st.selectbox("Tipo de Relatório:", 
                             ["Relatório Completo (Todos Devedores)", 
                              "Devedor Completo (Individual)", 
                              "Todos por Período", 
                              "Devedor por Período"])
        
        tabela_html = ""
        titulo_rel = ""

        if "Relatório Completo" in opcao:
            titulo_rel = "RELATÓRIO GERAL DE DEVEDORES"
            dados_rel = []
            for _, r in df_c.iterrows():
                v_cli = df_v[(df_v['Cliente'] == r['Nome'])]
                saldo = v_cli[v_cli['Tipo'] == 'Compra']['Valor'].sum() - v_cli[v_cli['Tipo'] == 'Pagamento']['Valor'].sum()
                if saldo > 0:
                    dados_rel.append(f"<tr><td>{r['Nome']}</td><td>{r['Categoria']}</td><td>R$ {saldo:.2f}</td></tr>")
            tabela_html = f"<table class='print-table'><tr><th>Nome</th><th>Categoria</th><th>Débito</th></tr>{''.join(dados_rel)}</table>"

        elif "Devedor Completo" in opcao:
            nome_sel = st.selectbox("Selecione o Cliente:", sorted(df_c['Nome'].unique()))
            titulo_rel = f"EXTRATO COMPLETO: {nome_sel}"
            v_cli = df_v[df_v['Cliente'] == nome_sel]
            dados_rel = [f"<tr><td>{rv['Data']}</td><td>{rv['Tipo']}</td><td>{rv['Item']}</td><td>R$ {rv['Valor']:.2f}</td></tr>" for _, rv in v_cli.iterrows()]
            tabela_html = f"<table class='print-table'><tr><th>Data</th><th>Tipo</th><th>Item</th><th>Valor</th></tr>{''.join(dados_rel)}</table>"

        elif "Todos por Período" in opcao:
            per = st.selectbox("Período:", ["Manhã", "Tarde"])
            tur = st.selectbox("Turma:", ["1ª Turma", "2ª Turma", "3ª Turma"])
            titulo_rel = f"DEVEDORES: {per} - {tur}"
            df_f = df_c[(df_c['Periodo'] == per) & (df_c['Turma'] == tur)]
            dados_rel = []
            for _, r in df_f.iterrows():
                v_cli = df_v[df_v['Cliente'] == r['Nome']]
                saldo = v_cli[v_cli['Tipo'] == 'Compra']['Valor'].sum() - v_cli[v_cli['Tipo'] == 'Pagamento']['Valor'].sum()
                if saldo > 0: dados_rel.append(f"<tr><td>{r['Nome']}</td><td>R$ {saldo:.2f}</td></tr>")
            tabela_html = f"<table class='print-table'><tr><th>Nome</th><th>Débito</th></tr>{''.join(dados_rel)}</table>"

        # Área de Visualização e Botão de Comando
        st.divider()
        st.markdown(f"### {titulo_rel}")
        st.markdown(tabela_html, unsafe_allow_html=True)
        st.info("💡 DICA: Para salvar como PDF, clique com o botão direito na página e escolha 'Imprimir' (ou Ctrl+P) e mude o destino para 'Salvar como PDF'.")

    # --- 8. RESTANTE DAS TELAS (ALUNOS/DEVEDORES/VENDAS) ---
    else:
        st.markdown('<div class="btn-voltar">', unsafe_allow_html=True)
        if st.button("⬅️ VOLTAR AO MENU"):
            st.session_state.tela_atual = "home"
            st.session_state.cliente_selecionado = None
            if 'op' in st.session_state: del st.session_state.op
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        if st.session_state.tela_atual == "alunos":
            st.subheader("🎓 Área dos Alunos")
            c1, c2 = st.columns(2)
            with c1: pf = st.selectbox("Período:", ["Manhã", "Tarde"])
            with c2: tf = st.selectbox("Turma:", ["1ª Turma", "2ª Turma", "3ª Turma"])
            df_fa = df_c[(df_c['Categoria'] == 'Aluno') & (df_c['Periodo'] == pf) & (df_c['Turma'] == tf)]
            sel_a = st.selectbox("Selecione o Aluno:", ["-- Selecionar --"] + sorted(df_fa['Nome'].unique().tolist()))
            if sel_a != "-- Selecionar --": st.session_state.cliente_selecionado = (sel_a, "Aluno"); st.session_state.tela_atual = "vendas"; st.rerun()

        elif st.session_state.tela_atual == "funcionarios":
            st.subheader("💼 Área dos Funcionários")
            sel_f = st.selectbox("Selecione o Funcionário:", ["-- Selecionar --"] + sorted(df_c[df_c['Categoria'] == 'Funcionário']['Nome'].unique().tolist()))
            if sel_f != "-- Selecionar --": st.session_state.cliente_selecionado = (sel_f, "Funcionário"); st.session_state.tela_atual = "vendas"; st.rerun()

        elif st.session_state.tela_atual == "devedores":
            st.subheader("📊 Relatório de Devedores")
            total_a_receber = 0
            for _, r in df_c.iterrows():
                v_cli = df_v[(df_v['Cliente'] == r['Nome'])]
                saldo = v_cli[v_cli['Tipo'] == 'Compra']['Valor'].sum() - v_cli[v_cli['Tipo'] == 'Pagamento']['Valor'].sum()
                if saldo > 0:
                    if st.button(f"{r['Nome']} ➔ R$ {saldo:.2f}", key=f"d_{r['Nome']}"):
                        st.session_state.cliente_selecionado = (r['Nome'], r['Categoria'])
                        st.session_state.tela_atual = "vendas"; st.rerun()
                    total_a_receber += saldo
            st.write(f"**Total Geral:** R$ {total_a_receber:.2f}")

        # ÁREA DE VENDAS (A MESMA DO SEU CÓDIGO)
        if st.session_state.cliente_selecionado:
            cliente_final, cat_final = st.session_state.cliente_selecionado
            v_c = df_v[(df_v['Cliente'] == cliente_final)]
            divida = v_c[v_c['Tipo'] == 'Compra']['Valor'].sum() - v_c[v_c['Tipo'] == 'Pagamento']['Valor'].sum()
            row_cli = df_c[(df_c['Nome'] == cliente_final)].iloc[0]
            st.markdown(f'<div class="balance-card"><h2>{cliente_final}</h2><h1>R$ {divida:,.2f}</h1></div>', unsafe_allow_html=True)
            
            # (Aqui continuaria o resto do seu código de botões de produtos e formulário de venda...)
            col_c, col_p = st.columns(2)
            with col_c: 
                if st.button("➕ COMPRA"): st.session_state.op = "Compra"
            with col_p: 
                if st.button("💵 PAGOU"): st.session_state.op = "Pagamento"

            if 'op' in st.session_state:
                if 'val_temp' not in st.session_state: st.session_state.val_temp = 0.0
                produtos = {"Água": 4.0, "Salgado": 8.0, "Suco": 6.0, "Pipoca": 7.0}
                cols = st.columns(2)
                for i, (prod, preco) in enumerate(produtos.items()):
                    if cols[i%2].button(f"{prod} R${preco}"): st.session_state.val_temp += preco; st.rerun()
                with st.form("lanca"):
                    vf = st.number_input("Valor", value=st.session_state.val_temp)
                    if st.form_submit_button("✅ CONFIRMAR"):
                        new_row = pd.DataFrame([{'ID': datetime.now().strftime("%Y%m%d%H%M%S"), 'Cliente': cliente_final, 'Cat_Venda': cat_final, 'Item': '', 'Valor': vf, 'Data': datetime.now().strftime("%d/%m - %H:%M"), 'Tipo': st.session_state.op}])
                        pd.concat([df_v, new_row], ignore_index=True).to_csv(DB_VENDAS, index=False)
                        st.session_state.val_temp = 0.0; del st.session_state.op; st.rerun()
