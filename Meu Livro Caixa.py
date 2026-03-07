import streamlit as st
import pandas as pd
import os
from datetime import datetime
import urllib.parse
from fpdf import FPDF

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

# --- 2. FUNÇÕES DE DADOS E PDF ---
def load_data():
    c = pd.read_csv(DB_CLIENTES) if os.path.exists(DB_CLIENTES) else pd.DataFrame(columns=['Nome', 'Telefone', 'Categoria', 'Periodo', 'Turma', 'Limite'])
    v = pd.read_csv(DB_VENDAS) if os.path.exists(DB_VENDAS) else pd.DataFrame(columns=['ID', 'Cliente', 'Cat_Venda', 'Item', 'Valor', 'Data', 'Tipo'])
    for col in ['Categoria', 'Periodo', 'Turma', 'Limite']:
        if col not in c.columns: c[col] = 50.0 if col == 'Limite' else "N/A"
    return c, v

def gerar_pdf(titulo, linhas):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    # Tira acentos para evitar erro de encoding no PDF básico
    pdf.cell(190, 10, "Bear Snack Pro - Relatorio", ln=True, align="C")
    pdf.set_font("Arial", "B", 12)
    pdf.cell(190, 10, titulo.encode('latin-1', 'ignore').decode('latin-1'), ln=True, align="C")
    pdf.ln(10)
    pdf.set_font("Arial", size=10)
    for linha in linhas:
        # Limpa caracteres especiais de cada linha
        linha_limpa = linha.encode('latin-1', 'ignore').decode('latin-1')
        pdf.cell(0, 8, linha_limpa, ln=True)
    return pdf.output(dest='S').encode('latin-1')

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

    # --- LOGO TOPO ---
    st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
    if os.path.exists("logo.png"): st.image("logo.png", width=100)
    else: st.title("🐻 Bear Snack")
    st.markdown("</div>", unsafe_allow_html=True)

    # --- 6. TELA HOME ---
    if st.session_state.tela_atual == "home":
        st.markdown("<br>", unsafe_allow_html=True)
        st.write("🔍 **Buscar Cliente (digite o nome):**")
        nome_busca = st.text_input("", placeholder="Digite para buscar...", label_visibility="collapsed").strip()
        if nome_busca:
            matches = df_c[df_c['Nome'].str.contains(nome_busca, case=False, na=False)]
            for _, row in matches.head(3).iterrows():
                if st.button(f"✅ Atender: {row['Nome']} ({row['Categoria']})", key=f"fast_{row['Nome']}"):
                    st.session_state.cliente_selecionado = (row['Nome'], row['Categoria'])
                    st.session_state.tela_atual = "vendas"
                    st.rerun()
        st.divider()
        if st.button("🎓 ALUNOS"): st.session_state.tela_atual = "alunos"; st.rerun()
        if st.button("💼 FUNCIONÁRIOS"): st.session_state.tela_atual = "funcionarios"; st.rerun()
        if st.button("📊 DEVEDORES"): st.session_state.tela_atual = "devedores"; st.rerun()
        if st.button("📄 IMPRIMIR RELATÓRIO"): st.session_state.tela_atual = "relatorios"; st.rerun()

    # --- TELA DE RELATÓRIOS ---
    elif st.session_state.tela_atual == "relatorios":
        st.markdown('<div class="btn-voltar">', unsafe_allow_html=True)
        if st.button("⬅️ VOLTAR AO MENU"): st.session_state.tela_atual = "home"; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.subheader("Gerar Relatório PDF")
        tipo_rel = st.radio("Selecione o tipo:", 
                            ["Relatório Completo", "Devedor Completo", "Todos por Período", "Devedor por Período"])
        
        pdf_bytes = None
        nome_arquivo = "relatorio_bear.pdf"

        if tipo_rel == "Relatório Completo":
            linhas = []
            total = 0
            for _, r in df_c.iterrows():
                v_c = df_v[df_v['Cliente'] == r['Nome']]
                saldo = v_c[v_c['Tipo'] == 'Compra']['Valor'].sum() - v_c[v_c['Tipo'] == 'Pagamento']['Valor'].sum()
                if saldo > 0:
                    linhas.append(f"{r['Nome']} - R$ {saldo:.2f}")
                    total += saldo
            linhas.append("-" * 30)
            linhas.append(f"TOTAL A RECEBER: R$ {total:.2f}")
            pdf_bytes = gerar_pdf("Relatorio de Todos os Devedores", linhas)

        elif tipo_rel == "Devedor Completo":
            escolha = st.selectbox("Selecione o Cliente:", sorted(df_c['Nome'].tolist()))
            v_c = df_v[df_v['Cliente'] == escolha]
            linhas = [f"Cliente: {escolha}", "Historico:"]
            for _, rv in v_c.iterrows():
                linhas.append(f"{rv['Data']} - {rv['Tipo']} - R$ {rv['Valor']:.2f}")
            pdf_bytes = gerar_pdf(f"Extrato: {escolha}", linhas)

        elif tipo_rel == "Todos por Período":
            p_f = st.selectbox("Periodo:", ["Manhã", "Tarde"])
            t_f = st.selectbox("Turma:", ["1ª Turma", "2ª Turma", "3ª Turma"])
            df_filtro = df_c[(df_c['Periodo'] == p_f) & (df_c['Turma'] == t_f)]
            linhas = [f"Periodo: {p_f} / Turma: {t_f}", "---"]
            for _, r in df_filtro.iterrows():
                v_c = df_v[df_v['Cliente'] == r['Nome']]
                saldo = v_c[v_c['Tipo'] == 'Compra']['Valor'].sum() - v_c[v_c['Tipo'] == 'Pagamento']['Valor'].sum()
                if saldo > 0: linhas.append(f"{r['Nome']} - R$ {saldo:.2f}")
            pdf_bytes = gerar_pdf(f"Devedores {p_f} {t_f}", linhas)

        elif tipo_rel == "Devedor por Período":
            escolha = st.selectbox("Selecione o Cliente:", sorted(df_c['Nome'].tolist()))
            d_ini = st.date_input("De:")
            d_fim = st.date_input("Até:")
            v_c = df_v[df_v['Cliente'] == escolha]
            linhas = [f"Cliente: {escolha}", f"Filtro: {d_ini} a {d_fim}", "---"]
            for _, rv in v_c.iterrows():
                linhas.append(f"{rv['Data']} - {rv['Tipo']} - R$ {rv['Valor']:.2f}")
            pdf_bytes = gerar_pdf(f"Periodo: {escolha}", linhas)

        if pdf_bytes:
            st.download_button("📥 BAIXAR RELATORIO", data=pdf_bytes, file_name=nome_arquivo, mime="application/pdf")

    # --- TELAS DE VENDAS E SELEÇÃO (Mantidas da base) ---
    else:
        st.markdown('<div class="btn-voltar">', unsafe_allow_html=True)
        if st.button("⬅️ VOLTAR AO MENU"):
            st.session_state.tela_atual = "home"
            st.session_state.cliente_selecionado = None
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # Lógica de exibição das telas de Alunos, Funcionários e Devedores...
        if st.session_state.tela_atual == "alunos":
            st.subheader("🎓 Área dos Alunos")
            c1, c2 = st.columns(2)
            with c1: pf = st.selectbox("Período:", ["Manhã", "Tarde"])
            with c2: tf = st.selectbox("Turma:", ["1ª Turma", "2ª Turma", "3ª Turma"])
            df_fa = df_c[(df_c['Categoria'] == 'Aluno') & (df_c['Periodo'] == pf) & (df_c['Turma'] == tf)]
            sel_a = st.selectbox("Selecione:", ["-- Selecionar --"] + sorted(df_fa['Nome'].unique().tolist()))
            if sel_a != "-- Selecionar --": st.session_state.cliente_selecionado = (sel_a, "Aluno")

        elif st.session_state.tela_atual == "funcionarios":
            st.subheader("💼 Área dos Funcionários")
            sel_f = st.selectbox("Selecione:", ["-- Selecionar --"] + sorted(df_c[df_c['Categoria'] == 'Funcionário']['Nome'].unique().tolist()))
            if sel_f != "-- Selecionar --": st.session_state.cliente_selecionado = (sel_f, "Funcionário")

        elif st.session_state.tela_atual == "devedores":
            st.subheader("📊 Devedores")
            for _, r in df_c.iterrows():
                v_cli = df_v[df_v['Cliente'] == r['Nome']]
                saldo = v_cli[v_cli['Tipo'] == 'Compra']['Valor'].sum() - v_cli[v_cli['Tipo'] == 'Pagamento']['Valor'].sum()
                if saldo > 0:
                    if st.button(f"{r['Nome']} - R$ {saldo:.2f}", key=f"dev_{r['Nome']}"):
                        st.session_state.cliente_selecionado = (r['Nome'], r['Categoria'])
                        st.rerun()

        # --- ÁREA DE VENDAS ---
        if st.session_state.cliente_selecionado:
            cliente_final, cat_final = st.session_state.cliente_selecionado
            v_c = df_v[(df_v['Cliente'] == cliente_final)]
            divida = v_c[v_c['Tipo'] == 'Compra']['Valor'].sum() - v_c[v_c['Tipo'] == 'Pagamento']['Valor'].sum()
            st.markdown(f'<div class="balance-card"><h2>{cliente_final}</h2><h1>R$ {divida:,.2f}</h1></div>', unsafe_allow_html=True)
            
            c1, c2 = st.columns(2)
            if c1.button("➕ COMPRA"): st.session_state.op = "Compra"
            if c2.button("💵 PAGOU"): st.session_state.op = "Pagamento"

            if 'op' in st.session_state:
                if 'val_temp' not in st.session_state: st.session_state.val_temp = 0.0
                produtos = {"Água": 4.0, "Salgado": 8.0, "Suco": 6.0, "Pipoca": 7.0}
                cols = st.columns(2)
                for i, (p_nome, p_val) in enumerate(produtos.items()):
                    if cols[i%2].button(f"{p_nome} R${p_val}"): st.session_state.val_temp += p_val; st.rerun()
                
                with st.form("f_venda"):
                    vf = st.number_input("Valor Final", value=st.session_state.val_temp)
                    if st.form_submit_button("✅ CONFIRMAR"):
                        new_row = pd.DataFrame([{'ID': datetime.now().strftime("%Y%m%d%H%M%S"), 'Cliente': cliente_final, 'Cat_Venda': cat_final, 'Item': '', 'Valor': vf, 'Data': datetime.now().strftime("%d/%m - %H:%M"), 'Tipo': st.session_state.op}])
                        pd.concat([df_v, new_row], ignore_index=True).to_csv(DB_VENDAS, index=False)
                        st.session_state.val_temp = 0.0
                        del st.session_state.op
                        st.rerun()
