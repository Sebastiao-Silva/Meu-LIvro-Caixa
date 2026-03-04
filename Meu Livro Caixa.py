import streamlit as st
import pandas as pd
import os
from datetime import datetime
import urllib.parse
from PIL import Image

# --- CONFIGURAÇÃO VISUAL TEMÁTICA (Cores de Urso) ---
st.set_page_config(page_title="BEAR SNACK - Gestão", layout="centered")

# Paleta de Cores do Urso
C_URS_BASE = "#D2B48C"    # Marrom Tan (Pele base)
C_URS_MED = "#CD853F"     # Marrom Peru (Focinho/Detalhes)
C_URS_TEXTO = "#4E3620"   # Marrom Escuro (Letras e Contorno)
C_URS_CHAPE = "#B03020"   # Vermelho Tijolo (Chapéu do logo)
C_URS_TEXT_LOGO = "#EEDD88"# Amarelo Dourado (Fundo da letra SNACK)

# Injeção de CSS Avançado para Customização de Interface
st.markdown(f"""
    <style>
    /* Estilo de Fundo do App (Marrom Tan Claríssimo) */
    .stApp {{ background-color: #F8F5F1; }}
    
    /* Título e Texto Geral */
    h1, h2, h3, h4, .stText, p {{ color: {C_URS_TEXTO} !important; font-family: 'Poppins', sans-serif; }}
    
    /* Sidebar (Menu de Configurações) */
    [data-testid="stSidebar"] {{
        background-color: {C_URS_MED} !important;
    }}
    [data-testid="stSidebar"] h2 {{ color: white !important; }}
    [data-testid="stSidebar"] label {{ color: white !important; font-weight: bold; }}
    
    /* Botões Principais (Temáticos de Marrom Escuro) */
    .stButton>button {{
        background-color: {C_URS_TEXTO} !important;
        color: white !important;
        border-radius: 20px;
        border: 2px solid #EEE;
        font-weight: bold;
        transition: 0.3s;
    }}
    .stButton>button:hover {{ background-color: {C_URS_CHAPE} !important; }}
    
    /* Botão Verde do WhatsApp */
    .btn-wa-link button {{
        background-color: #25D366 !important;
        color: white !important;
        border-radius: 20px;
        border: none;
        height: 45px;
        width: 100%;
        cursor: pointer;
        font-weight: bold;
    }}
    .btn-wa-link button:hover {{ background-color: #128C7E !important; }}

    /* Cards de Histórico (Marrom Tan com Destaque Dourado) */
    .card-item {{
        background: {C_URS_BASE};
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 10px;
        border-left: 6px solid {C_URS_MED};
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }}
    .card-item small, .card-item b {{ color: {C_URS_TEXTO} !important; }}

    /* Expander e Inputs */
    .stExpander {{ background: white; border-radius: 12px; }}
    [data-testid="stForm"] {{ border: none; padding: 0; }}
    div[data-baseweb="input"] > div {{
        border-color: {C_URS_MED} !important;
    }}
    
    /* Card de Status de Dívida (Degradê Urso) */
    .status-card-urso {{
        background: linear-gradient(135deg, {C_URS_TEXTO}, {C_URS_MED});
        color: white;
        padding: 25px;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }}
    .status-card-urso h2 {{ color: white !important; font-weight: bold; font-size: 2.8em !important; }}

    /* Navegação por Abas */
    button[data-baseweb="tab"] {{
        background-color: {C_URS_TEXT_LOGO} !important;
        color: {C_URS_TEXTO} !important;
        border-radius: 10px 10px 0 0;
        margin-right: 5px;
    }}
    button[data-baseweb="tab"][aria-selected="true"] {{
        background-color: {C_URS_MED} !important;
        color: white !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- BANCO DE DADOS ---
DB_CLIENTES_URS = "clientes_urso.csv"
DB_VENDAS_URS = "vendas_urso.csv"

def carregar():
    c = pd.read_csv(DB_CLIENTES_URS) if os.path.exists(DB_CLIENTES_URS) else pd.DataFrame(columns=['Nome', 'Telefone', 'Avatar'])
    v = pd.read_csv(DB_VENDAS_URS) if os.path.exists(DB_VENDAS_URS) else pd.DataFrame(columns=['ID', 'Cliente', 'Item', 'Valor', 'Data', 'Tipo'])
    return c, v

df_c, df_v = carregar()

# --- SIDEBAR: CADASTRO TEMÁTICO ---
with st.sidebar:
    st.header("⚙️ Novo Cliente BEAR")
    n_nome_u = st.text_input("Nome do Cliente")
    n_tel_u = st.text_input("WhatsApp (ex: 5511999999999)")
    if st.button("Cadastrar Novo Lançamento"):
        if n_nome_u:
            novo_c_u = pd.concat([df_c, pd.DataFrame([{'Nome': n_nome_u, 'Telefone': n_tel_u, 'Avatar': '🐻'}])], ignore_index=True)
            novo_c_u.to_csv(DB_CLIENTES_URS, index=False)
            st.success("Cliente cadastrado com sucesso!")
            st.rerun()

# --- TELA PRINCIPAL: LOGO E IDENTIDADE ---
col_logo, col_desc = st.columns([0.4, 0.6])
with col_logo:
    # Mostra o logo oficial do "BEAR SNACK" (Ajuste o caminho para 'logo.png' no seu repo)
    if os.path.exists("logo.png"):
        img = Image.open("logo.png")
        st.image(img, use_column_width=True)
    else:
        # Texto de segurança caso o logo não seja encontrado no GitHub
        st.markdown('<h1 style="color:#B03020;">BEAR SNACK</h1>', unsafe_allow_html=True)
with col_desc:
    st.markdown('<p style="margin-top:20px;">Sistema de Gestão de Vendas e Cobranças de Dívidas</p>', unsafe_allow_html=True)

if df_c.empty:
    st.info("🐻 Use a barra lateral para cadastrar seu primeiro cliente do Livro de Fiados.")
else:
    cliente_sel_u = st.selectbox("Selecione o Cliente para Gerenciar Dívida:", ["-- Selecionar --"] + list(df_c['Nome'].unique()))

    if cliente_sel_u != "-- Selecionar --":
        # Dados do cliente
        dados_cliente_u = df_c[df_c['Nome'] == cliente_sel_u].iloc[0]
        vendas_c_u = df_v[df_v['Cliente'] == cliente_sel_u]
        
        # Cálculo de Saldo
        compras_u = vendas_c_u[vendas_c_u['Tipo'] == 'Compra']['Valor'].sum()
        pagamentos_u = vendas_c_u[vendas_c_u['Tipo'] == 'Pagamento']['Valor'].sum()
        saldo_u = compras_u - pagamentos_u

        # Card de Status Temático (Urso)
        st.markdown(f"""<div class="status-card-urso">
            <p style="margin:0; opacity:0.8; font-size:0.9em;">Saldo Devedor Ativo de {cliente_sel_u}</p>
            <h2 style="margin:0;">R$ {saldo_u:,.2f}</h2>
        </div>""", unsafe_allow_html=True)

        # Ações do App
        col_l_u, col_w_u = st.columns(2)
        with col_l_u:
            with st.expander("➕ Inserir Dados de Compra / Pagamento", expanded=True):
                with st.form("add_venda_u", clear_on_submit=True):
                    t_u = st.selectbox("Operação", ["Compra", "Pagamento"])
                    v_u = st.number_input("Valor R$", min_value=0.0, step=0.50)
                    i_u = st.text_input("Descrição (Ex: Pizza Bear, Suco Marrom)")
                    d_u = st.date_input("Data do Registro", datetime.now())
                    if st.form_submit_button("Confirmar Lançamento"):
                        if v_u > 0:
                            novo_id_u = datetime.now().strftime("%Y%m%d%H%M%S")
                            nova_l_u = pd.DataFrame([{'ID': novo_id_u, 'Cliente': cliente_sel_u, 'Item': i_u, 'Valor': v_u, 'Data': d_u.strftime("%d/%m/%Y"), 'Tipo': t_u}])
                            pd.concat([df_v, nova_l_u], ignore_index=True).to_csv(DB_VENDAS_URS, index=False)
                            st.rerun()
        
        with col_w_u:
            # BOTÃO COBRANÇA WHATSAPP (Mensagem customizada do Recibo)
            data_hoje_u = datetime.now().strftime('%d/%m/%y')
            msg_u = f"🐻 Olá {cliente_sel_u}, segue seu extrato do BEAR SNACK:\n*Saldo devedor atual:* R$ {saldo_u:,.2f}\nÚltima atualização: {data_hoje_u}\n(Este é um sistema de cobrança de fiados)."
            link_wa_u = f"https://wa.me/{dados_cliente_u['Telefone']}?text={urllib.parse.quote(msg_u)}"
            st.markdown(f'<a href="{link_wa_u}" target="_blank" class="btn-wa-link"><button>✉️ ENVIAR COBRANÇA</button></a>', unsafe_allow_html=True)

        st.divider()

        # HISTÓRICO TEMÁTICO COM EXCLUSÃO E CAIXA DE SELEÇÃO
        st.subheader(f"📜 Histórico de {cliente_sel_u}")
        
        # Inverter para mostrar os mais recentes primeiro
        for idx_u, row_u in vendas_c_u.iloc[::-1].iterrows():
            with st.container():
                col_info_u, col_del_u = st.columns([0.85, 0.15])
                with col_info_u:
                    # Cores para Compra/Pagamento
                    status_c_u = "card-entrada" if row_u['Tipo'] == "Compra" else "card-saida"
                    cor_v_u = "#B03020" if row_u['Tipo'] == "Compra" else "#2e7d32" # Vermelho Chapéu ou Verde Pagamento
                    
                    st.markdown(f"""<div class="card-item">
                        <div>
                            <small>{row_u['Data']}</small><br>
                            <span style="font-weight: 600; font-size:1.1em; color:#4E3620;">{row_u['Item']}</span>
                        </div>
                        <div style="color:{cor_v_u}; font-weight:bold; font-size:1.2em;">
                            {"➕" if row_u['Tipo'] == "Compra" else "➖"} R$ {row_u['Valor']:,.2f}
                        </span>
                    </div>""", unsafe_allow_html=True)
                with col_del_u:
                    # Botão de Lixeira
                    if st.button("🗑️", key=f"del_{row_u['ID']}"):
                        df_v = df_v[df_v['ID'] != row_u['ID']]
                        df_v.to_csv(DB_VENDAS_URS, index=False)
                        st.rerun()
