import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# --- 1. CONFIGURAÇÃO E DESIGN PREMIUM (SEM ALTERAR NOMES) ---
st.set_page_config(page_title="Bear Snack Pro", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .stApp { background-color: #121212; color: #E0E0E0; }
    h1, h2, h3 { color: #D4AF37 !important; text-align: center; }
    .stDivider { border-bottom: 1px solid #333 !important; }

    /* Cards de Saldo */
    .balance-card {
        background: linear-gradient(145deg, #1e1e1e, #252525);
        border: 1px solid #D4AF37;
        color: #FFFFFF;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    }
    .balance-card h1 { color: #00E676 !important; margin: 5px 0; }

    /* Botões com as suas ordens originais */
    .stButton > button {
        width: 100%;
        height: 50px !important;
        border-radius: 12px !important;
        background-color: #2D2D2D !important;
        color: #D4AF37 !important;
        font-weight: bold !important;
        border: 1px solid #444 !important;
    }
    .stButton > button:hover {
        background-color: #D4AF37 !important;
        color: #121212 !important;
    }

    .btn-voltar > button {
        height: 35px !important;
        background-color: #333 !important;
        color: #CCC !important;
        margin-bottom: 20px;
    }

    .print-table {
        width: 100%; border-collapse: collapse; background-color: #1E1E1E; color: white;
    }
    .print-table th, .print-table td {
        border: 1px solid #333; padding: 10px; text-align: left;
    }
    .print-table th { background-color: #D4AF37; color: #121212; }

    /* Estilo WhatsApp */
    .wa-link {
        display: block; background-color: #25D366; color: white !important;
        padding: 15px; border-radius: 12px; text-align: center;
        font-weight: bold; text-decoration: none; margin-top: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

DB_VENDAS = "vendas_bear_final.csv"
DB_CLIENTES = "clientes_bear_final.csv"

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
            try: return datetime.strptime(str(x).split(' - ')[0], "%d/%m/%Y").date()
            except: return get_sp_time().date()
        v['dt_obj'] = v['Data'].apply(parse_dt)
    else: v['dt_obj'] = None
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
        # MANTIDA A ORDEM ORIGINAL DOS BOTÕES
        if st.button("🎓 ALUNOS"): st.session_state.tela_atual = "alunos"; st.rerun()
        if st.button("💼 FUNCIONÁRIOS"): st.session_state.tela_atual = "funcionarios"; st.rerun()
        if st.button("📊 DEVEDORES"): st.session_state.tela_atual = "devedores"; st.rerun()
        if st.button("📄 RELATÓRIOS"): st.session_state.tela_atual = "relatorios"; st.rerun()

    # --- 7. TELA DE RELATÓRIOS ---
    elif st.session_state.tela_atual == "relatorios":
        st.markdown('<div class="btn-voltar">', unsafe_allow_html=True)
        if st.button("⬅️ VOLTAR AO MENU"): st.session_state.tela_atual = "home"; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
        tipo = st.selectbox("Tipo de Relatório:", 
                            ["Relatório Completo (Todos Devedores)", 
                             "Devedor Completo (Individual)", 
                             "Todos por Período (Calendário)", 
                             "Devedor por Período (Calendário)"])
        
        tabela_html, titulo_rel, texto_txt = "", "", ""
        agora_sp = get_sp_time().date()

        if "Relatório Completo" in tipo:
            titulo_rel = "RELATÓRIO GERAL DE DEVEDORES"
            total_geral = 0
            dados_html, dados_txt = [], [f"{titulo_rel}\n{'='*30}\nNOME{' '*16}SALDO\n{'-'*30}"]
            for _, r in df_c.iterrows():
                v_cli = df_v[df_v['Cliente'] == r['Nome']]
                saldo = v_cli[v_cli['Tipo'] == 'Compra']['Valor'].sum() - v_cli[v_cli['Tipo'] == 'Pagamento']['Valor'].sum()
                if saldo > 0: 
                    total_geral += saldo
                    dados_html.append(f"<tr><td>{r['Nome']}</td><td>R$ {saldo:.2f}</td></tr>")
                    dados_txt.append(f"{r['Nome'][:20]:<20} R$ {saldo:>7.2f}")
            dados_txt.append(f"{'-'*30}\nTOTAL GERAL:{' '*10}R$ {total_geral:>7.2f}")
            tabela_html = f"<table class='print-table'><tr><th>Nome</th><th>Saldo</th></tr>{''.join(dados_html)}<tr><td><b>TOTAL</b></td><td><b>R$ {total_geral:.2f}</b></td></tr></table>"
            texto_txt = "\n".join(dados_txt)

        elif "Devedor Completo" in tipo:
            n_sel = st.selectbox("Selecione:", sorted(df_c['Nome'].unique()))
            titulo_rel = f"HISTÓRICO: {n_sel}"
            v_c = df_v[df_v['Cliente'] == n_sel]
            saldo_f = v_c[v_c['Tipo'] == 'Compra']['Valor'].sum() - v_c[v_c['Tipo'] == 'Pagamento']['Valor'].sum()
            dados_html = [f"<tr><td>{rv['Data']}</td><td>{rv['Tipo']}</td><td>R$ {rv['Valor']:.2f}</td></tr>" for _, rv in v_c.iterrows()]
            dados_txt = [f"{titulo_rel}\n{'='*30}\nDATA{' '*11}TIPO{' '*6}VALOR\n{'-'*30}"]
            for _, rv in v_c.iterrows():
                dados_txt.append(f"{rv['Data'][:14]:<14} {rv['Tipo'][:8]:<8} R${rv['Valor']:>6.2f}")
            dados_txt.append(f"{'-'*30}\nSALDO DEVEDOR:{' '*8}R$ {saldo_f:>7.2f}")
            tabela_html = f"<table class='print-table'><tr><th>Data</th><th>Tipo</th><th>Valor</th></tr>{''.join(dados_html)}<tr><td colspan='2'><b>SALDO ATUAL</b></td><td><b>R$ {saldo_f:.2f}</b></td></tr></table>"
            texto_txt = "\n".join(dados_txt)

        elif "Todos por Período" in tipo:
            c1, c2 = st.columns(2)
            di, df = c1.date_input("Início", agora_sp), c2.date_input("Fim", agora_sp)
            titulo_rel = f"GERAL: {di.strftime('%d/%m')} a {df.strftime('%d/%m')}"
            mask = (df_v['dt_obj'] >= di) & (df_v['dt_obj'] <= df)
            v_f = df_v[mask]
            vendas_t = v_f[v_f['Tipo'] == 'Compra']['Valor'].sum()
            pagos_t = v_f[v_f['Tipo'] == 'Pagamento']['Valor'].sum()
            dados_html = [f"<tr><td>{rv['Data']}</td><td>{rv['Cliente']}</td><td>{rv['Tipo']}</td><td>R$ {rv['Valor']:.2f}</td></tr>" for _, rv in v_f.iterrows()]
            dados_txt = [f"{titulo_rel}\n{'='*30}\nDATA{' '*11}CLIENTE{' '*5}VALOR\n{'-'*30}"]
            for _, rv in v_f.iterrows():
                dados_txt.append(f"{rv['Data'][:14]:<14} {rv['Cliente'][:12]:<12} R${rv['Valor']:>6.2f}")
            dados_txt.append(f"{'-'*30}\nTOTAL VENDAS:{' '*9}R$ {vendas_t:>7.2f}\nTOTAL PAGOS:{' '*10}R$ {pagos_t:>7.2f}")
            tabela_html = f"<table class='print-table'><tr><th>Data</th><th>Cliente</th><th>Tipo</th><th>Valor</th></tr>{''.join(dados_html)}</table>"
            texto_txt = "\n".join(dados_txt)

        elif "Devedor por Período" in tipo:
            n_sel = st.selectbox("Selecione:", sorted(df_c['Nome'].unique()))
            c1, c2 = st.columns(2)
            di, df = c1.date_input("De:", agora_sp), c2.date_input("Até:", agora_sp)
            titulo_rel = f"EXTRATO {n_sel}\n{di.strftime('%d/%m')} a {df.strftime('%d/%m')}"
            mask = (df_v['Cliente'] == n_sel) & (df_v['dt_obj'] >= di) & (df_v['dt_obj'] <= df)
            v_f = df_v[mask]
            subtotal = v_f[v_f['Tipo'] == 'Compra']['Valor'].sum() - v_f[v_f['Tipo'] == 'Pagamento']['Valor'].sum()
            dados_html = [f"<tr><td>{rv['Data']}</td><td>{rv['Tipo']}</td><td>R$ {rv['Valor']:.2f}</td></tr>" for _, rv in v_f.iterrows()]
            dados_txt = [f"{titulo_rel}\n{'='*30}\nDATA{' '*11}TIPO{' '*6}VALOR\n{'-'*30}"]
            for _, rv in v_f.iterrows():
                dados_txt.append(f"{rv['Data'][:14]:<14} {rv['Tipo'][:8]:<8} R${rv['Valor']:>6.2f}")
            dados_txt.append(f"{'-'*30}\nSUBTOTAL PERÍODO:{' '*5}R$ {subtotal:>7.2f}")
            tabela_html = f"<table class='print-table'><tr><th>Data</th><th>Tipo</th><th>Valor</th></tr>{''.join(dados_html)}<tr><td colspan='2'><b>SUBTOTAL</b></td><td><b>R$ {subtotal:.2f}</b></td></tr></table>"
            texto_txt = "\n".join(dados_txt)

        st.divider()
        st.download_button(label="📥 BAIXAR TXT PARA IMPRESSÃO", data=texto_txt, file_name=f"relatorio_bear.txt", mime="text/plain")
        st.markdown(f"<h3 style='text-align:center;'>{titulo_rel}</h3>", unsafe_allow_html=True)
        st.markdown(tabela_html, unsafe_allow_html=True)

    # --- 8. TELAS INTERNAS ---
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
            pf, tf = c1.selectbox("Período:", ["Manhã", "Tarde"]), c2.selectbox("Turma:", ["1ª Turma", "2ª Turma", "3ª Turma"])
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
                
                st.write("Valores Rápidos:")
                cv1, cv2, cv3 = st.columns(3)
                if cv1.button("Fruta R$ 4,00"): st.session_state.val_temp += 4.0; st.rerun()
                if cv2.button("Suco Natural R$ 7,00"): st.session_state.val_temp += 7.0; st.rerun()
                if cv3.button("Bolo de Pote R$ 8,00"): st.session_state.val_temp += 8.0; st.rerun()

                produtos = {"Água": 4.0, "Salgado": 8.0, "Suco": 6.0, "Pipoca": 7.0, "Biscoito": 4.0, "Refri": 6.0}
                cols_p = st.columns(3)
                for i, (prod, preco) in enumerate(produtos.items()):
                    if cols_p[i%3].button(f"{prod}\n${preco:.2f}"): 
                        st.session_state.val_temp += preco; st.rerun()
                
                with st.form("lanca"):
                    vf = st.number_input("Valor Final", value=st.session_state.val_temp)
                    obs = st.text_input("Obs:")
                    if st.form_submit_button("✅ CONFIRMAR"):
                        sp_now = get_sp_time()
                        data_br = sp_now.strftime("%d/%m/%Y - %H:%M")
                        new_r = pd.DataFrame([{'ID': sp_now.strftime("%Y%m%d%H%M%S"), 'Cliente': cliente_f, 'Cat_Venda': cat_f, 'Item': obs, 'Valor': vf, 'Data': data_br, 'Tipo': st.session_state.op}])
                        pd.concat([df_v, new_r], ignore_index=True).to_csv(DB_VENDAS, index=False)
                        st.session_state.val_temp = 0.0; del st.session_state.op; st.rerun()
            
            st.divider()
            url = f"https://wa.me/{row_cli['Telefone']}?text=Olá {cliente_f}, seu saldo no Bear Snack é R$ {divida:,.2f}"
            st.markdown(f'<a href="{url}" target="_blank" class="wa-link">📲 WHATSAPP</a>', unsafe_allow_html=True)
