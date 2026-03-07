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
    
    /* Centralização Absoluta do Logo no Topo */
    [data-testid="stImage"] {
        display: block;
        margin-left: auto;
        margin-right: auto;
        width: fit-content;
    }
    
    .centered-header {
        text-align: center;
        width: 100%;
        margin-top: -50px; /* Ajuste para subir mais o logo */
        margin-bottom: 20px;
    }

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

DB_VENDAS = "vendas_bear_final.csv"
DB_CLIENTES = "clientes_bear_final.csv"
DB_ANTIGO = "Livro Caixa.db"

# --- 2. FUNÇÕES DE DADOS E MIGRAÇÃO ---
def migrar_dados_antigos():
    if os.path.exists(DB_ANTIGO) and not os.path.exists(DB_CLIENTES):
        try:
            conn = sqlite3.connect(DB_ANTIGO)
            query = "SELECT DISTINCT description FROM cashTransaction WHERE description IS NOT NULL"
            df_bruto = pd.read_sql_query(query, conn)
            conn.close()

            clientes_migrados = []
            for item in df_bruto['description']:
                original = str(item).strip()
                if not original: continue

                if original.startswith('@'):
                    nome = original.replace('@', '').strip()
                    clientes_migrados.append({'Nome': nome, 'Telefone': '', 'Categoria': 'Funcionário', 'Periodo': 'N/A', 'Turma': 'N/A', 'Limite': 100.0})
                else:
                    hora_match = re.search(r'(\d{2}:\d{2})', original)
                    if hora_match:
                        hora = hora_match.group(1)
                        nome = original.replace(hora, '').strip()
                        periodo, turma = "Manhã", "1ª Turma"
                        
                        if hora in ['08:40', '09:00']: periodo, turma = "Manhã", "1ª Turma"
                        elif hora == '09:30': periodo, turma = "Manhã", "2ª Turma"
                        elif hora == '10:00': periodo, turma = "Manhã", "3ª Turma"
                        elif int(hora.split(':')[0]) >= 15: periodo, turma = "Tarde", "1ª Turma"
                        
                        clientes_migrados.append({'Nome': nome, 'Telefone': '', 'Categoria': 'Aluno', 'Periodo': periodo, 'Turma': turma, 'Limite': 50.0})
            
            if clientes_migrados:
                pd.DataFrame(clientes_migrados).to_csv(DB_CLIENTES, index=False, encoding='utf-8-sig')
                return True
        except: return False
    return False

def load_data():
    migrar_dados_antigos()
    if os.path.exists(DB_CLIENTES): c = pd.read_csv(DB_CLIENTES)
    else: c = pd.DataFrame(columns=['Nome', 'Telefone', 'Categoria', 'Periodo', 'Turma', 'Limite'])
    
    if os.path.exists(DB_VENDAS): v = pd.read_csv(DB_VENDAS)
    else: v = pd.DataFrame(columns=['ID', 'Cliente', 'Cat_Venda', 'Item', 'Valor', 'Data', 'Tipo'])
    
    for col in ['Categoria', 'Periodo', 'Turma', 'Limite']:
        if col not in c.columns: c[col] = 50.0 if col == 'Limite' else "N/A"
    return c, v

df_c, df_v = load_data()

# --- 3. LOGIN ---
if 'logado' not in st.session_state: st.session_state.logado = False

if not st.session_state.logado:
    # Topo centralizado no Login
    if os.path.exists("logo.png"): 
        st.image("logo.png", width=200)
    else: 
        st.markdown('<h1 class="centered-header">🐻 BEAR SNACK</h1>', unsafe_allow_html=True)
    
    user = st.text_input("Usuário")
    pw = st.text_input("Senha", type="password")
    if st.button("ACESSAR SISTEMA"):
        if user == "admin" and pw == "bear123":
            st.session_state.logado = True
            st.rerun()
        else: st.error("Dados incorretos")
else:
    # --- 4. SIDEBAR (GESTÃO) ---
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
        t = st.text_input("WhatsApp (DDD+Número)", value=val_t)
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
                df_temp, _ = load_data()
                if editando: df_temp = df_temp[df_temp['Nome'] != cliente_para_editar]
                new_row = pd.DataFrame([{'Nome': n, 'Telefone': t, 'Categoria': cat, 'Periodo': p, 'Turma': tur, 'Limite': lim}])
                pd.concat([df_temp, new_row], ignore_index=True).to_csv(DB_CLIENTES, index=False)
                st.success("Salvo!")
                st.rerun()

    # --- 5. INTERFACE PRINCIPAL ---
    # Topo centralizado no Sistema
    if os.path.exists("logo.png"): 
        st.image("logo.png", width=150)
    else: 
        st.markdown('<h1 class="centered-header">🐻 Bear Snack</h1>', unsafe_allow_html=True)

    aba_selecionada = st.tabs(["🎓 ALUNOS", "💼 FUNCIONÁRIOS", "📊 DEVEDORES"])
    cliente_final, cat_final = None, None

    with aba_selecionada[0]:
        c1, c2 = st.columns(2)
        with c1: pf = st.selectbox("Período:", ["Manhã", "Tarde"], key="fa_p")
        with c2: tf = st.selectbox("Turma:", ["1ª Turma", "2ª Turma", "3ª Turma"], key="fa_t")
        df_fa = df_c[(df_c['Categoria'] == 'Aluno') & (df_c['Periodo'] == pf) & (df_c['Turma'] == tf)]
        sel_a = st.selectbox("Selecione o Aluno:", ["-- Selecionar --"] + sorted(df_fa['Nome'].unique().tolist()), key="sa_a")
        if sel_a != "-- Selecionar --": cliente_final, cat_final = sel_a, "Aluno"
        
    with aba_selecionada[1]:
        sel_f = st.selectbox("Selecione o Funcionário:", ["-- Selecionar --"] + sorted(df_c[df_c['Categoria'] == 'Funcionário']['Nome'].unique().tolist()), key="sf_f")
        if sel_f != "-- Selecionar --": cliente_final, cat_final = sel_f, "Funcionário"

    with aba_selecionada[2]:
        total_a_receber = 0
        devedores = []
        for _, r in df_c.iterrows():
            v_cli = df_v[(df_v['Cliente'] == r['Nome']) & (df_v['Cat_Venda'] == r['Categoria'])]
            saldo = v_cli[v_cli['Tipo'] == 'Compra']['Valor'].sum() - v_cli[v_cli['Tipo'] == 'Pagamento']['Valor'].sum()
            if saldo > 0:
                devedores.append({'Nome': r['Nome'], 'Divida': saldo, 'Cat': r['Categoria']})
                total_a_receber += saldo
        
        st.markdown(f'<div style="background-color:#4E3620; color:#D2B48C; padding:15px; border-radius:15px; text-align:center; margin-bottom:20px;"><small>TOTAL A RECEBER</small><br><b style="font-size:24px;">R$ {total_a_receber:,.2f}</b></div>', unsafe_allow_html=True)
        for d in sorted(devedores, key=lambda x: x['Nome']):
            st.button(f"{d['Nome']} ({d['Cat']}) ➔ R$ {d['Divida']:,.2f}")

    # --- 6. LANÇAMENTOS E PRODUTOS ---
    if cliente_final:
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
            
            produtos = {
                "Água": 4.0, "Biscoito": 4.0, "Fruta": 4.0, "Pipoca": 7.0,
                "Refrigerante": 6.0, "Salgado": 8.0, "Suco": 6.0, "Suco Natural": 7.0
            }
            
            cols = st.columns(2)
            for i, (prod, preco) in enumerate(produtos.items()):
                if cols[i%2].button(f"{prod} (R$ {preco:.2f})", key=f"btn_{prod}"):
                    st.session_state.val_temp += preco
                    st.rerun()

            with st.form("lanca_venda"):
                vf = st.number_input("Valor Final R$", min_value=0.0, value=st.session_state.val_temp)
                desc = st.text_input("Observação", placeholder="Ex: Salgado e Suco")
                c_z, c_s = st.columns(2)
                if c_z.form_submit_button("🧹 LIMPAR"):
                    st.session_state.val_temp = 0.0
                    st.rerun()
                if c_s.form_submit_button("✅ CONFIRMAR"):
                    if vf > 0:
                        _, df_v_up = load_data()
                        nid = datetime.now().strftime("%Y%m%d%H%M%S")
                        agora = datetime.now().strftime("%d/%m - %H:%M")
                        new_row = pd.DataFrame([{'ID': nid, 'Cliente': cliente_final, 'Cat_Venda': cat_final, 'Item': desc, 'Valor': vf, 'Data': agora, 'Tipo': st.session_state.op}])
                        pd.concat([df_v_up, new_row], ignore_index=True).to_csv(DB_VENDAS, index=False)
                        st.session_state.val_temp = 0.0
                        del st.session_state.op
                        st.rerun()

        # --- 7. WHATSAPP E PIX ---
        st.divider()
        if os.path.exists("QRcode.jpeg"):
            st.image("QRcode.jpeg", caption="Pague via PIX", width=200)
            st.code("Chave PIX: (13) 97827-5300", language="text")

        if divida > 0:
            status, cor_z, pix_msg = f"débito de R$ {divida:,.2f}", "#25D366", "\n\nChave PIX: (13) 97827-5300"
        elif divida < 0:
            status, cor_z, pix_msg = f"crédito de R$ {abs(divida):,.2f}", "#075E54", ""
        else:
            status, cor_z, pix_msg = "saldo zerado", "#25D366", ""

        msg = f"Olá {cliente_final}, informamos que você possui um {status} no Bear Snack.{pix_msg}"
        url = f"https://wa.me/{tel}?text={urllib.parse.quote(msg)}"
        st.markdown(f'<a href="{url}" target="_blank" style="text-decoration:none;"><div style="background-color:{cor_z}; color:white; padding:15px; border-radius:15px; text-align:center; font-weight:bold; margin-bottom:20px;">📲 ENVIAR SALDO VIA WHATSAPP</div></a>', unsafe_allow_html=True)

        st.write("### Histórico")
        for i, row in v_c.iloc[::-1].iterrows():
            cor_hist = "#B03020" if row['Tipo'] == "Compra" else "#2e7d32"
            st.markdown(f'<div class="item-card"><div><b>{row["Item"] if str(row["Item"]) != "nan" and row["Item"] != "" else row["Tipo"]}</b><br><small>{row["Data"]}</small></div><b style="color:{cor_hist};">R$ {row["Valor"]:.2f}</b></div>', unsafe_allow_html=True)
            if st.button("🗑️", key=f"del_{row['ID']}"):
                _, df_v_del = load_data()
                df_v_del = df_v_del[df_v_del['ID'] != row['ID']]
                df_v_del.to_csv(DB_VENDAS, index=False)
                st.rerun()












