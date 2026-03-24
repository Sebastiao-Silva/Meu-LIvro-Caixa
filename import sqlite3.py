import customtkinter as ctk
import sqlite3
from datetime import datetime, timedelta
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import os

# BIBLIOTECAS PARA PDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

# ==========================================
# CONFIGURAÇÕES DE INTERFACE
# ==========================================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ==========================================
# 1. BANCO DE DADOS (ESTRUTURA COMPLETA)
# ==========================================
def iniciar_banco():
    conn = sqlite3.connect('Livro Caixa.db')
    cursor = conn.cursor()
    
    # Tabela principal de vendas e movimentações
    cursor.execute('''CREATE TABLE IF NOT EXISTS vendas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data_ms INTEGER,
        total REAL,
        metodo TEXT,
        sub_metodo TEXT,
        pago REAL,
        troco REAL,
        descricao_resumo TEXT,
        cliente_id INTEGER
    )''')
    
    # Detalhamento dos itens de cada venda
    cursor.execute('''CREATE TABLE IF NOT EXISTS itens_venda (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        venda_id INTEGER,
        descricao TEXT,
        valor REAL,
        cliente_id INTEGER,
        data_ms INTEGER,
        FOREIGN KEY(venda_id) REFERENCES vendas(id)
    )''')

    # Cadastro de clientes (Caderneta)
    cursor.execute('''CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        perfil TEXT, 
        contato TEXT,
        limite REAL DEFAULT 0.0,
        saldo_devedor REAL DEFAULT 0.0
    )''')

    # Verificação de colunas para compatibilidade
    for col, tipo in [("sub_metodo", "TEXT"), ("cliente_id", "INTEGER"), ("pago", "REAL"), ("troco", "REAL")]:
        try: cursor.execute(f"ALTER TABLE vendas ADD COLUMN {col} {tipo}")
        except: pass
        
    for col, tipo in [("perfil", "TEXT"), ("contato", "TEXT"), ("limite", "REAL"), ("saldo_devedor", "REAL")]:
        try: cursor.execute(f"ALTER TABLE clientes ADD COLUMN {col} {tipo}")
        except: pass

    try: cursor.execute("ALTER TABLE itens_venda ADD COLUMN cliente_id INTEGER")
    except: pass
    try: cursor.execute("ALTER TABLE itens_venda ADD COLUMN data_ms INTEGER")
    except: pass

    conn.commit()
    conn.close()

iniciar_banco()

# ==========================================
# 2. MÓDULO: PROTETOR DE TELA (LOGO)
# ==========================================
class ProtetorTela(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.attributes("-fullscreen", True)
        self.configure(fg_color="white")
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.grab_set()

        try:
            img_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")
            self.img_logo = ctk.CTkImage(light_image=Image.open(img_path),
                                         dark_image=Image.open(img_path),
                                         size=(500, 500))
            self.l_logo = ctk.CTkLabel(self, image=self.img_logo, text="")
            self.l_logo.place(relx=0.5, rely=0.5, anchor="center")
        except:
            self.l_logo = ctk.CTkLabel(self, text="BEAR SNACK", font=("Roboto", 40, "bold"), text_color="black")
            self.l_logo.place(relx=0.5, rely=0.5, anchor="center")

        self.bind("<Any-KeyPress>", lambda e: self.fechar())
        self.bind("<Motion>", lambda e: self.fechar())
        self.bind("<Button-1>", lambda e: self.fechar())

    def fechar(self):
        self.destroy()

# ==========================================
# 3. MÓDULO: EXTRATO INDIVIDUAL
# ==========================================
class JanelaExtratoCliente(ctk.CTkToplevel):
    def __init__(self, parent, cliente_id, nome_cliente):
        super().__init__(parent)
        self.cliente_id = cliente_id
        self.title(f"Extrato: {nome_cliente}")
        self.geometry("700x600")
        self.grab_set()

        f_filtro = ctk.CTkFrame(self)
        f_filtro.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(f_filtro, text="Filtrar Período:").pack(side="left", padx=10)
        self.dias_filtro = ctk.CTkComboBox(f_filtro, values=["Hoje", "7 dias", "15 dias", "30 dias", "Tudo"], command=self.carregar_extrato)
        self.dias_filtro.set("30 dias")
        self.dias_filtro.pack(side="left", padx=10)

        self.tree = ttk.Treeview(self, columns=("DATA", "PROD", "VALOR"), show="headings")
        self.tree.heading("DATA", text="DATA/HORA")
        self.tree.heading("PROD", text="ITEM / OPERAÇÃO")
        self.tree.heading("VALOR", text="VALOR")
        self.tree.column("DATA", width=150)
        self.tree.column("PROD", width=350)
        self.tree.pack(fill="both", expand=True, padx=20, pady=10)

        self.l_resumo = ctk.CTkLabel(self, text="Total no Período: R$ 0,00", font=("Roboto", 18, "bold"))
        self.l_resumo.pack(pady=10)
        self.carregar_extrato()

    def carregar_extrato(self, _=None):
        for i in self.tree.get_children(): self.tree.delete(i)
        filtro = self.dias_filtro.get()
        limite_ms = 0
        agora = datetime.now()

        if filtro == "Hoje": limite_ms = agora.replace(hour=0, minute=0, second=0).timestamp() * 1000
        elif filtro == "7 dias": limite_ms = (agora - timedelta(days=7)).timestamp() * 1000
        elif filtro == "15 dias": limite_ms = (agora - timedelta(days=15)).timestamp() * 1000
        elif filtro == "30 dias": limite_ms = (agora - timedelta(days=30)).timestamp() * 1000
        
        total_p = 0
        with sqlite3.connect('Livro Caixa.db') as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT data_ms, descricao, valor FROM itens_venda 
                WHERE cliente_id = ? AND data_ms >= ?
                UNION ALL
                SELECT data_ms, descricao_resumo, -total FROM vendas 
                WHERE cliente_id = ? AND metodo = 'RECEB. FIADO' AND data_ms >= ?
                ORDER BY data_ms DESC
            """, (self.cliente_id, limite_ms, self.cliente_id, limite_ms))
            
            for r in cur.fetchall():
                dt = datetime.fromtimestamp(r[0]/1000).strftime('%d/%m/%Y %H:%M')
                val_limpo = float(r[2])
                self.tree.insert("", "end", values=(dt, r[1], f"R$ {val_limpo:.2f}"))
                total_p += val_limpo
        self.l_resumo.configure(text=f"Total no Período: R$ {total_p:.2f}")

# ==========================================
# 4. MÓDULO: CADERNETA (F2)
# ==========================================
class JanelaCaderneta(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Caderneta Digital")
        self.geometry("1100x650")
        self.grab_set()
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.id_selecionado = None 

        f_esq = ctk.CTkFrame(self, width=320)
        f_esq.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        ctk.CTkLabel(f_esq, text="DADOS DO CLIENTE", font=("Roboto", 18, "bold")).pack(pady=15)
        self.e_nome = ctk.CTkEntry(f_esq, placeholder_text="Nome Completo")
        self.e_nome.pack(pady=5, padx=20, fill="x")
        self.perfil = ctk.CTkSegmentedButton(f_esq, values=["ALUNO", "FUNCIONÁRIO", "CLIENTE"])
        self.perfil.pack(pady=10, padx=20, fill="x")
        self.perfil.set("ALUNO")
        
        self.e_cont = ctk.CTkEntry(f_esq, placeholder_text="Contato/Matrícula")
        self.e_cont.pack(pady=5, padx=20, fill="x")
        self.e_lim = ctk.CTkEntry(f_esq, placeholder_text="Limite de Crédito")
        self.e_lim.pack(pady=5, padx=20, fill="x")
        
        ctk.CTkButton(f_esq, text="SALVAR / ALTERAR", fg_color="#27ae60", command=self.salvar).pack(pady=10, padx=20, fill="x")
        ctk.CTkButton(f_esq, text="LIMPAR / NOVO", fg_color="#7f8c8d", command=self.limpar_campos).pack(pady=5, padx=20, fill="x")

        ctk.CTkLabel(f_esq, text="FINANCEIRO", font=("Roboto", 16, "bold")).pack(pady=(30, 5))
        self.e_pago = ctk.CTkEntry(f_esq, placeholder_text="Valor Pago R$")
        self.e_pago.pack(pady=5, padx=20, fill="x")
        ctk.CTkButton(f_esq, text="BAIXAR DÍVIDA", fg_color="#2980b9", command=self.quitar_debito).pack(pady=5, padx=20, fill="x")
        ctk.CTkButton(f_esq, text="VER EXTRATO", fg_color="#8e44ad", command=self.abrir_extrato).pack(pady=5, padx=20, fill="x")
        ctk.CTkButton(f_esq, text="GERAR PDF / COMPROVANTE", fg_color="#d35400", command=self.gerar_pdf_cliente).pack(pady=5, padx=20, fill="x")

        f_list = ctk.CTkFrame(self)
        f_list.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.tree = ttk.Treeview(f_list, columns=("ID", "NOME", "PERFIL", "DIVIDA"), show="headings")
        self.tree.heading("ID", text="ID"); self.tree.heading("NOME", text="NOME")
        self.tree.heading("PERFIL", text="PERFIL"); self.tree.heading("DIVIDA", text="DÍVIDA")
        self.tree.column("ID", width=50); self.tree.column("NOME", width=250)
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.tree.bind("<<TreeviewSelect>>", self.carregar_para_edicao)
        self.tree.bind("<Double-1>", lambda e: self.abrir_extrato())
        self.atualizar()

    def gerar_pdf_cliente(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione um cliente na lista primeiro!")
            return
        
        item = self.tree.item(sel)['values']
        c_id, nome, perfil, divida = item[0], item[1], item[2], item[3]
        data_atual = datetime.now().strftime("%d/%m/%Y %H:%M")
        nome_arquivo = f"Comprovante_{nome.replace(' ', '_')}.pdf"

        try:
            pdf = canvas.Canvas(nome_arquivo, pagesize=A4)
            largura, altura = A4

            try:
                pdf.drawInlineImage("LOGO4K.png", largura - 160, altura - 130, width=120, height=120)
            except: pass 

            pdf.setFont("Helvetica-Bold", 16)
            pdf.drawString(50, altura - 50, "BEAR SNACK - COMPROVANTE DE DÉBITO")
            pdf.setFont("Helvetica", 10)
            pdf.drawString(50, altura - 65, f"Gerado em: {data_atual}")
            pdf.line(50, altura - 75, 550, altura - 75)

            pdf.setFont("Helvetica-Bold", 12)
            pdf.drawString(50, altura - 110, f"CLIENTE: {nome}")
            pdf.setFont("Helvetica", 12)
            pdf.drawString(50, altura - 130, f"PERFIL: {perfil}")
            pdf.drawString(50, altura - 150, f"CONTATO: {self.e_cont.get()}")
            
            pdf.setFont("Helvetica-Bold", 14)
            pdf.setFillColorRGB(0.7, 0, 0) 
            pdf.drawString(50, altura - 190, f"VALOR TOTAL EM ABERTO: {divida}")
            
            try:
                pdf.drawInlineImage("QRcode.jpeg", largura - 180, altura - 350, width=130, height=150)
                pdf.setFillColorRGB(0, 0, 0)
                pdf.setFont("Helvetica", 9)
                pdf.drawCentredString(largura - 115, altura - 365, "Escaneie para pagar")
            except:
                pdf.setFillColorRGB(0, 0, 0)

            pdf.setFont("Helvetica-Oblique", 10)
            pdf.drawString(50, altura - 380, "Este documento serve apenas para simples conferência de débitos.")
            pdf.drawString(50, altura - 395, "Favor comparecer ao caixa para regularização.")
            pdf.line(50, altura - 410, 550, altura - 410)

            pdf.save()
            messagebox.showinfo("Sucesso", f"PDF gerado com sucesso!\nArquivo: {nome_arquivo}")
            os.startfile(nome_arquivo) 
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível gerar o PDF: {e}")

    def abrir_extrato(self):
        sel = self.tree.selection()
        if sel:
            item = self.tree.item(sel)['values']
            JanelaExtratoCliente(self, item[0], item[1])

    def carregar_para_edicao(self, e):
        sel = self.tree.selection()
        if sel:
            item_id = self.tree.item(sel)['values'][0]
            self.id_selecionado = item_id
            with sqlite3.connect('Livro Caixa.db') as conn:
                cur = conn.cursor()
                cur.execute("SELECT nome, perfil, contato, limite FROM clientes WHERE id = ?", (self.id_selecionado,))
                res = cur.fetchone()
                if res:
                    self.limpar_campos(apenas_texto=True)
                    self.e_nome.insert(0, res[0]); self.perfil.set(res[1])
                    self.e_cont.insert(0, res[2] if res[2] else ""); self.e_lim.insert(0, str(res[3]))

    def limpar_campos(self, apenas_texto=False):
        self.e_nome.delete(0, 'end'); self.e_cont.delete(0, 'end')
        self.e_lim.delete(0, 'end'); self.e_pago.delete(0, 'end')
        if not apenas_texto:
            self.id_selecionado = None
            if self.tree.selection(): self.tree.selection_remove(self.tree.selection())

    def salvar(self):
        try:
            nome = self.e_nome.get().upper()
            lim = float(self.e_lim.get().replace(",", ".") or 0)
            contato, perfil = self.e_cont.get(), self.perfil.get()
            if not nome: return
            with sqlite3.connect('Livro Caixa.db') as conn:
                cur = conn.cursor()
                if self.id_selecionado:
                    cur.execute("UPDATE clientes SET nome=?, perfil=?, contato=?, limite=? WHERE id=?", (nome, perfil, contato, lim, self.id_selecionado))
                else:
                    cur.execute("INSERT INTO clientes (nome, perfil, contato, limite) VALUES (?,?,?,?)", (nome, perfil, contato, lim))
            self.atualizar(); self.limpar_campos()
        except: messagebox.showerror("Erro", "Dados inválidos.")

    def quitar_debito(self):
        sel = self.tree.selection()
        if not sel: return
        try:
            v_pago = float(self.e_pago.get().replace(",", "."))
            c_id = self.tree.item(sel)['values'][0]
            nome = self.tree.item(sel)['values'][1]
            with sqlite3.connect('Livro Caixa.db') as conn:
                cur = conn.cursor()
                cur.execute("UPDATE clientes SET saldo_devedor = saldo_devedor - ? WHERE id = ?", (v_pago, c_id))
                cur.execute("INSERT INTO vendas (data_ms, total, metodo, descricao_resumo, cliente_id) VALUES (?,?,?,?,?)",
                            (int(datetime.now().timestamp()*1000), v_pago, "RECEB. FIADO", f"PAGAMENTO DE {nome}", c_id))
            self.atualizar(); self.e_pago.delete(0, 'end')
            messagebox.showinfo("Sucesso", "Pagamento registrado!")
        except: pass

    def atualizar(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        with sqlite3.connect('Livro Caixa.db') as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, nome, perfil, saldo_devedor FROM clientes ORDER BY nome")
            for r in cur.fetchall(): self.tree.insert("", "end", values=(r[0], r[1], r[2], f"R$ {float(r[3]):.2f}"))

# ==========================================
# 5. MÓDULO: VENDAS PDV (F1)
# ==========================================
class JanelaCarrinho(ctk.CTkToplevel):
    precos_conhecidos = {}

    def __init__(self, parent, callback):
        super().__init__(parent)
        self.callback = callback
        self.itens = []
        self.cliente_id = None
        self.attributes("-fullscreen", True)
        self.grab_set()
        self.grid_columnconfigure(0, weight=1); self.grid_columnconfigure(1, weight=1); self.grid_rowconfigure(0, weight=1)

        f_e = ctk.CTkFrame(self, fg_color="#1a1a1a")
        f_e.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        ctk.CTkLabel(f_e, text="NOVA VENDA", font=("Roboto", 30, "bold")).pack(pady=20)
        self.e_desc = ctk.CTkEntry(f_e, placeholder_text="PRODUTO / DESCRIÇÃO", height=50, font=("Roboto", 16))
        self.e_desc.pack(fill="x", padx=40, pady=5); self.e_desc.focus()
        self.e_desc.bind("<KeyRelease>", self.verificar_preco)
        
        self.e_val = ctk.CTkEntry(f_e, placeholder_text="PREÇO R$", height=50, font=("Roboto", 16))
        self.e_val.pack(fill="x", padx=40, pady=5)
        
        f_btns = ctk.CTkFrame(f_e, fg_color="transparent")
        f_btns.pack(pady=15)
        ctk.CTkButton(f_btns, text="ADICIONAR\n(F1)", command=self.add_item, width=130, height=60, fg_color="#2980b9").pack(side="left", padx=5)
        ctk.CTkButton(f_btns, text="LIMPAR\n(F2)", command=self.limpar_venda, width=130, height=60, fg_color="#7f8c8d").pack(side="left", padx=5)
        ctk.CTkButton(f_btns, text="FINALIZAR\n(F10)", command=self.finalizar, width=130, height=60, fg_color="#27ae60").pack(side="left", padx=5)

        ctk.CTkLabel(f_e, text="FORMA DE PAGAMENTO:", font=("Roboto", 14)).pack(pady=(20, 5))
        self.metodo = ctk.CTkSegmentedButton(f_e, values=["DINHEIRO", "CARTÃO", "PIX", "FIADO"], command=self.mudar_pagamento)
        self.metodo.pack(pady=10, padx=40, fill="x"); self.metodo.set("DINHEIRO")

        self.f_cartao = ctk.CTkFrame(f_e, fg_color="transparent")
        self.sub_cartao = ctk.CTkSegmentedButton(self.f_cartao, values=["DÉBITO", "CRÉDITO"])
        self.sub_cartao.pack(fill="x", padx=40); self.sub_cartao.set("DÉBITO")

        self.f_fiado = ctk.CTkFrame(f_e, fg_color="transparent")
        self.e_busca = ctk.CTkEntry(self.f_fiado, placeholder_text="🔎 Buscar Cliente..."); self.e_busca.pack(fill="x", padx=40, pady=5)
        self.e_busca.bind("<KeyRelease>", self.buscar_cli)
        self.tree_cli = ttk.Treeview(self.f_fiado, columns=("ID", "NOME", "PERFIL"), show="headings", height=4)
        self.tree_cli.heading("ID", text="ID"); self.tree_cli.heading("NOME", text="NOME"); self.tree_cli.heading("PERFIL", text="PERFIL")
        self.tree_cli.column("ID", width=40); self.tree_cli.pack(fill="x", padx=40); self.tree_cli.bind("<<TreeviewSelect>>", self.selecionar_cli)

        self.f_troco = ctk.CTkFrame(f_e, fg_color="transparent")
        self.e_pago = ctk.CTkEntry(self.f_troco, placeholder_text="VALOR RECEBIDO", height=40); self.e_pago.pack(pady=5)
        self.e_pago.bind("<KeyRelease>", self.calc_troco)
        self.l_troco = ctk.CTkLabel(self.f_troco, text="TROCO: R$ 0,00", font=("Roboto", 22, "bold"), text_color="#f1c40f"); self.l_troco.pack()
        self.f_troco.pack()

        f_d = ctk.CTkFrame(self); f_d.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.tree_v = ttk.Treeview(f_d, columns=("D", "V"), show="headings")
        self.tree_v.heading("D", text="PRODUTO"); self.tree_v.heading("V", text="VALOR")
        self.tree_v.pack(fill="both", expand=True, padx=20, pady=20)
        self.l_total = ctk.CTkLabel(f_d, text="TOTAL: R$ 0,00", font=("Roboto", 60, "bold"), text_color="#2ecc71"); self.l_total.pack(pady=20)
        ctk.CTkButton(f_d, text="SAIR (ESC)", fg_color="#c0392b", command=self.destroy, height=45).pack(pady=10)

        self.bind("<F1>", lambda e: self.add_item())
        self.bind("<F2>", lambda e: self.limpar_venda())
        self.bind("<F10>", lambda e: self.finalizar())
        self.bind("<Escape>", lambda e: self.destroy())

    def verificar_preco(self, e):
        nome = self.e_desc.get().upper().strip()
        if nome in JanelaCarrinho.precos_conhecidos:
            preco = JanelaCarrinho.precos_conhecidos[nome]
            self.e_val.delete(0, 'end'); self.e_val.insert(0, f"{preco:.2f}".replace(".", ","))

    def limpar_venda(self, e=None):
        self.itens = []
        for i in self.tree_v.get_children(): self.tree_v.delete(i)
        self.l_total.configure(text="TOTAL: R$ 0,00")
        self.e_desc.delete(0, 'end'); self.e_val.delete(0, 'end'); self.e_pago.delete(0, 'end')
        self.l_troco.configure(text="TROCO: R$ 0,00")
        self.cliente_id = None; self.e_busca.delete(0, 'end')
        self.e_desc.focus()

    def mudar_pagamento(self, v):
        self.f_cartao.pack_forget(); self.f_fiado.pack_forget(); self.f_troco.pack_forget()
        if v == "CARTÃO": self.f_cartao.pack(fill="x")
        elif v == "FIADO": self.f_fiado.pack(fill="x")
        elif v == "DINHEIRO": self.f_troco.pack(fill="x")

    def buscar_cli(self, e):
        termo = f"%{self.e_busca.get().upper()}%"
        for i in self.tree_cli.get_children(): self.tree_cli.delete(i)
        with sqlite3.connect('Livro Caixa.db') as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, nome, perfil FROM clientes WHERE nome LIKE ? LIMIT 5", (termo,))
            for r in cur.fetchall(): self.tree_cli.insert("", "end", values=r)

    def selecionar_cli(self, e):
        sel = self.tree_cli.selection()
        if sel:
            r = self.tree_cli.item(sel)['values']
            self.cliente_id = r[0]; self.e_busca.delete(0, 'end'); self.e_busca.insert(0, f"PAGADOR: {r[1]}")

    def add_item(self):
        try:
            v = float(self.e_val.get().replace(",", ".")); d = self.e_desc.get().upper().strip() or "ITEM"
            JanelaCarrinho.precos_conhecidos[d] = v
            self.itens.append((d, v)); self.tree_v.insert("", "end", values=(d, f"R$ {v:.2f}"))
            self.l_total.configure(text=f"TOTAL: R$ {sum(i[1] for i in self.itens):.2f}")
            self.e_desc.delete(0, 'end'); self.e_val.delete(0, 'end'); self.e_desc.focus()
        except: pass

    def calc_troco(self, e):
        try: 
            total_atual = sum(i[1] for i in self.itens) or float(self.e_val.get().replace(",", "."))
            self.l_troco.configure(text=f"TROCO: R$ {float(self.e_pago.get().replace(',','.')) - total_atual:.2f}")
        except: pass

    def finalizar(self):
        if not self.itens:
            try: 
                v_d = float(self.e_val.get().replace(",", ".")); d_d = self.e_desc.get().upper().strip() or "VENDA"
                self.itens.append((d_d, v_d))
            except: return
        met = self.metodo.get(); sub = self.sub_cartao.get() if met == "CARTÃO" else ""
        if met == "FIADO" and not self.cliente_id: return
        tot = sum(i[1] for i in self.itens); res = ", ".join([i[0] for i in self.itens]); now = int(datetime.now().timestamp()*1000)
        with sqlite3.connect('Livro Caixa.db') as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO vendas (data_ms, total, metodo, sub_metodo, descricao_resumo, cliente_id) VALUES (?,?,?,?,?,?)", (now, tot, met, sub, res, self.cliente_id))
            v_id = cur.lastrowid
            if met == "FIADO": cur.execute("UPDATE clientes SET saldo_devedor = saldo_devedor + ? WHERE id = ?", (tot, self.cliente_id))
            for d, v in self.itens: cur.execute("INSERT INTO itens_venda (venda_id, descricao, valor, cliente_id, data_ms) VALUES (?,?,?,?,?)", (v_id, d, v, self.cliente_id, now))
        self.callback(); self.destroy()

# ==========================================
# 6. MÓDULO: SANGRIA / SUPRIMENTO (F7)
# ==========================================
class JanelaMovimentacao(ctk.CTkToplevel):
    def __init__(self, parent, callback):
        super().__init__(parent); self.callback = callback; self.title("Movimentação"); self.geometry("350x450"); self.grab_set()
        ctk.CTkLabel(self, text="ENTRADA / SAÍDA", font=("Roboto", 18, "bold")).pack(pady=20)
        self.tipo = ctk.CTkSegmentedButton(self, values=["SANGRIA", "SUPRIMENTO"])
        self.tipo.pack(pady=10, padx=20, fill="x"); self.tipo.set("SANGRIA")
        self.e_val = ctk.CTkEntry(self, placeholder_text="Valor R$"); self.e_val.pack(pady=10, padx=30, fill="x")
        self.e_mot = ctk.CTkEntry(self, placeholder_text="Motivo"); self.e_mot.pack(pady=10, padx=30, fill="x")
        ctk.CTkButton(self, text="CONFIRMAR", fg_color="#e74c3c", command=self.salvar).pack(pady=20, padx=30, fill="x")

    def salvar(self):
        try:
            val = float(self.e_val.get().replace(",", "."))
            if self.tipo.get() == "SANGRIA": val = -val
            with sqlite3.connect('Livro Caixa.db') as conn:
                cur = conn.cursor()
                cur.execute("INSERT INTO vendas (data_ms, total, metodo, descricao_resumo) VALUES (?,?,?,?)",
                            (int(datetime.now().timestamp()*1000), val, "MOV. CAIXA", self.e_mot.get().upper()))
            self.callback(); self.destroy()
        except: pass

# ==========================================
# MÓDULO DE EXCLUSÃO
# ==========================================
class JanelaDetalhesExclusao(ctk.CTkToplevel):
    def __init__(self, parent, venda_id, callback_atualizar):
        super().__init__(parent)
        self.v_id = venda_id
        self.callback = callback_atualizar
        self.title(f"Gerenciar Itens da Venda #{venda_id}")
        self.geometry("600x500")
        self.grab_set()
        
        ctk.CTkLabel(self, text="Selecione os itens que deseja excluir:", font=("Roboto", 14, "bold")).pack(pady=10)
        
        self.tree = ttk.Treeview(self, columns=("ID", "DESC", "VAL"), show="headings")
        self.tree.heading("ID", text="ID"); self.tree.heading("DESC", text="PRODUTO"); self.tree.heading("VAL", text="VALOR")
        self.tree.column("ID", width=50); self.tree.column("DESC", width=350)
        self.tree.pack(fill="both", expand=True, padx=20, pady=10)
        
        f_b = ctk.CTkFrame(self, fg_color="transparent")
        f_b.pack(pady=20)
        
        ctk.CTkButton(f_b, text="EXCLUIR SELECIONADOS", fg_color="#e67e22", command=self.excluir_itens).pack(side="left", padx=10)
        ctk.CTkButton(f_b, text="EXCLUIR VENDA COMPLETA", fg_color="#c0392b", command=self.excluir_total).pack(side="left", padx=10)
        
        self.carregar_itens()

    def carregar_itens(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        with sqlite3.connect('Livro Caixa.db') as conn:
            res = conn.cursor().execute("SELECT id, descricao, valor FROM itens_venda WHERE venda_id = ?", (self.v_id,)).fetchall()
            for r in res: self.tree.insert("", "end", values=(r[0], r[1], f"{float(r[2]):.2f}"))

    def excluir_itens(self):
        selecionados = self.tree.selection()
        if not selecionados: return
        
        if messagebox.askyesno("Confirmar", "Remover itens selecionados da venda?"):
            try:
                with sqlite3.connect('Livro Caixa.db') as conn:
                    cur = conn.cursor()
                    for sel in selecionados:
                        item_info = self.tree.item(sel)['values']
                        i_id = item_info[0]
                        i_val = float(str(item_info[2]).replace("R$", "").replace(",", ".").strip())
                        
                        cur.execute("SELECT total, cliente_id, metodo FROM vendas WHERE id = ?", (self.v_id,))
                        v = cur.fetchone()
                        if v:
                            v_total = float(v[0])
                            novo_total = v_total - i_val
                            cur.execute("UPDATE vendas SET total = ? WHERE id = ?", (novo_total, self.v_id))
                            if v[2] == "FIADO" and v[1]:
                                cur.execute("UPDATE clientes SET saldo_devedor = saldo_devedor - ? WHERE id = ?", (i_val, v[1]))
                        
                        cur.execute("DELETE FROM itens_venda WHERE id = ?", (i_id,))
                    
                    cur.execute("SELECT descricao FROM itens_venda WHERE venda_id = ?", (self.v_id,))
                    restantes = [r[0] for r in cur.fetchall()]
                    novo_resumo = ", ".join(restantes)
                    cur.execute("UPDATE vendas SET descricao_resumo = ? WHERE id = ?", (novo_resumo, self.v_id))
                    
                    conn.commit()
                
                self.carregar_itens()
                self.callback()
                messagebox.showinfo("Sucesso", "Itens excluídos!")
            except Exception as e:
                messagebox.showerror("Erro de Cálculo", f"Erro: {e}")

    def excluir_total(self):
        if messagebox.askyesno("Confirmar", "Excluir toda a venda e seus itens?"):
            try:
                with sqlite3.connect('Livro Caixa.db') as conn:
                    cur = conn.cursor()
                    cur.execute("SELECT total, cliente_id, metodo FROM vendas WHERE id = ?", (self.v_id,))
                    v = cur.fetchone()
                    if v:
                        v_total = float(v[0])
                        if v[2] == "FIADO" and v[1]:
                            cur.execute("UPDATE clientes SET saldo_devedor = saldo_devedor - ? WHERE id = ?", (v_total, v[1]))
                    
                    cur.execute("DELETE FROM itens_venda WHERE venda_id = ?", (self.v_id,))
                    cur.execute("DELETE FROM vendas WHERE id = ?", (self.v_id,))
                    conn.commit()
                
                self.callback()
                self.destroy()
                messagebox.showinfo("Sucesso", "Venda removida!")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro: {e}")

# ==========================================
# 7. RELATÓRIOS
# ==========================================
class JanelaRelatorio(ctk.CTkToplevel):
    def __init__(self, parent, callback_main):
        super().__init__(parent)
        self.callback_main = callback_main
        self.title("Histórico de Vendas")
        self.geometry("900x650"); self.grab_set()
        
        self.tree = ttk.Treeview(self, columns=("ID", "DATA", "FORMA", "VALOR", "DESC"), show="headings")
        self.tree.heading("ID", text="ID"); self.tree.heading("DATA", text="DATA/HORA")
        self.tree.heading("FORMA", text="FORMA"); self.tree.heading("VALOR", text="TOTAL")
        self.tree.heading("DESC", text="DESCRIÇÃO")
        self.tree.column("ID", width=50); self.tree.column("DESC", width=300)
        self.tree.pack(fill="both", expand=True, padx=20, pady=20)
        
        btn_del = ctk.CTkButton(self, text="GERENCIAR / EXCLUIR REGISTRO", fg_color="#c0392b", height=45, font=("Roboto", 14, "bold"), command=self.abrir_exclusao)
        btn_del.pack(pady=10, padx=20, fill="x")
        
        self.carregar_dados()

    def carregar_dados(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        with sqlite3.connect('Livro Caixa.db') as conn:
            res = conn.cursor().execute("SELECT id, data_ms, metodo, total, descricao_resumo FROM vendas ORDER BY id DESC").fetchall()
            for r in res:
                dt = datetime.fromtimestamp(r[1]/1000).strftime('%d/%m/%Y %H:%M')
                self.tree.insert("", "end", values=(r[0], dt, r[2], f"R$ {float(r[3]):.2f}", r[4]))

    def abrir_exclusao(self):
        sel = self.tree.selection()
        if not sel: return
        v_id = self.tree.item(sel)['values'][0]
        JanelaDetalhesExclusao(self, v_id, lambda: [self.carregar_dados(), self.callback_main()])

# ==========================================
# 9. MÓDULO: FECHAMENTO DE CAIXA
# ==========================================
class JanelaFechamento(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Fechamento de Caixa Diário")
        self.geometry("500x600")
        self.grab_set()

        ctk.CTkLabel(self, text="RESUMO DE HOJE", font=("Roboto", 24, "bold")).pack(pady=20)
        
        self.f_resumo = ctk.CTkFrame(self)
        self.f_resumo.pack(fill="both", expand=True, padx=30, pady=10)
        
        self.gerar_relatorio()
        
        ctk.CTkButton(self, text="IMPRIMIR FECHAMENTO (PDF)", fg_color="#27ae60", 
                      command=self.exportar_pdf).pack(pady=20, padx=30, fill="x")

    def gerar_relatorio(self):
        hoje_inicio = int(datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp() * 1000)
        self.dados_fechamento = {"DINHEIRO": 0.0, "CARTÃO": 0.0, "PIX": 0.0, "FIADO": 0.0, "MOV. CAIXA": 0.0}
        
        with sqlite3.connect('Livro Caixa.db') as conn:
            cur = conn.cursor()
            cur.execute("SELECT metodo, total FROM vendas WHERE data_ms >= ?", (hoje_inicio,))
            vendas = cur.fetchall()
            for met, tot in vendas:
                if met in self.dados_fechamento:
                    self.dados_fechamento[met] += tot
        
        total_vendas = sum([v for k, v in self.dados_fechamento.items() if k != "MOV. CAIXA"])
        saldo_caixa = self.dados_fechamento["DINHEIRO"] + self.dados_fechamento["MOV. CAIXA"]

        for chave, valor in self.dados_fechamento.items():
            cor = "#2ecc71" if valor >= 0 else "#e74c3c"
            ctk.CTkLabel(self.f_resumo, text=f"{chave}:", font=("Roboto", 16)).pack(pady=2, padx=20, anchor="w")
            ctk.CTkLabel(self.f_resumo, text=f"R$ {valor:.2f}", font=("Roboto", 16, "bold"), text_color=cor).pack(pady=2, padx=20, anchor="e")

        ctk.CTkLabel(self.f_resumo, text="-"*40).pack()
        ctk.CTkLabel(self.f_resumo, text=f"TOTAL VENDIDO: R$ {total_vendas:.2f}", font=("Roboto", 18, "bold")).pack(pady=5)
        ctk.CTkLabel(self.f_resumo, text=f"SALDO EM ESPÉCIE (CAIXA): R$ {saldo_caixa:.2f}", 
                     font=("Roboto", 18, "bold"), text_color="#f1c40f").pack(pady=5)

    def exportar_pdf(self):
        nome_arq = f"Fechamento_{datetime.now().strftime('%d_%m_%Y')}.pdf"
        pdf = canvas.Canvas(nome_arq, pagesize=A4)
        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(50, 800, f"FECHAMENTO DE CAIXA - {datetime.now().strftime('%d/%m/%Y')}")
        pdf.line(50, 790, 550, 790)
        y = 760
        pdf.setFont("Helvetica", 12)
        for k, v in self.dados_fechamento.items():
            pdf.drawString(50, y, f"{k}: R$ {v:.2f}")
            y -= 20
        pdf.save()
        messagebox.showinfo("Sucesso", "Relatório de fechamento gerado!")
        os.startfile(nome_arq)

# ==========================================
# 8. TELA PRINCIPAL
# ==========================================
class SistemaPDV(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("BEAR SNACK - SISTEMA DE GESTÃO")
        self.attributes("-fullscreen", True)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=4)
        self.grid_rowconfigure(0, weight=1)

        # 1. BARRA LATERAL (MENU)
        self.f_menu = ctk.CTkFrame(self, corner_radius=0)
        self.f_menu.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # LOGOTIPO NO MENU (SUPERIOR)
        try:
            img_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")
            self.img_logo_menu = ctk.CTkImage(light_image=Image.open(img_path),
                                              dark_image=Image.open(img_path),
                                              size=(180, 180))
            self.l_logo_menu = ctk.CTkLabel(self.f_menu, image=self.img_logo_menu, text="")
            self.l_logo_menu.pack(pady=20)
        except:
            ctk.CTkLabel(self.f_menu, text="BEAR SNACK", font=("Roboto", 20, "bold")).pack(pady=30)

        # BOTÕES DO MENU
        ctk.CTkButton(self.f_menu, text="VENDAS (F1)", height=50, command=lambda: JanelaCarrinho(self, self.atualizar_vendas)).pack(pady=10, padx=20, fill="x")
        ctk.CTkButton(self.f_menu, text="CADERNETA (F2)", height=50, command=lambda: JanelaCaderneta(self)).pack(pady=10, padx=20, fill="x")
        ctk.CTkButton(self.f_menu, text="MOVIMENTAÇÃO (F7)", height=50, command=lambda: JanelaMovimentacao(self, self.atualizar_vendas)).pack(pady=10, padx=20, fill="x")
        ctk.CTkButton(self.f_menu, text="HISTÓRICO / RELATÓRIO", height=50, command=lambda: JanelaRelatorio(self, self.atualizar_vendas)).pack(pady=10, padx=20, fill="x")
        ctk.CTkButton(self.f_menu, text="FECHAMENTO (F12)", height=50, fg_color="#16a085", command=lambda: JanelaFechamento(self)).pack(pady=10, padx=20, fill="x")
        
        ctk.CTkButton(self.f_menu, text="SAIR", fg_color="#c0392b", command=self.confirmar_saida).pack(side="bottom", pady=20, padx=20, fill="x")

        # 2. ÁREA CENTRAL (RELATÓRIO DE ÚLTIMAS TRANSAÇÕES)
        self.f_main = ctk.CTkFrame(self, fg_color="transparent")
        self.f_main.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        ctk.CTkLabel(self.f_main, text="ÚLTIMAS TRANSAÇÕES", font=("Roboto", 24, "bold")).pack(pady=(20, 10))
        
        # TABELA DE ÚLTIMAS TRANSAÇÕES
        self.tree = ttk.Treeview(self.f_main, columns=("DATA", "METODO", "TOTAL", "DESC"), show="headings")
        self.tree.heading("DATA", text="DATA/HORA")
        self.tree.heading("METODO", text="MÉTODO")
        self.tree.heading("TOTAL", text="TOTAL")
        self.tree.heading("DESC", text="DESCRIÇÃO")
        self.tree.column("DATA", width=150)
        self.tree.column("METODO", width=120)
        self.tree.column("TOTAL", width=100)
        self.tree.column("DESC", width=400)
        self.tree.pack(fill="both", expand=True, padx=20, pady=20)

        # CONFIGURAÇÕES DE SISTEMA
        self.ultimo_movimento = datetime.now()
        self.protetor_ativo = False
        
        self.bind("<F1>", lambda e: JanelaCarrinho(self, self.atualizar_vendas))
        self.bind("<F2>", lambda e: JanelaCaderneta(self))
        self.bind("<F7>", lambda e: JanelaMovimentacao(self, self.atualizar_vendas))
        self.bind("<F12>", lambda e: JanelaFechamento(self))
        
        self.bind("<Motion>", self.resetar_timer)
        self.bind("<Any-KeyPress>", self.resetar_timer)
        
        self.atualizar_vendas()
        self.verificar_inatividade()

    def confirmar_saida(self):
        if messagebox.askyesno("Sair do Sistema", "Deseja realmente fechar o sistema BEAR SNACK?"):
            self.quit()

    def atualizar_vendas(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        with sqlite3.connect('Livro Caixa.db') as conn:
            res = conn.cursor().execute("SELECT data_ms, metodo, total, descricao_resumo FROM vendas ORDER BY id DESC LIMIT 20").fetchall()
            for r in res:
                dt = datetime.fromtimestamp(r[0]/1000).strftime('%d/%m/%Y %H:%M')
                self.tree.insert("", "end", values=(dt, r[1], f"R$ {float(r[2]):.2f}", r[3]))

    def resetar_timer(self, event=None):
        self.ultimo_movimento = datetime.now()

    def verificar_inatividade(self):
        if (datetime.now() - self.ultimo_movimento).total_seconds() > 300: # 5 minutos
            if not self.protetor_ativo:
                self.protetor_ativo = True
                ProtetorTela(self)
        self.after(10000, self.verificar_inatividade)

# ==========================================
# INICIALIZAÇÃO
# ==========================================
if __name__ == "__main__":
    app = SistemaPDV()
    app.mainloop()
    