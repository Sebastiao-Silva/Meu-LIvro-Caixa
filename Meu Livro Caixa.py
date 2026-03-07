import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# --- 1. CONFIGURAÇÃO E DESIGN PREMIUM ---
st.set_page_config(page_title="Bear Snack Pro", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    /* Fundo e Estética Geral */
    .stApp { background-color: #121212; color: #E0E0E0; font-family: 'Inter', sans-serif; }
    
    /* Títulos e Identidade */
    h1, h2, h3 { color: #D4AF37 !important; text-align: center; font-weight: 700 !important; }
    .stDivider { border-bottom: 1px solid #333 !important; }

    /* Card de Saldo Elegante */
    .balance-card {
        background: linear-gradient(145deg, #1e1e1e, #252525);
        border: 1px solid #D4AF37;
        color: #FFFFFF;
        padding: 25px;
        border-radius: 18px;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.4);
    }
    .balance-card h1 { color: #00E676 !important; font-size: 2.8rem !important; margin: 10px 0; }
    .balance-card h2 { color: #D4AF37 !important; font-size: 1.2rem !important; opacity: 0.9; }

    /* Botões de Ação Principal */
    .stButton > button {
        width: 100%;
        height: 56px !important;
        border-radius: 12px !important;
        background-color: #2D2D2D !important;
        color: #D4AF37 !important;
        font-weight: 600 !important;
        border: 1px solid #444 !important;
        transition: all 0.2s ease-in-out !important;
        letter-spacing: 0.5px;
        font-size: 15px !important;
    }
    .stButton > button:hover {
        background-color: #D4AF37 !important;
        color: #121212 !important;
        border-color: #FFF !important;
        transform: scale(1.02);
    }

    /* Botões Rápidos e Internos */
    .btn-voltar > button {
        height: 42px !important;
        background-color: #333 !important;
        color: #AAA !important;
        border: none !important;
        margin-bottom: 15px;
    }

    /* Tabela de Relatórios Estilizada */
    .print-table {
        width: 100%;
        border-collapse: collapse;
        background-color: #1E1E1E;
        color: #DDD;
        border-radius: 12px;
        overflow: hidden;
        margin-top: 20px;
        border: 1px solid #333;
    }
    .print-table th {
        background-color: #D4AF37;
        color: #121212;
        padding: 14px;
        font-weight: bold;
        text-align: left;
    }
    .print-table td {
        padding: 14px;
        border-bottom: 1px solid #2A2A2A;
        font-size: 14px;
    }
    .print-table tr:last-child { border-bottom: none; }
    .print-table tr:nth-child(even) { background-color: #252525; }

    /* Estilização de Entradas de Texto/Select */
    .stTextInput input, .stSelectbox div, .stNumberInput input {
        background-color: #1E1E1E !important;
        color: #FFF !important;
        border: 1px solid #444 !important;
        border-radius: 8px !important;
    }
    
    /* WhatsApp Button */
    .wa-btn {
        background-color: #25D366;
        color: white !important;
        padding: 16px;
        border-radius: 14px;
        text-align: center;
        font-weight: bold;
        text-decoration: none;
        display: block;
        margin-top: 15px;
        box-shadow: 0 4px 12px rgba(37, 211, 102, 0.3);
    }
    </style>
    """, unsafe_allow_html=True)

DB_VENDAS = "vendas_bear_final.csv"
DB_CLIENTES = "clientes_bear_final.csv"

def get_sp_time():
    return datetime.utcnow() - timedelta(hours=3)

# --- 2. GESTÃO DE DADOS ---
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

# --- 3. ESTADO DA APP ---
if 'logado' not in st.session_state: st.session_state.logado = False
if 'tela_atual' not in st.session_state: st.session_state.tela_atual = "home"
if 'cliente_selecionado' not in st.session_state: st.session_state.cliente_selecionado = None

# --- 4. TELA DE LOGIN ---
if not st.session_state.logado:
    st.markdown("<br><br>", unsafe_allow_html=True)
    if os.path.exists("logo.png"): 
        st.image("logo.png", width=200)
    else: 
        st.markdown("<h1>🐻 BEAR SNACK PRO</h1><p style='text-align:center; color:#888;'>Painel de Administração</p>", unsafe_allow_html=True)
    
    with st.container():
        st.markdown("<div style='max-width:300px; margin:auto;'>", unsafe_allow_html=True)
        user = st.text_input("Usuário")
        pw = st.text_input("Senha", type="password")
        if st.button("ENTRAR NO SISTEMA"):
            if user == "admin" and pw == "bear123":
                st.session_state.logado = True
                st.rerun()
            else: st.error("Acesso negado")
        st.markdown("</div>", unsafe_allow_html=True)

else:
    # --- 5. MENU LATERAL (SIDEBAR) ---
    with st.sidebar:
        st.markdown("### 🛠️ GESTÃO")
        if st.button("🚪 SAIR"):
            st.session_state.logado = False
            st.rerun()
        st.divider()
        st.subheader("👤 Cadastro & Edição")
        lista_clientes = ["-- Novo Cadastro --"] + sorted(df_c['Nome'].unique().tolist())
        cliente_para_editar = st.selectbox("Buscar/Editar:", options=lista_clientes)
        
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

        if st.button("💾 SALVAR DADOS"):
            if n:
                df_temp, _ = load_data()
                if editando: df_temp = df_temp[df_temp['Nome'] != cliente_para_editar]
                new_row = pd.DataFrame([{'Nome': n, 'Telefone': t, 'Categoria': cat, 'Periodo': p, 'Turma': tur, 'Limite': lim}])
                pd.concat([df_temp, new_row], ignore_index=True).to_csv(DB_CLIENTES, index=False)
                st.success("Dados Gravados!"); st.rerun()

    # --- 6. TELA PRINCIPAL ---
    if st.session_state.tela_atual == "home":
        if os.path.exists("logo.png"): st.image("logo.png", width=120)
        else: st.markdown("<h1>🐻 Bear Snack</h1>", unsafe_allow_html=True)

        nome_busca = st.text_input("🔍 Localizar Cliente:", placeholder="Nome do cliente...").strip()
        if nome_busca:
            matches = df_c[df_c['Nome'].str.contains(nome_busca, case=False, na=False)]
            for _, row in matches.head(3).iterrows():
                if st.button(f"👤 Atender: {row['Nome']}", key=f"f_{row['Nome']}"):
                    st.session_state.cliente_selecionado = (row['Nome'], row['Categoria'])
                    st.session_state.tela_atual = "vendas"; st.rerun()

        st.divider()
        c1, c2 = st.columns(2)
        if c1.button("🎓 ALUNOS"): st.session_state.tela_atual = "alunos"; st.rerun()
        if c2.button("💼 STAFF"): st.session_state.tela_atual = "funcionarios"; st.rerun()
        if c1.button("📊 DÍVIDAS"): st.session_state.tela_atual = "devedores"; st.rerun()
        if c2.button("📄 RELATÓRIO"): st.session_state.tela_atual = "relatorios"; st.rerun()

    # --- 7. TELA DE RELATÓRIOS ---
    elif st.session_state.tela_atual == "relatorios":
        st.markdown('<div class="btn-voltar">', unsafe_allow_html=True)
        if st.button("⬅️ MENU"): st.session_state.tela_atual = "home"; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
        tipo = st.selectbox("Tipo de Relatório:", 
                            ["Geral de Devedores", "Individual Completo", "Período (Todos)", "Período (Individual)"])
        
        tabela_html, titulo_rel, texto_txt = "", "", ""
        agora_sp = get_sp_time().date()

        if "Geral" in tipo:
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

        elif "Individual" in tipo and "Período" not in tipo:
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

        elif "Período (Todos)" in tipo:
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

        elif "Período (Individual)" in tipo:
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
        st.markdown(f"<h3>{titulo_rel}</h3>", unsafe_allow_html=True)
        st.markdown(tabela_html, unsafe_allow_html=True)

    # --- 8. TELAS DE CATEGORIAS E VENDAS ---
    else:
        st.markdown('<div class="btn-voltar">', unsafe_allow_html=True)
        if st.button("⬅️ VOLTAR AO MENU"):
            st.session_state.tela_atual = "home"; st.session_state.cliente_selecionado = None
            if 'op' in st.session_state: del st.session_state.op
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        if st.session_state.tela_atual == "alunos":
            st.subheader("🎓 Área de Alunos")
            c1, c2 = st.columns(2)
            pf, tf = c1.selectbox("Período:", ["Manhã", "Tarde"]), c2.selectbox("Turma:", ["1ª Turma", "2ª Turma", "3ª Turma"])
            df_fa = df_c[(df_c['Categoria'] == 'Aluno') & (df_c['Periodo'] == pf) & (df_c['Turma'] == tf)]
            sel_a = st.selectbox("Selecione o Aluno:", ["-- Selecionar --"] + sorted(df_fa['Nome'].unique().tolist()))
            if sel_a != "-- Selecionar --": 
                st.session_state.cliente_selecionado = (sel_a, "Aluno"); st.session_state.tela_atual = "vendas"; st.rerun()

        elif st.session_state.tela_atual == "funcionarios":
            st.subheader("💼 Área de Funcionários")
            sel_f = st.selectbox("Selecione:", ["-- Selecionar --"] + sorted(df_c[df_c['Categoria'] == 'Funcionário']['Nome'].unique().tolist()))
            if sel_f != "-- Selecionar --": 
                st.session_state.cliente_selecionado = (sel_f, "Funcionário"); st.session_state.tela_atual = "vendas"; st.rerun()

        elif st.session_state.tela_atual == "devedores":
            st.subheader("📊 Lista de Devedores")
            total_r = 0
            for _, r in df_c.iterrows():
                v_cli = df_v[df_v['Cliente'] == r['Nome']]
                saldo = v_cli[v_cli['Tipo'] == 'Compra']['Valor'].sum() - v_cli[v_cli['Tipo'] == 'Pagamento']['Valor'].sum()
                if saldo > 0:
                    if st.button(f"{r['Nome']} ➔ R$ {saldo:.2f}", key=f"d_{r['Nome']}"):
                        st.session_state.cliente_selecionado = (r['Nome'], r['Categoria'])
                        st.session_state.tela_atual = "vendas"; st.rerun()
                    total_r += saldo
            st.markdown(f'<div class="balance-card"><h2>Dívida Total</h2><h1>R$ {total_r:,.2f}</h1></div>', unsafe_allow_html=True)

        if st.session_state.cliente_selecionado:
            cliente_f, cat_f = st.session_state.cliente_selecionado
            v_c = df_v[df_v['Cliente'] == cliente_f]
            divida = v_c[v_c['Tipo'] == 'Compra']['Valor'].sum() - v_c[v_c['Tipo'] == 'Pagamento']['Valor'].sum()
            row_cli = df_c[df_c['Nome'] == cliente_f].iloc[0]
            
            st.markdown(f'<div class="balance-card"><h2>{cliente_f}</h2><h1>R$ {divida:,.2f}</h1></div>', unsafe_allow_html=True)
            
            c1, c2 = st.columns(2)
            if c1.button("➕ NOVA COMPRA"): st.session_state.op = "Compra"
            if c2.button("💵 PAGAMENTO"): st.session_state.op = "Pagamento"

            if 'op' in st.session_state:
                if 'val_temp' not in st.session_state: st.session_state.val_temp = 0.0
                
                st.markdown("<p style='color:#D4AF37; margin-bottom:5px;'>Valores Rápidos:</p>", unsafe_allow_html=True)
                cv1, cv2, cv3 = st.columns(3)
                if cv1.button("🍎 Fruta\nR$ 4,00"): st.session_state.val_temp += 4.0; st.rerun()
                if cv2.button("🥤 Suco\nR$ 7,00"): st.session_state.val_temp += 7.0; st.rerun()
                if cv3.button("🍰 Bolo\nR$ 8,00"): st.session_state.val_temp += 8.0; st.rerun()

                produtos = {"💧 Água": 4.0, "🥐 Salgado": 8.0, "🍹 Suco": 6.0, "🍿 Pipoca": 7.0, "🍪 Biscoit": 4.0, "🥤 Refri": 6.0}
                cols_p = st.columns(3)
                for i, (prod, preco) in enumerate(produtos.items()):
                    if cols_p[i%3].button(f"{prod}\n${preco:.2f}"): 
                        st.session_state.val_temp += preco; st.rerun()
                
                with st.form("lanca"):
                    vf = st.number_input("Valor Final (R$)", value=st.session_state.val_temp)
                    obs = st.text_input("Observação (opcional):")
                    if st.form_submit_button("✅ CONFIRMAR LANÇAMENTO"):
                        sp_now = get_sp_time()
                        data_br = sp_now.strftime("%d/%m/%Y - %H:%M")
                        new_r = pd.DataFrame([{'ID': sp_now.strftime("%Y%m%d%H%M%S"), 'Cliente': cliente_f, 'Cat_Venda': cat_f, 'Item': obs, 'Valor': vf, 'Data': data_br, 'Tipo': st.session_state.op}])
                        pd.concat([df_v, new_r], ignore_index=True).to_csv(DB_VENDAS, index=False)
                        st.session_state.val_temp = 0.0; del st.session_state.op; st.rerun()
            
            st.divider()
            txt_wa = f"Olá {cliente_f}, seu saldo no Bear Snack Pro é R$ {divida:,.2f}"
            url_wa = f"https://wa.me/{row_cli['Telefone']}?text={txt_wa}"
            st.markdown(f'<a href="{url_wa}" target="_blank" class="wa-btn">📲 NOTIFICAR WHATSAPP</a>', unsafe_allow_html=True)
