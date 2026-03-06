import streamlit as st
import pandas as pd
import os
import sqlite3
import re
from datetime import datetime
import urllib.parse

# --- 1. CONFIGURAÇÃO DE PÁGINA E ESTILO ---
st.set_page_config(page_title="Bear Snack Pro", layout="centered", initial_sidebar_state="collapsed")

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

# Nomes dos ficheiros
DB_VENDAS = "vendas_bear_final.csv"
DB_CLIENTES = "clientes_bear_final.csv"
DB_ANTIGO = "Livro Caixa.db"

# --- 2. MOTOR DE MIGRAÇÃO E CARGA DE DADOS ---
def inicializar_sistema():
    # 1. Tentar migrar se o CSV de clientes não existir
    if not os.path.exists(DB_CLIENTES) and os.path.exists(DB_ANTIGO):
        try:
            conn = sqlite3.connect(DB_ANTIGO)
            query = "SELECT DISTINCT description FROM cashTransaction WHERE description IS NOT NULL"
            df_sql = pd.read_sql_query(query, conn)
            conn.close()

            lista_migrada = []
            for item in df_sql['description']:
                txt = str(item).strip()
                if not txt or txt.lower() == 'none': continue

                # Regra: Funcionário (@)
                if txt.startswith('@'):
                    nome = txt.replace('@', '').strip()
                    lista_migrada.append({'Nome': nome, 'Telefone': '', 'Categoria': 'Funcionário', 'Periodo': 'N/A', 'Turma': 'N/A', 'Limite': 100.0})
                
                # Regra: Alunos (Horários)
                else:
                    hora_match = re.search(r'(\d{2}:\d{2})', txt)
                    if hora_match:
                        hora = hora_match.group(1)
                        nome = txt.replace(hora, '').strip()
                        periodo, turma = "Manhã", "1ª Turma"
                        
                        # Lógica de Horários solicitada
                        if hora in ['08:40', '09:00']: periodo, turma = "Manhã", "1ª Turma"
                        elif hora == '09:30': periodo, turma = "Manhã", "2ª Turma"
                        elif hora == '10:00': periodo, turma = "Manhã", "3ª Turma"
                        elif int(hora.split(':')[0]) >= 15: periodo, turma = "Tarde", "1ª Turma"
                        
                        lista_migrada.append({'Nome': nome, 'Telefone': '', 'Categoria': 'Aluno', 'Periodo': periodo, 'Turma': turma, 'Limite': 50.0})
            
            if lista_migrada:
                df_c_novo = pd.DataFrame(lista_migrada).drop_duplicates(subset=['Nome'])
                df_c_novo.to_csv(DB_CLIENTES, index=False, encoding='utf-8-sig')
        except Exception as e:
            st.error(f"Erro na migração: {e}")

    # 2. Carregar DataFrames
    if os.path.exists(DB_CLIENTES):
        df_c = pd.read_csv(DB_CLIENTES)
    else:
        df_c = pd.DataFrame(columns=['Nome', 'Telefone', 'Categoria', 'Periodo', 'Turma', 'Limite'])

    if os.path.exists(DB_VENDAS):
        df_v = pd.read_csv(DB_VENDAS)
    else:
        df_v = pd.DataFrame(columns=['ID', 'Cliente', 'Cat_Venda', 'Item', 'Valor', 'Data', 'Tipo'])

    return df_c, df_v

df_c, df_v = inicializar_sistema()

# --- 3. CONTROLO DE ACESSO ---
if 'logado' not in st.session_state: st.session_state.logado = False

if not st.session_state.logado:
    st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
    if os.path.exists("logo.png"): st.image("logo.png", width=150)
    st.title("🐻 BEAR SNACK LOGIN")
    st.markdown("</div>", unsafe_allow_html=True)
    
    user = st.text_input("Usuário", value="admin")
    pw = st.text_input("Senha", type="password")
    
    if st.button("ENTRAR NO SISTEMA"):
        if user == "admin" and pw == "bear123":
            st.session_state.logado = True
            st.rerun()
        else:
            st.error("Credenciais Inválidas")
    
    # Status dos arquivos para o utilizador verificar
    st.divider()
    col1, col2 = st.columns(2)
    col1.write(f"📁 Banco Antigo: {'✅' if os.path.exists(DB_ANTIGO) else '❌'}")
    col2.write(f"👥 Clientes CSV: {'✅' if os.path.exists(DB_CLIENTES) else '❌'}")
    
    if not os.path.exists(DB_CLIENTES) and os.path.exists(DB_ANTIGO):
        st.info("O Banco de Dados foi detetado. Ele será importado automaticamente ao entrar.")

else:
    # --- 4. INTERFACE PRINCIPAL ---
    st.markdown("<h1 style='text-align:center;'>🐻 Bear Snack Pro</h1>", unsafe_allow_html=True)
    
    aba1, aba2, aba3 = st.tabs(["🎓 ALUNOS", "💼 FUNCIONÁRIOS", "📊 DEVEDORES"])
    cliente_final, cat_final = None, None

    with aba1:
        c1, c2 = st.columns(2)
        with c1: p_sel = st.selectbox("Período", ["Manhã", "Tarde"])
        with c2: t_sel = st.selectbox("Turma", ["1ª Turma", "2ª Turma", "3ª Turma"])
        
        filtro_a = df_c[(df_c['Categoria'] == 'Aluno') & (df_c['Periodo'] == p_sel) & (df_c['Turma'] == t_sel)]
        sel_a = st.selectbox("Selecione o Aluno", ["--"] + sorted(filtro_a['Nome'].unique().tolist()))
        if sel_a != "--": cliente_final, cat_final = sel_a, "Aluno"

    with aba2:
        filtro_f = df_c[df_c['Categoria'] == 'Funcionário']
        sel_f = st.selectbox("Selecione o Funcionário", ["--"] + sorted(filtro_f['Nome'].unique().tolist()))
        if sel_f != "--": cliente_final, cat_final = sel_f, "Funcionário"

    with aba3:
        lista_dev = []
        for _, r in df_c.iterrows():
            v_cli = df_v[(df_v['Cliente'] == r['Nome'])]
            total = v_cli[v_cli['Tipo'] == 'Compra']['Valor'].sum() - v_cli[v_cli['Tipo'] == 'Pagamento']['Valor'].sum()
            if total > 0: lista_dev.append({'n': r['Nome'], 'v': total})
        
        if lista_dev:
            for d in sorted(lista_dev, key=lambda x: x['n']):
                st.warning(f"{d['n']}: R$ {d['v']:.2f}")
        else:
            st.success("Nenhum saldo devedor pendente.")

    # --- 5. ÁREA DE LANÇAMENTO ---
    if cliente_final:
        v_cli = df_v[df_v['Cliente'] == cliente_final]
        saldo = v_cli[v_cli['Tipo'] == 'Compra']['Valor'].sum() - v_cli[v_cli['Tipo'] == 'Pagamento']['Valor'].sum()
        
        st.markdown(f"""<div class="balance-card"><h3>{cliente_final}</h3><h1>R$ {saldo:,.2f}</h1></div>""", unsafe_allow_html=True)

        if 'v_temp' not in st.session_state: st.session_state.v_temp = 0.0
        
        col_btn1, col_btn2 = st.columns(2)
        if col_btn1.button("➕ NOVA COMPRA"): st.session_state.modo = "Compra"
        if col_btn2.button("💵 REGISTRAR PAGAMENTO"): st.session_state.modo = "Pagamento"

        if 'modo' in st.session_state:
            st.subheader(f"Registrar {st.session_state.modo}")
            
            if st.session_state.modo == "Compra":
                prods = {"Salgado": 8.0, "Suco": 6.0, "Refrigerante": 6.0, "Pipoca": 7.0, "Água": 4.0, "Biscoito": 4.0}
                c_p = st.columns(3)
                for i, (p, v) in enumerate(prods.items()):
                    if c_p[i%3].button(f"{p}\nR${v}"):
                        st.session_state.v_temp += v
                        st.rerun()

            with st.form("f_lanca"):
                v_final = st.number_input("Valor", value=st.session_state.v_temp)
                obs = st.text_input("Observação")
                if st.form_submit_button("CONFIRMAR"):
                    nova_v = pd.DataFrame([{
                        'ID': datetime.now().strftime("%Y%m%d%H%M%S"),
                        'Cliente': cliente_final, 'Cat_Venda': cat_final,
                        'Item': obs if obs else st.session_state.modo,
                        'Valor': v_final, 'Data': datetime.now().strftime("%d/%m %H:%M"),
                        'Tipo': st.session_state.modo
                    }])
                    df_v_salvar = pd.concat([df_v, nova_v], ignore_index=True)
                    df_v_salvar.to_csv(DB_VENDAS, index=False)
                    st.session_state.v_temp = 0.0
                    del st.session_state.modo
                    st.rerun()

        # WhatsApp e PIX
        st.divider()
        if os.path.exists("QRcode.jpeg"): st.image("QRcode.jpeg", width=200)
        
        txt_zap = f"Olá {cliente_final}, o seu saldo no Bear Snack é de R$ {saldo:.2f}."
        if saldo > 0: txt_zap += " Chave PIX: (13) 97827-5300"
        
        url_zap = f"https://wa.me/?text={urllib.parse.quote(txt_zap)}"
        st.markdown(f'<a href="{url_zap}" target="_blank"><button style="width:100%; background-color:#25D366; color:white; border:none; padding:10px; border-radius:10px; font-weight:bold;">📲 NOTIFICAR WHATSAPP</button></a>', unsafe_allow_html=True)

    # --- 6. SIDEBAR ADMIN ---
    with st.sidebar:
        st.header("⚙️ Configurações")
        if st.button("SAIR"):
            st.session_state.logado = False
            st.rerun()
        st.divider()
        if st.button("🗑️ APAGAR TUDO E REIMPORTAR DB"):
            if os.path.exists(DB_CLIENTES): os.remove(DB_CLIENTES)
            if os.path.exists(DB_VENDAS): os.remove(DB_VENDAS)
            st.rerun()
