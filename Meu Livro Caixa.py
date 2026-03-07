import streamlit as st
import pandas as pd
import os
from datetime import datetime

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
        border-left: 6px solid #CD853F; color: black;
    }
    .btn-voltar > button {
        height: 35px !important; background-color: #D2B48C !important;
        color: #4E3620 !important; margin-bottom: 20px;
    }
    /* Estilo do Relatório para Print */
    .relatorio-print {
        background-color: white; color: black; padding: 15px;
        border: 1px solid #ccc; border-radius: 10px; font-family: sans-serif;
    }
    .tabela-relatorio {
        width: 100%; border-collapse: collapse; margin-top: 10px;
    }
    .tabela-relatorio th, .tabela-relatorio td {
        border-bottom: 1px solid #eee; padding: 8px; text-align: left; font-size: 13px;
    }
    </style>
    """, unsafe_allow_html=True)

DB_VENDAS = "vendas_bear_final.csv"
DB_CLIENTES = "clientes_bear_final.csv"

# --- 2. FUNÇÕES DE DADOS ---
def load_data():
    c = pd.read_csv(DB_CLIENTES) if os.path.exists(DB_CLIENTES) else pd.DataFrame(columns=['Nome', 'Telefone', 'Categoria', 'Periodo', 'Turma', 'Limite'])
    v = pd.read_csv(DB_VENDAS) if os.path.exists(DB_VENDAS) else pd.DataFrame(columns=['ID', 'Cliente', 'Cat_Venda', 'Item', 'Valor', 'Data', 'Tipo'])
    
    for col in ['Categoria', 'Periodo', 'Turma', 'Limite']:
        if col not in c.columns: c[col] = 50.0 if col == 'Limite' else "N/A"
    
    if not v.empty:
        v['dt_obj'] = v['Data'].apply(lambda x: datetime.strptime(f"{str(x)[:5]}/2026", "%d/%m/%Y").date() if isinstance(x, str) else datetime.now().date())
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
    # --- 5. SIDEBAR (GERENCIAMENTO) ---
    with st.sidebar:
        if st.button("🚪 SAIR"): st.session_state.logado = False; st.rerun()
        st.divider()
        st.subheader("👤 Gerenciar Cliente")
        lista = ["-- Novo Cadastro --"] + sorted(df_c['Nome'].unique().tolist())
        c_edit = st.selectbox("🔍 Buscar/Editar:", options=lista)
        
        v_n, v_t, v_cat, v_lim, v_p, v_tur = "", "", "Aluno", 50.0, "Manhã", "1ª Turma"
        edit = False
        if c_edit != "-- Novo Cadastro --":
            edit = True
            d = df_c[df_c['Nome'] == c_edit].iloc[0]
            v_n, v_t, v_cat, v_lim, v_p, v_tur = d['Nome'], str(d['Telefone']), d['Categoria'], float(d['Limite']), d['Periodo'], d['Turma']

        n = st.text_input("Nome", value=v_n)
        t = st.text_input("WhatsApp", value=v_t)
        cat = st.selectbox("Tipo:", ["Aluno", "Funcionário"], index=0 if v_cat == "Aluno" else 1)
        lim = st.number_input("Limite R$", value=v_lim)
        p, tur = "N/A", "N/A"
        if cat == "Aluno":
            p = st.selectbox("Período:", ["Manhã", "Tarde"], index=0 if v_p == "Manhã" else 1)
            tur = st.selectbox("Turma:", ["1ª Turma", "2ª Turma", "3ª Turma"], index=0 if "1" in v_tur else (1 if "2" in v_tur else 2))

        if st.button("SALVAR"):
            if n:
                df_t, _ = load_data()
                if edit: df_t = df_t[df_t['Nome'] != c_edit]
                new = pd.DataFrame([{'Nome': n, 'Telefone': t, 'Categoria': cat, 'Periodo': p, 'Turma': tur, 'Limite': lim}])
                pd.concat([df_t, new], ignore_index=True).to_csv(DB_CLIENTES, index=False)
                st.success("Salvo!"); st.rerun()

    # --- 6. TELA HOME (MENU + BUSCA) ---
    if st.session_state.tela_atual == "home":
        st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
        if os.path.exists("logo.png"): st.image("logo.png", width=100)
        else: st.title("🐻 Bear Snack")
        st.markdown("</div>", unsafe_allow_html=True)

        busca = st.text_input("🔍 Buscar Cliente por Nome:", placeholder="Digite para buscar...").strip()
        if busca:
            m = df_c[df_c['Nome'].str.contains(busca, case=False, na=False)]
            for _, r in m.head(3).iterrows():
                if st.button(f"✅ Atender: {r['Nome']}", key=f"f_{r['Nome']}"):
                    st.session_state.cliente_selecionado = (r['Nome'], r['Categoria'])
                    st.session_state.tela_atual = "vendas"; st.rerun()

        st.divider()
        if st.button("🎓 ALUNOS"): st.session_state.tela_atual = "alunos"; st.rerun()
        if st.button("💼 FUNCIONÁRIOS"): st.session_state.tela_atual = "funcionarios"; st.rerun()
        if st.button("📊 DEVEDORES"): st.session_state.tela_atual = "devedores"; st.rerun()
        if st.button("📄 IMPRIMIR RELATÓRIO"): st.session_state.tela_atual = "relatorios"; st.rerun()

    # --- 7. TELA DE RELATÓRIOS (IMPRESSÃO) ---
    elif st.session_state.tela_atual == "relatorios":
        st.markdown('<div class="btn-voltar">', unsafe_allow_html=True)
        if st.button("⬅️ VOLTAR AO MENU"): st.session_state.tela_atual = "home"; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.subheader("Relatórios por Período")
        c1, c2 = st.columns(2)
        d_ini = c1.date_input("Início", datetime.now())
        d_fim = c2.date_input("Fim", datetime.now())
        
        tipo = st.selectbox("Tipo de Filtro:", ["Vendas Gerais", "Devedores Atuais (Sem data)", "Extrato de um Cliente"])
        
        tabela_html, titulo_rel = "", ""

        if tipo == "Vendas Gerais":
            mask = (df_v['dt_obj'] >= d_ini) & (df_v['dt_obj'] <= d_fim)
            df_f = df_v[mask]
            titulo_rel = f"VENDAS: {d_ini.strftime('%d/%m')} a {d_fim.strftime('%d/%m')}"
            colunas = ["Data", "Cliente", "Tipo", "Valor"]
            tabela_html = f"<table class='tabela-relatorio'><tr>{''.join([f'<th>{c}</th>' for c in colunas])}</tr>"
            for _, r in df_f.iterrows():
                tabela_html += f"<tr><td>{r['Data']}</td><td>{r['Cliente']}</td><td>{r['Tipo']}</td><td>R$ {r['Valor']:.2f}</td></tr>"
            tabela_html += "</table>"

        elif tipo == "Devedores Atuais (Sem data)":
            titulo_rel = "LISTA GERAL DE DEVEDORES"
            tabela_html = "<table class='tabela-relatorio'><tr><th>Cliente</th><th>Saldo</th></tr>"
            for _, r in df_c.iterrows():
                v_cli = df_v[df_v['Cliente'] == r['Nome']]
                s = v_cli[v_cli['Tipo'] == 'Compra']['Valor'].sum() - v_cli[v_cli['Tipo'] == 'Pagamento']['Valor'].sum()
                if s > 0: tabela_html += f"<tr><td>{r['Nome']}</td><td>R$ {s:.2f}</td></tr>"
            tabela_html += "</table>"

        elif tipo == "Extrato de um Cliente":
            n_sel = st.selectbox("Selecione o Cliente:", sorted(df_c['Nome'].unique()))
            mask = (df_v['Cliente'] == n_sel) & (df_v['dt_obj'] >= d_ini) & (df_v['dt_obj'] <= d_fim)
            df_f = df_v[mask]
            titulo_rel = f"EXTRATO: {n_sel} ({d_ini.strftime('%d/%m')} a {df_fim.strftime('%d/%m')})"
            tabela_html = f"<table class='tabela-relatorio'><tr><th>Data</th><th>Tipo</th><th>Valor</th></tr>"
            for _, r in df_f.iterrows():
                tabela_html += f"<tr><td>{r['Data']}</td><td>{r['Tipo']}</td><td>R$ {r['Valor']:.2f}</td></tr>"
            tabela_html += "</table>"

        st.markdown(f'<div class="relatorio-print"><h2 style="text-align:center;">🐻 BEAR SNACK</h2><p style="text-align:center;"><b>{titulo_rel}</b></p>{tabela_html}</div>', unsafe_allow_html=True)
        st.info("Pressione Ctrl+P para imprimir ou salvar em PDF.")

    # --- 8. TELAS DE VENDAS E SELEÇÃO ---
    else:
        st.markdown('<div class="btn-voltar">', unsafe_allow_html=True)
        if st.button("⬅️ VOLTAR"):
            st.session_state.tela_atual = "home"; st.session_state.cliente_selecionado = None
            if 'op' in st.session_state: del st.session_state.op
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        if st.session_state.tela_atual == "alunos":
            c1, c2 = st.columns(2)
            pf = c1.selectbox("Período:", ["Manhã", "Tarde"])
            tf = c2.selectbox("Turma:", ["1ª Turma", "2ª Turma", "3ª Turma"])
            df_fa = df_c[(df_c['Categoria'] == 'Aluno') & (df_c['Periodo'] == pf) & (df_c['Turma'] == tf)]
            sel_a = st.selectbox("Selecione:", ["-- Escolher --"] + sorted(df_fa['Nome'].unique().tolist()))
            if sel_a != "-- Escolher --": st.session_state.cliente_selecionado = (sel_a, "Aluno"); st.session_state.tela_atual = "vendas"; st.rerun()

        elif st.session_state.tela_atual == "funcionarios":
            sel_f = st.selectbox("Selecione:", ["-- Escolher --"] + sorted(df_c[df_c['Categoria'] == 'Funcionário']['Nome'].unique().tolist()))
            if sel_f != "-- Escolher --": st.session_state.cliente_selecionado = (sel_f, "Funcionário"); st.session_state.tela_atual = "vendas"; st.rerun()

        elif st.session_state.tela_atual == "devedores":
            total_dev = 0
            for _, r in df_c.iterrows():
                v_cli = df_v[df_v['Cliente'] == r['Nome']]
                s = v_cli[v_cli['Tipo'] == 'Compra']['Valor'].sum() - v_cli[v_cli['Tipo'] == 'Pagamento']['Valor'].sum()
                if s > 0:
                    if st.button(f"{r['Nome']} ➔ R$ {s:.2f}", key=f"d_{r['Nome']}"):
                        st.session_state.cliente_selecionado = (r['Nome'], r['Categoria'])
                        st.session_state.tela_atual = "vendas"; st.rerun()
                    total_dev += s
            st.markdown(f'<div class="balance-card">Total: R$ {total_dev:,.2f}</div>', unsafe_allow_html=True)

        # ÁREA FINAL DE LANÇAMENTO
        if st.session_state.cliente_selecionado:
            cliente, categoria = st.session_state.cliente_selecionado
            v_c = df_v[df_v['Cliente'] == cliente]
            saldo = v_c[v_c['Tipo'] == 'Compra']['Valor'].sum() - v_c[v_c['Tipo'] == 'Pagamento']['Valor'].sum()
            row = df_c[df_c['Nome'] == cliente].iloc[0]
            
            st.markdown(f'<div class="balance-card"><h2>{cliente}</h2><h1>R$ {saldo:,.2f}</h1><p>Limite: R$ {row["Limite"]:.2f}</p></div>', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            if col1.button("➕ COMPRA"): st.session_state.op = "Compra"
            if col2.button("💵 PAGOU"): st.session_state.op = "Pagamento"

            if 'op' in st.session_state:
                if 'val_t' not in st.session_state: st.session_state.val_t = 0.0
                prods = {"Água": 4.0, "Salgado": 8.0, "Suco": 6.0, "Pipoca": 7.0, "Biscoito": 4.0, "Refrigerante": 6.0}
                cols = st.columns(3)
                for i, (p_n, p_v) in enumerate(prods.items()):
                    if cols[i%3].button(f"{p_n}\nR${p_v}"): st.session_state.val_t += p_v; st.rerun()
                
                with st.form("f_venda"):
                    vf = st.number_input("Valor Final", value=st.session_state.val_t)
                    obs = st.text_input("Obs:")
                    if st.form_submit_button("✅ CONFIRMAR"):
                        new_v = pd.DataFrame([{'ID': datetime.now().strftime("%Y%m%d%H%M%S"), 'Cliente': cliente, 'Cat_Venda': categoria, 'Item': obs, 'Valor': vf, 'Data': datetime.now().strftime("%d/%m - %H:%M"), 'Tipo': st.session_state.op}])
                        pd.concat([df_v, new_v], ignore_index=True).to_csv(DB_VENDAS, index=False)
                        st.session_state.val_t = 0.0; del st.session_state.op; st.rerun()
            
            st.divider()
            url = f"https://wa.me/{row['Telefone']}?text=Olá {cliente}, seu saldo no Bear Snack é R$ {saldo:,.2f}"
            st.markdown(f'<a href="{url}" target="_blank" style="text-decoration:none;"><div style="background-color:#25D366; color:white; padding:15px; border-radius:15px; text-align:center; font-weight:bold;">📲 ENVIAR COBRANÇA</div></a>', unsafe_allow_html=True)
