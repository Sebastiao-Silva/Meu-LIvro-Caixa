import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

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
    .btn-voltar > button {
        height: 35px !important; background-color: #D2B48C !important;
        color: #4E3620 !important; margin-bottom: 20px;
    }
    .print-table {
        width: 100%; border-collapse: collapse; background-color: white; color: black; margin-top: 10px;
    }
    .print-table th, .print-table td {
        border: 1px solid #ddd; padding: 10px; text-align: left; font-size: 14px;
    }
    .print-table th { background-color: #f2f2f2; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

DB_VENDAS = "vendas_bear_final.csv"
DB_CLIENTES = "clientes_bear_final.csv"

# --- FUNÇÃO PARA HORÁRIO DE SÃO PAULO (UTC-3) ---
def get_sp_time():
    return datetime.utcnow() - timedelta(hours=3)

# --- 2. FUNÇÕES DE DADOS ---
def load_data():
    c = pd.read_csv(DB_CLIENTES) if os.path.exists(DB_CLIENTES) else pd.DataFrame(columns=['Nome', 'Telefone', 'Categoria', 'Periodo', 'Turma', 'Limite'])
    v = pd.read_csv(DB_VENDAS) if os.path.exists(DB_VENDAS) else pd.DataFrame(columns=['ID', 'Cliente', 'Cat_Venda', 'Item', 'Valor', 'Data', 'Tipo'])
    
    for col in ['Categoria', 'Periodo', 'Turma', 'Limite']:
        if col not in c.columns: c[col] = 50.0 if col == 'Limite' else "N/A"
    
    if not v.empty:
        def parse_dt(x):
            try:
                # Tenta ler o formato dia/mes/ano salvo no CSV
                return datetime.strptime(str(x).split(' - ')[0], "%d/%m/%Y").date()
            except:
                return get_sp_time().date()
        v['dt_obj'] = v['Data'].apply(parse_dt)
    else:
        v['dt_obj'] = None
        
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
    # --- 5. SIDEBAR ---
    with st.sidebar:
        if st.button("🚪 SAIR"):
            st.session_state.logado = False
            st.rerun()
        st.divider()
        st.subheader("👤 Gerenciar Cliente")
        lista_clientes = ["-- Novo Cadastro --"] + sorted(df_c['Nome'].unique().tolist())
        cliente_para_editar = st.selectbox("🔍 Buscar/Editar:", options=lista_clientes)
        
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
                st.success("Salvo!"); st.rerun()

    # --- 6. TELA HOME ---
    if st.session_state.tela_atual == "home":
        st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
        if os.path.exists("logo.png"): st.image("logo.png", width=100)
        else: st.title("🐻 Bear Snack")
        st.markdown("</div>", unsafe_allow_html=True)

        nome_busca = st.text_input("🔍 Buscar Cliente:", placeholder="Digite o nome...").strip()
        if nome_busca:
            matches = df_c[df_c['Nome'].str.contains(nome_busca, case=False, na=False)]
            for _, row in matches.head(3).iterrows():
                if st.button(f"✅ Atender: {row['Nome']}", key=f"f_{row['Nome']}"):
                    st.session_state.cliente_selecionado = (row['Nome'], row['Categoria'])
                    st.session_state.tela_atual = "vendas"; st.rerun()

        st.divider()
        if st.button("🎓 ALUNOS"): st.session_state.tela_atual = "alunos"; st.rerun()
        if st.button("💼 FUNCIONÁRIOS"): st.session_state.tela_atual = "funcionarios"; st.rerun()
        if st.button("📊 DEVEDORES"): st.session_state.tela_atual = "devedores"; st.rerun()
        if st.button("📄 IMPRIMIR RELATÓRIO"): st.session_state.tela_atual = "relatorios"; st.rerun()

    # --- 7. TELA DE RELATÓRIOS ---
    elif st.session_state.tela_atual == "relatorios":
        st.markdown('<div class="btn-voltar">', unsafe_allow_html=True)
        if st.button("⬅️ VOLTAR AO MENU"): st.session_state.tela_atual = "home"; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.subheader("Configurar Impressão")
        tipo = st.selectbox("Tipo de Relatório:", 
                            ["Relatório Completo (Todos Devedores)", 
                             "Devedor Completo (Individual)", 
                             "Todos por Período (Calendário)", 
                             "Devedor por Período (Calendário)"])
        
        tabela_html, titulo_rel = "", ""
        agora_sp = get_sp_time().date()

        if "Relatório Completo" in tipo:
            titulo_rel = "RELATÓRIO GERAL DE DEVEDORES"
            dados = []
            for _, r in df_c.iterrows():
                v_cli = df_v[df_v['Cliente'] == r['Nome']]
                saldo = v_cli[v_cli['Tipo'] == 'Compra']['Valor'].sum() - v_cli[v_cli['Tipo'] == 'Pagamento']['Valor'].sum()
                if saldo > 0: dados.append(f"<tr><td>{r['Nome']}</td><td>R$ {saldo:.2f}</td></tr>")
            tabela_html = f"<table class='print-table'><tr><th>Nome</th><th>Saldo devedor</th></tr>{''.join(dados)}</table>"

        elif "Devedor Completo" in tipo:
            n_sel = st.selectbox("Selecione:", sorted(df_c['Nome'].unique()))
            titulo_rel = f"HISTÓRICO COMPLETO: {n_sel}"
            v_c = df_v[df_v['Cliente'] == n_sel]
            dados = [f"<tr><td>{rv['Data']}</td><td>{rv['Tipo']}</td><td>R$ {rv['Valor']:.2f}</td></tr>" for _, rv in v_c.iterrows()]
            tabela_html = f"<table class='print-table'><tr><th>Data</th><th>Tipo</th><th>Valor</th></tr>{''.join(dados)}</table>"

        elif "Todos por Período" in tipo:
            c1, c2 = st.columns(2)
            di, df = c1.date_input("Início", agora_sp), c2.date_input("Fim", agora_sp)
            titulo_rel = f"RELATÓRIO GERAL: {di.strftime('%d/%m/%Y')} a {df.strftime('%d/%m/%Y')}"
            mask = (df_v['dt_obj'] >= di) & (df_v['dt_obj'] <= df)
            v_f = df_v[mask]
            dados = [f"<tr><td>{rv['Data']}</td><td>{rv['Cliente']}</td><td>{rv['Tipo']}</td><td>R$ {rv['Valor']:.2f}</td></tr>" for _, rv in v_f.iterrows()]
            tabela_html = f"<table class='print-table'><tr><th>Data</th><th>Cliente</th><th>Tipo</th><th>Valor</th></tr>{''.join(dados)}</table>"

        elif "Devedor por Período" in tipo:
            n_sel = st.selectbox("Selecione o Cliente:", sorted(df_c['Nome'].unique()))
            c1, c2 = st.columns(2)
            di, df = c1.date_input("De:", agora_sp), c2.date_input("Até:", agora_sp)
            titulo_rel = f"EXTRATO {n_sel}: {di.strftime('%d/%m/%Y')} a {df.strftime('%d/%m/%Y')}"
            mask = (df_v['Cliente'] == n_sel) & (df_v['dt_obj'] >= di) & (df_v['dt_obj'] <= df)
            v_f = df_v[mask]
            dados = [f"<tr><td>{rv['Data']}</td><td>{rv['Tipo']}</td><td>R$ {rv['Valor']:.2f}</td></tr>" for _, rv in v_f.iterrows()]
            tabela_html = f"<table class='print-table'><tr><th>Data</th><th>Tipo</th><th>Valor</th></tr>{''.join(dados)}</table>"

        st.divider()
        st.markdown(f"<h3 style='text-align:center;'>{titulo_rel}</h3>", unsafe_allow_html=True)
        st.markdown(tabela_html, unsafe_allow_html=True)
        st.info("Para salvar ou imprimir: Use Ctrl + P.")

    # --- 8. TELAS INTERNAS (VENDAS RECUPERADAS) ---
    else:
        st.markdown('<div class="btn-voltar">', unsafe_allow_html=True)
        if st.button("⬅️ VOLTAR AO MENU"):
            st.session_state.tela_atual = "home"; st.session_state.cliente_selecionado = None
            if 'op' in st.session_state: del st.session_state.op
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        if st.session_state.tela_atual == "alunos":
            st.subheader("🎓 Alunos")
            c1, c2 = st.columns(2)
            pf = c1.selectbox("Período:", ["Manhã", "Tarde"])
            tf = c2.selectbox("Turma:", ["1ª Turma", "2ª Turma", "3ª Turma"])
            df_fa = df_c[(df_c['Categoria'] == 'Aluno') & (df_c['Periodo'] == pf) & (df_c['Turma'] == tf)]
            sel_a = st.selectbox("Selecione:", ["-- Selecionar --"] + sorted(df_fa['Nome'].unique().tolist()))
            if sel_a != "-- Selecionar --": st.session_state.cliente_selecionado = (sel_a, "Aluno"); st.session_state.tela_atual = "vendas"; st.rerun()

        elif st.session_state.tela_atual == "funcionarios":
            st.subheader("💼 Funcionários")
            sel_f = st.selectbox("Selecione:", ["-- Selecionar --"] + sorted(df_c[df_c['Categoria'] == 'Funcionário']['Nome'].unique().tolist()))
            if sel_f != "-- Selecionar --": st.session_state.cliente_selecionado = (sel_f, "Funcionário"); st.session_state.tela_atual = "vendas"; st.rerun()

        elif st.session_state.tela_atual == "devedores":
            st.subheader("📊 Devedores")
            total_r = 0
            for _, r in df_c.iterrows():
                v_cli = df_v[df_v['Cliente'] == r['Nome']]
                saldo = v_cli[v_cli['Tipo'] == 'Compra']['Valor'].sum() - v_cli[v_cli['Tipo'] == 'Pagamento']['Valor'].sum()
                if saldo > 0:
                    if st.button(f"{r['Nome']} ➔ R$ {saldo:.2f}", key=f"d_{r['Nome']}"):
                        st.session_state.cliente_selecionado = (r['Nome'], r['Categoria'])
                        st.session_state.tela_atual = "vendas"; st.rerun()
                    total_r += saldo
            st.markdown(f'<div class="balance-card">Total: R$ {total_r:,.2f}</div>', unsafe_allow_html=True)

        if st.session_state.cliente_selecionado:
            cliente_f, cat_f = st.session_state.cliente_selecionado
            v_c = df_v[df_v['Cliente'] == cliente_f]
            divida = v_c[v_c['Tipo'] == 'Compra']['Valor'].sum() - v_c[v_c['Tipo'] == 'Pagamento']['Valor'].sum()
            row_cli = df_c[df_c['Nome'] == cliente_f].iloc[0]
            st.markdown(f'<div class="balance-card"><h2>{cliente_f}</h2><h1>R$ {divida:,.2f}</h1></div>', unsafe_allow_html=True)
            
            c1, c2 = st.columns(2)
            if c1.button("➕ COMPRA"): st.session_state.op = "Compra"
            if c2.button("💵 PAGOU"): st.session_state.op = "Pagamento"

            if 'op' in st.session_state:
                if 'val_temp' not in st.session_state: st.session_state.val_temp = 0.0
                # BOTÕES DE PRODUTOS RESTAURADOS
                produtos = {"Água": 4.0, "Salgado": 8.0, "Suco": 6.0, "Pipoca": 7.0, "Biscoito": 4.0, "Refrigerante": 6.0}
                cols_p = st.columns(3) # 3 por linha para ficar organizado
                for i, (prod, preco) in enumerate(produtos.items()):
                    if cols_p[i%3].button(f"{prod}\nR${preco:.2f}"): 
                        st.session_state.val_temp += preco; st.rerun()
                
                with st.form("lanca"):
                    vf = st.number_input("Valor", value=st.session_state.val_temp)
                    obs = st.text_input("Obs (Opcional):")
                    if st.form_submit_button("✅ CONFIRMAR"):
                        sp_now = get_sp_time()
                        data_br = sp_now.strftime("%d/%m/%Y - %H:%M")
                        new_r = pd.DataFrame([{'ID': sp_now.strftime("%Y%m%d%H%M%S"), 'Cliente': cliente_f, 'Cat_Venda': cat_f, 'Item': obs, 'Valor': vf, 'Data': data_br, 'Tipo': st.session_state.op}])
                        pd.concat([df_v, new_r], ignore_index=True).to_csv(DB_VENDAS, index=False)
                        st.session_state.val_temp = 0.0; del st.session_state.op; st.rerun()
            
            st.divider()
            url = f"https://wa.me/{row_cli['Telefone']}?text=Olá {cliente_f}, seu saldo no Bear Snack é R$ {divida:,.2f}"
            st.markdown(f'<a href="{url}" target="_blank" style="text-decoration:none;"><div style="background-color:#25D366; color:white; padding:15px; border-radius:15px; text-align:center; font-weight:bold;">📲 WHATSAPP</div></a>', unsafe_allow_html=True)
