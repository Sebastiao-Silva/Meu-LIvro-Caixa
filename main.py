import flet as ft
import sqlite3
import urllib.parse
import pandas as pd
import os
import time
import shutil
from datetime import datetime

def main(page: ft.Page):
    # 1. CONFIGURAÇÕES DE PÁGINA E ASSETS
    page.assets_dir = "assets" 
    page.title = "BEAR SNACK"
    page.theme_mode = ft.ThemeMode.DARK
    
    # 2. DECLARAÇÃO DE VARIÁVEIS DE ESTADO
    total_venda_atual = 0.0

    # 3. DETECÇÃO DE PLATAFORMA E CAMINHO DO BANCO
    def get_db_path():
        nome_db = "Livro_Caixa.db"
        if page.platform == ft.PagePlatform.ANDROID or page.platform == ft.PagePlatform.IOS:
            return os.path.join(os.getcwd(), nome_db)
        else:
            return os.path.join(os.path.dirname(os.path.abspath(__file__)), nome_db)

    def get_db():
        caminho_db = get_db_path()
        conn = sqlite3.connect(caminho_db, check_same_thread=False)
        # Tabelas principais
        conn.execute("""
            CREATE TABLE IF NOT EXISTS clientes (
                nome TEXT,
                saldo_devedor REAL DEFAULT 0,
                tipo TEXT DEFAULT 'CLIENTE',
                telefone TEXT,
                documento TEXT,
                classe TEXT,
                periodo TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS vendas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_ms INTEGER,
                total REAL,
                metodo TEXT,
                descricao_resumo TEXT,
                baixada INTEGER DEFAULT 1,
                cliente_nome TEXT
            )
        """)
        # Migrações
        colunas_novas = [
            ("tipo", "TEXT DEFAULT 'CLIENTE'"),
            ("telefone", "TEXT"),
            ("documento", "TEXT"),
            ("classe", "TEXT"),
            ("periodo", "TEXT")
        ]
        for col, tipo in colunas_novas:
            try:
                conn.execute(f"ALTER TABLE clientes ADD COLUMN {col} {tipo}")
            except:
                pass
        return conn

    # --- RESTAURAÇÃO E EXPORTAÇÃO ---
    def ao_selecionar_arquivo(e: ft.FilePickerResultEvent):
        if e.files:
            caminho_selecionado = e.files[0].path
            caminho_atual = get_db_path()

            def processar_substituicao():
                try:
                    shutil.copy(caminho_selecionado, caminho_atual)
                    page.snack_bar = ft.SnackBar(ft.Text("Banco de Dados Restaurado com Sucesso!"), bgcolor="blue")
                    page.snack_bar.open = True
                    atualizar_clientes()
                    atualizar_historico()
                    page.update()
                except Exception as ex:
                    page.snack_bar = ft.SnackBar(ft.Text(f"Erro na restauração: {str(ex)}"), bgcolor="red")
                    page.snack_bar.open = True
                    page.update()

            confirmar_acao(
                "RESTAURAR DADOS", 
                "Isso substituirá todos os dados atuais pelos do arquivo selecionado. Confirma?", 
                processar_substituicao
            )

    picker_restaurar = ft.FilePicker(on_result=ao_selecionar_arquivo)
    page.overlay.append(picker_restaurar)

    def exportar_excel(e):
        try:
            conn = get_db()
            df_vendas = pd.read_sql_query("SELECT * FROM vendas", conn)
            df_clientes = pd.read_sql_query("SELECT * FROM clientes", conn)
            conn.close()

            data_str = datetime.now().strftime("%d_%m_%Y_%H%M")
            nome_arquivo = f"Backup_BearSnack_{data_str}.xlsx"
            caminho_final = os.path.abspath(nome_arquivo)
            
            with pd.ExcelWriter(caminho_final, engine='openpyxl') as writer:
                df_vendas.to_excel(writer, sheet_name="Vendas", index=False)
                df_clientes.to_excel(writer, sheet_name="Clientes", index=False)
            
            page.snack_bar = ft.SnackBar(ft.Text(f"Arquivo gerado: {nome_arquivo}"), bgcolor="green")
            page.snack_bar.open = True
            page.update()
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"Erro ao salvar: {str(ex)}"), bgcolor="red")
            page.snack_bar.open = True
            page.update()

    # --- LOGIN ---
    def validar_login(e):
        if campo_senha.value == "Hillary2010": 
            view_login.visible = False
            container_sistema.visible = True
            nav_bar.visible = True
            page.update()
        else:
            campo_senha.error_text = "Senha incorreta!"
            page.update()

    campo_senha = ft.TextField(
        label="Senha de Acesso", 
        password=True, 
        can_reveal_password=True, 
        width=300,
        on_submit=validar_login
    )

    view_login = ft.Column([
        ft.Container(
            content=ft.Image(src="logo.png", width=250, height=250, fit=ft.ImageFit.CONTAIN),
            alignment=ft.alignment.center,
            expand=True
        ),
        ft.Text("ÁREA RESTRITA", size=20, weight="bold", color="blue"),
        campo_senha,
        ft.Container(
            content=ft.ElevatedButton("ENTRAR", on_click=validar_login, width=200, height=50),
            padding=ft.padding.only(bottom=50)
        )
    ], horizontal_alignment="center", alignment="center", expand=True, visible=True)

    # --- FUNÇÕES DE NEGÓCIO ---
    def enviar_whatsapp(nome, total, lista_itens):
        try:
            conn = get_db()
            perfil = conn.execute("SELECT telefone FROM clientes WHERE nome = ?", (nome,)).fetchone()
            conn.close()
            tel = perfil[0] if perfil and perfil[0] else ""
            msg = f"*BEAR SNACK - Relatório de Débito*\n\n"
            msg += f"Olá, *{nome}*!\n"
            msg += f"Seguem seus consumos pendentes:\n\n"
            msg += lista_itens
            msg += f"\n*Total Pendente: R$ {total:.2f}*"
            texto_url = urllib.parse.quote(msg)
            page.launch_url(f"https://wa.me/{tel}?text={texto_url}")
        except: pass

    def confirmar_acao(titulo, mensagem, ao_confirmar):
        def fechar(e):
            dlg_confirmar.open = False
            page.update()
        def executar_e_fechar(e):
            ao_confirmar()
            dlg_confirmar.open = False
            page.update()
        dlg_confirmar.title = ft.Text(titulo)
        dlg_confirmar.content = ft.Text(mensagem)
        dlg_confirmar.actions = [
            ft.TextButton("CANCELAR", on_click=fechar),
            ft.TextButton("CONFIRMAR", on_click=executar_e_fechar),
        ]
        dlg_confirmar.open = True
        page.update()

    def cadastrar_novo_perfil(e):
        if not e_novo_nome.value: return
        try:
            conn = get_db()
            conn.execute("""INSERT INTO clientes (nome, saldo_devedor, tipo, telefone, documento, classe, periodo) 
                            VALUES (?, 0, ?, ?, ?, ?, ?)""", 
                         (e_novo_nome.value.upper(), e_novo_tipo.value, e_novo_tel.value, 
                          e_novo_doc.value, e_novo_classe.value, e_novo_periodo.value))
            conn.commit()
            conn.close()
            e_novo_nome.value = ""
            e_novo_tel.value = ""
            e_novo_doc.value = ""
            e_novo_classe.value = ""
            dlg_cadastro.open = False
            atualizar_clientes()
            page.update()
        except: pass

    def salvar_edicao_perfil(e):
        rowid_perfil = e_edit_nome.data 
        def acao():
            try:
                conn = get_db()
                conn.execute("""UPDATE clientes SET nome = ?, tipo = ?, telefone = ?, documento = ?, 
                                classe = ?, periodo = ? WHERE rowid = ?""", 
                             (e_edit_nome.value.upper(), e_edit_tipo.value, e_edit_tel.value, 
                              e_edit_doc.value, e_edit_classe.value, e_edit_periodo.value, rowid_perfil))
                conn.commit()
                conn.close()
                dlg_editar.open = False
                atualizar_clientes()
            except: pass
        confirmar_acao("Alterar Perfil", "Deseja salvar as alterações neste perfil?", acao)

    def excluir_perfil(e):
        rowid_perfil = e_edit_nome.data
        def acao():
            try:
                conn = get_db()
                conn.execute("DELETE FROM clientes WHERE rowid = ?", (rowid_perfil,))
                conn.commit()
                conn.close()
                dlg_editar.open = False
                atualizar_clientes()
            except: pass
        confirmar_acao("Excluir Perfil", "Tem certeza que deseja excluir este cadastro?", acao)

    def abrir_edicao_venda(id_venda, desc_atual, valor_atual):
        e_edit_venda_desc.value = desc_atual
        e_edit_venda_valor.value = str(valor_atual).replace(".", ",")
        e_edit_venda_desc.data = id_venda
        dlg_editar_venda.open = True
        page.update()

    def salvar_alteracao_venda(e):
        id_v = e_edit_venda_desc.data
        nova_desc = e_edit_venda_desc.value
        try:
            novo_valor = float(e_edit_venda_valor.value.replace(",", "."))
            conn = get_db()
            venda = conn.execute("SELECT cliente_nome, total, baixada FROM vendas WHERE id = ?", (id_v,)).fetchone()
            if venda:
                nome_c, valor_antigo, baixada = venda[0], venda[1], venda[2]
                conn.execute("UPDATE vendas SET descricao_resumo = ?, total = ? WHERE id = ?", (nova_desc, novo_valor, id_v))
                if baixada == 0 and nome_c:
                    diferenca = novo_valor - valor_antigo
                    conn.execute("UPDATE clientes SET saldo_devedor = saldo_devedor + ? WHERE nome = ?", (diferenca, nome_c))
            conn.commit()
            conn.close()
            dlg_editar_venda.open = False
            if nome_c: mostrar_detalhes_cliente(nome_c)
            atualizar_clientes()
            atualizar_historico()
        except: pass

    def excluir_venda(id_venda):
        def acao():
            try:
                conn = get_db()
                venda = conn.execute("SELECT cliente_nome, total, baixada FROM vendas WHERE id = ?", (id_venda,)).fetchone()
                nome_c = None
                if venda:
                    nome_c, total_v, baixada = venda[0], venda[1], venda[2]
                    if baixada == 0 and nome_c:
                        conn.execute("UPDATE clientes SET saldo_devedor = saldo_devedor - ? WHERE nome = ?", (total_v, nome_c))
                conn.execute("DELETE FROM vendas WHERE id = ?", (id_venda,))
                conn.commit()
                conn.close()
                if nome_c: mostrar_detalhes_cliente(nome_c)
                atualizar_historico()
                atualizar_clientes()
            except: pass
        confirmar_acao("Excluir Venda", "Deseja apagar este registro?", acao)

    def dar_baixa_pagamento(nome_cliente):
        def acao():
            try:
                conn = get_db()
                conn.execute("UPDATE vendas SET baixada = 1 WHERE cliente_nome = ?", (nome_cliente,))
                conn.execute("UPDATE clientes SET saldo_devedor = 0 WHERE nome = ?", (nome_cliente,))
                conn.commit()
                conn.close()
                dlg_relatorio.open = False 
                atualizar_clientes()
                page.snack_bar = ft.SnackBar(ft.Text(f"Dívida de {nome_cliente} quitada!"), bgcolor="blue")
                page.snack_bar.open = True
                page.update()
            except: pass
        confirmar_acao("Quitar Dívida", f"Confirmar pagamento total de {nome_cliente}?", acao)

    def mostrar_detalhes_cliente(nome_cliente):
        dialog_lista.controls.clear()
        total_pendente = 0
        itens_txt = ""
        try:
            conn = get_db()
            # Buscamos o histórico completo (baixadas e não baixadas) para conferência
            vendas = conn.execute("""SELECT id, descricao_resumo, total, data_ms, baixada 
                                     FROM vendas WHERE cliente_nome = ? 
                                     ORDER BY data_ms DESC""", (nome_cliente,)).fetchall()
            
            if not vendas:
                dialog_lista.controls.append(ft.Text("Nenhum registro encontrado.", color="grey"))
            else:
                for v in vendas:
                    id_v, item_desc, item_valor, ms, baixada = v[0], str(v[1]), float(v[2]), v[3], v[4]
                    
                    # Formatação da data e hora
                    dt = datetime.fromtimestamp(ms / 1000.0)
                    data_formatada = dt.strftime("%d/%m %H:%M")
                    
                    if baixada == 0:
                        total_pendente += item_valor
                        itens_txt += f"• {data_formatada} - {item_desc}: R$ {item_valor:.2f}\n"
                        cor_texto = "red"
                        texto_status = " (PENDENTE)"
                    else:
                        cor_texto = "green"
                        texto_status = " (PAGO)"

                    dialog_lista.controls.append(
                        ft.ListTile(
                            leading=ft.Text(data_formatada, size=11, color="grey"),
                            title=ft.Text(f"{item_desc}{texto_status}", color=cor_texto, weight="bold", size=14), 
                            subtitle=ft.Text(f"R$ {item_valor:.2f}"),
                            trailing=ft.Row([
                                ft.IconButton(ft.Icons.EDIT, icon_size=20, on_click=lambda e, iv=id_v, d=item_desc, vl=item_valor: abrir_edicao_venda(iv, d, vl)),
                                ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_size=20, icon_color="red", on_click=lambda e, iv=id_v: excluir_venda(iv))
                            ], tight=True)
                        )
                    )
            conn.close()
            lbl_total_dialog.value = f"TOTAL PENDENTE: R$ {total_pendente:.2f}"
            btn_zap.on_click = lambda _: enviar_whatsapp(nome_cliente, total_pendente, itens_txt)
            btn_baixar.on_click = lambda _: dar_baixa_pagamento(nome_cliente)
            dlg_relatorio.title = ft.Text(f"Histórico: {nome_cliente}")
            dlg_relatorio.open = True
            page.update()
        except: pass

    def filtrar_clientes(e):
        termo = str(e.control.value).lower()
        atualizar_clientes(termo)

    def atualizar_clientes(filtro=""):
        lista_clientes.controls.clear()
        lista_alunos.controls.clear()
        lista_bandeja_caderneta.controls.clear()
        lista_checkbox_bandeja.controls.clear() 
        opcoes_dropdown = []
        try:
            conn = get_db()
            res = conn.execute("SELECT rowid, nome, saldo_devedor, tipo, periodo FROM clientes ORDER BY nome").fetchall()
            for r in res:
                rid, nome_c, divida, tipo_c, periodo_c = r[0], str(r[1]), float(r[2]), str(r[3]).upper(), r[4] or ""
                opcoes_dropdown.append(ft.dropdown.Option(nome_c))
                
                if filtro in nome_c.lower():
                    item = ft.ListTile(
                        leading=ft.Icon(ft.Icons.PERSON, color="blue" if tipo_c == "CLIENTE" else "orange"),
                        title=ft.Text(nome_c, weight="bold"),
                        subtitle=ft.Text(f"{periodo_c} - Dívida: R$ {divida:.2f}", color="red" if divida > 0 else "grey"),
                        trailing=ft.IconButton(ft.Icons.SETTINGS, on_click=lambda e, id_r=rid: abrir_edicao(id_r)),
                        on_click=lambda e, n=nome_c: mostrar_detalhes_cliente(n)
                    )
                    if tipo_c == "ALUNO": lista_alunos.controls.append(item)
                    elif tipo_c == "CLIENTE": lista_clientes.controls.append(item)
                    elif tipo_c == "BANDEJA": lista_bandeja_caderneta.controls.append(item)

                if tipo_c == "BANDEJA":
                    lista_checkbox_bandeja.controls.append(ft.Checkbox(label=f"{nome_c} ({periodo_c})", value=False, data=nome_c))
            
            select_cliente.options = opcoes_dropdown
            conn.close()
        except: pass
        page.update()

    def adicionar_ao_total(e):
        nonlocal total_venda_atual
        if not e_valor.value: return
        try:
            valor = float(e_valor.value.replace(",", "."))
            total_venda_atual += valor
            lbl_soma_venda.value = f"Total Atual: R$ {total_venda_atual:.2f}"
            e_valor.value = ""
            page.update()
        except: pass

    def adicionar_por_botao(nome, valor):
        e_desc.value = f"{e_desc.value} {nome}".strip()
        e_valor.value = str(valor).replace(".", ",")
        page.update()

    def limpar_venda_atual(e):
        nonlocal total_venda_atual
        total_venda_atual = 0.0
        lbl_soma_venda.value = "Total Atual: R$ 0.00"
        e_desc.value = ""
        e_valor.value = ""
        page.update()

    def finalizar_venda(e):
        nonlocal total_venda_atual
        valor_final = 0.0
        if total_venda_atual > 0: valor_final = total_venda_atual
        elif e_valor.value: valor_final = float(e_valor.value.replace(",", "."))
        if valor_final <= 0: return
        try:
            desc = e_desc.value or "Venda"
            met = metodo_pag.value
            cliente_nome = select_cliente.value
            agora = int(datetime.now().timestamp() * 1000)
            conn = get_db()
            status_baixa = 0 if met in ["FIADO", "CRÉDITO"] else 1
            conn.execute("INSERT INTO vendas (data_ms, total, metodo, descricao_resumo, baixada, cliente_nome) VALUES (?,?,?,?,?,?)", 
                         (agora, valor_final, met, desc, status_baixa, cliente_nome))
            if status_baixa == 0 and cliente_nome:
                conn.execute("UPDATE clientes SET saldo_devedor = saldo_devedor + ? WHERE nome = ?", (valor_final, cliente_nome))
            conn.commit()
            conn.close()
            e_valor.value = ""
            e_desc.value = ""
            select_cliente.value = None
            total_venda_atual = 0.0
            lbl_soma_venda.value = "Total Atual: R$ 0.00"
            img_animada.src = "BearSnack.gif"
            page.update()
            time.sleep(3)
            img_animada.src = "logo.png"
            page.snack_bar = ft.SnackBar(ft.Text("Venda registrada!"), bgcolor="green")
            page.snack_bar.open = True
            atualizar_historico()
            page.update()
        except: pass

    def atualizar_historico():
        lista_historico.controls.clear()
        try:
            conn = get_db()
            res = conn.execute("""SELECT id, descricao_resumo, total, metodo, data_ms 
                                  FROM vendas ORDER BY id DESC LIMIT 20""").fetchall()
            for r in res:
                dt_h = datetime.fromtimestamp(r[4] / 1000.0).strftime("%d/%m %H:%M")
                lista_historico.controls.append(
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.MONETIZATION_ON, color="green"), 
                        title=ft.Text(f"{r[1]} ({dt_h})"), 
                        subtitle=ft.Text(f"R$ {float(r[2]):.2f} - {r[3]}"), 
                        trailing=ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, icon_color="red", on_click=lambda e, id_v=r[0]: excluir_venda(id_v))
                    )
                )
            conn.close()
        except: pass
        page.update()

    def abrir_edicao(rowid_perfil):
        try:
            conn = get_db()
            p = conn.execute("SELECT nome, tipo, telefone, documento, classe, periodo FROM clientes WHERE rowid = ?", (rowid_perfil,)).fetchone()
            conn.close()
            if p:
                e_edit_nome.value = p[0]
                e_edit_nome.data = rowid_perfil 
                e_edit_tipo.value = p[1]
                e_edit_tel.value = p[2]
                e_edit_doc.value = p[3]
                e_edit_classe.value = p[4]
                e_edit_periodo.value = p[5]
                dlg_editar.open = True
                page.update()
        except: pass

    def salvar_consumo_bandeja(e):
        selecionados = [c.data for c in lista_checkbox_bandeja.controls if c.value]
        if not selecionados:
            page.snack_bar = ft.SnackBar(ft.Text("Ninguém selecionado!"), bgcolor="red")
            page.snack_bar.open = True
            page.update()
            return
        try:
            valor_b = float(e_valor_bandeja.value.replace(",", "."))
            desc_b = e_cardapio_texto.value or "Consumo Bandeja"
            agora = int(datetime.now().timestamp() * 1000)
            conn = get_db()
            for nome in selecionados:
                conn.execute("INSERT INTO vendas (data_ms, total, metodo, descricao_resumo, baixada, cliente_nome) VALUES (?,?,?,?,?,?)", 
                               (agora, valor_b, "FIADO", desc_b, 0, nome))
                conn.execute("UPDATE clientes SET saldo_devedor = saldo_devedor + ? WHERE nome = ?", (valor_b, nome))
            conn.commit()
            conn.close()
            page.snack_bar = ft.SnackBar(ft.Text(f"Consumo registrado para {len(selecionados)} pessoas!"), bgcolor="green")
            page.snack_bar.open = True
            limpar_selecao_bandeja(None)
            atualizar_clientes()
        except:
            page.snack_bar = ft.SnackBar(ft.Text("Verifique o valor inserido!"), bgcolor="red")
            page.snack_bar.open = True
            page.update()

    def limpar_selecao_bandeja(e):
        for checkbox in lista_checkbox_bandeja.controls: checkbox.value = False
        page.update()

    # --- COMPONENTES DE INTERFACE (UI) ---
    dlg_confirmar = ft.AlertDialog(title=ft.Text("Confirmar"), content=ft.Text(""))
    
    e_edit_venda_desc = ft.TextField(label="Descrição da Venda")
    e_edit_venda_valor = ft.TextField(label="Valor (R$)", keyboard_type=ft.KeyboardType.NUMBER)
    dlg_editar_venda = ft.AlertDialog(
        title=ft.Text("Editar Item"),
        content=ft.Column([e_edit_venda_desc, e_edit_venda_valor], tight=True),
        actions=[ft.TextButton("SALVAR ALTERAÇÃO", on_click=salvar_alteracao_venda)]
    )

    e_novo_nome = ft.TextField(label="Nome")
    e_novo_tel = ft.TextField(label="Telefone", keyboard_type=ft.KeyboardType.PHONE)
    e_novo_doc = ft.TextField(label="CPF ou Documento")
    e_novo_classe = ft.TextField(label="Classe")
    e_novo_periodo = ft.Dropdown(label="Período", value="MANHÃ", options=[ft.dropdown.Option("MANHÃ"), ft.dropdown.Option("TARDE")])
    e_novo_tipo = ft.Dropdown(label="Tipo", value="CLIENTE", options=[ft.dropdown.Option("CLIENTE"), ft.dropdown.Option("ALUNO"), ft.dropdown.Option("BANDEJA")])
    
    dlg_cadastro = ft.AlertDialog(
        title=ft.Text("Novo Cadastro"), 
        content=ft.Column([e_novo_nome, e_novo_tel, e_novo_doc, e_novo_classe, e_novo_periodo, e_novo_tipo], tight=True, scroll=ft.ScrollMode.AUTO), 
        actions=[ft.TextButton("SALVAR", on_click=cadastrar_novo_perfil)]
    )

    e_edit_nome = ft.TextField(label="Nome")
    e_edit_tel = ft.TextField(label="Telefone")
    e_edit_doc = ft.TextField(label="CPF/Documento")
    e_edit_classe = ft.TextField(label="Classe")
    e_edit_periodo = ft.Dropdown(label="Período", options=[ft.dropdown.Option("MANHÃ"), ft.dropdown.Option("TARDE")])
    e_edit_tipo = ft.Dropdown(label="Tipo", options=[ft.dropdown.Option("CLIENTE"), ft.dropdown.Option("ALUNO"), ft.dropdown.Option("BANDEJA")])
    
    dlg_editar = ft.AlertDialog(
        title=ft.Text("Configurar Perfil"), 
        content=ft.Column([e_edit_nome, e_edit_tel, e_edit_doc, e_edit_classe, e_edit_periodo, e_edit_tipo], tight=True), 
        actions=[ft.TextButton("EXCLUIR PERFIL", on_click=excluir_perfil, icon_color="red"), ft.TextButton("SALVAR ALTERAÇÕES", on_click=salvar_edicao_perfil)]
    )

    dialog_lista = ft.Column(tight=True, scroll=ft.ScrollMode.AUTO)
    lbl_total_dialog = ft.Text("TOTAL PENDENTE: R$ 0.00", weight="bold", size=18)
    btn_zap = ft.ElevatedButton("ENVIAR WHATSAPP", icon=ft.Icons.SEND, bgcolor="green", color="white")
    btn_baixar = ft.TextButton("DAR BAIXA NO PAGAMENTO TOTAL", icon=ft.Icons.CHECK_CIRCLE)
    dlg_relatorio = ft.AlertDialog(content=ft.Container(content=ft.Column([ft.Container(content=dialog_lista, height=350), ft.Divider(), lbl_total_dialog, ft.Column([btn_zap, btn_baixar], horizontal_alignment="center")], tight=True), width=350))
    
    e_desc = ft.TextField(label="Descrição", width=350)
    e_valor = ft.TextField(label="Valor Unitário (R$)", width=240, keyboard_type=ft.KeyboardType.NUMBER)
    btn_add_valor = ft.IconButton(ft.Icons.ADD_CIRCLE, on_click=adicionar_ao_total, icon_color="blue", icon_size=40)
    lbl_soma_venda = ft.Text("Total Atual: R$ 0.00", size=20, weight="bold", color="green")
    img_animada = ft.Image(src="logo.png", width=180, height=180, fit=ft.ImageFit.CONTAIN)

    botoes_atalho = ft.Row([
        ft.Column([ft.IconButton(ft.Icons.LOCAL_DRINK, on_click=lambda _: adicionar_por_botao("SUCO", 5.00)), ft.Text("SUCO", size=10)], horizontal_alignment="center"),
        ft.Column([ft.IconButton(ft.Icons.APPLE, on_click=lambda _: adicionar_por_botao("FRUTA", 4.00)), ft.Text("FRUTA", size=10)], horizontal_alignment="center"),
        ft.Column([ft.IconButton(ft.Icons.LIQUOR, on_click=lambda _: adicionar_por_botao("REFRI", 6.00)), ft.Text("REFRI", size=10)], horizontal_alignment="center"),
        ft.Column([ft.IconButton(ft.Icons.SET_MEAL, on_click=lambda _: adicionar_por_botao("SALGADO", 8.00)), ft.Text("SALGADO", size=10)], horizontal_alignment="center"),
        ft.Column([ft.IconButton(ft.Icons.LOCAL_CAFE, on_click=lambda _: adicionar_por_botao("SUCO NAT.", 8.00)), ft.Text("NATURAL", size=10)], horizontal_alignment="center"),
        ft.Column([ft.IconButton(ft.Icons.GRAIN, on_click=lambda _: adicionar_por_botao("PIPOCA", 7.00)), ft.Text("PIPOCA", size=10)], horizontal_alignment="center"),
        ft.Column([ft.IconButton(ft.Icons.COOKIE, on_click=lambda _: adicionar_por_botao("BISCOITO", 4.00)), ft.Text("BISCOITO", size=10)], horizontal_alignment="center"),
        ft.Column([ft.IconButton(ft.Icons.BAKERY_DINING, on_click=lambda _: adicionar_por_botao("P. QUEIJO", 7.00)), ft.Text("P.QUEIJO", size=10)], horizontal_alignment="center"),
        ft.Column([ft.IconButton(ft.Icons.LUNCH_DINING, on_click=lambda _: adicionar_por_botao("SANDUÍCHE", 8.00)), ft.Text("SANDUÍCHE", size=10)], horizontal_alignment="center"),
        ft.Column([ft.IconButton(ft.Icons.CAKE, on_click=lambda _: adicionar_por_botao("BOLO", 8.00)), ft.Text("BOLO", size=10)], horizontal_alignment="center"),
    ], wrap=True, alignment="center", width=350)

    metodo_pag = ft.Dropdown(label="Pagamento", value="DINHEIRO", width=350, options=[ft.dropdown.Option("DINHEIRO"), ft.dropdown.Option("PIX"), ft.dropdown.Option("CARTÃO"), ft.dropdown.Option("CRÉDITO"), ft.dropdown.Option("FIADO")])
    select_cliente = ft.Dropdown(label="Devedor", width=350)
    
    view_vendas = ft.Column([
        ft.Text("BEAR SNACK", size=32, weight="bold", color="blue"), 
        botoes_atalho, ft.Divider(), e_desc, 
        ft.Row([e_valor, btn_add_valor], alignment="center"),
        ft.Container(content=lbl_soma_venda, padding=10, border=ft.border.all(1, "grey"), border_radius=10),
        metodo_pag, select_cliente, 
        ft.Row([ft.ElevatedButton("LIMPAR", on_click=limpar_venda_atual, bgcolor="red", color="white", width=120, height=50), ft.ElevatedButton("FINALIZAR", on_click=finalizar_venda, bgcolor="green", color="white", width=200, height=50)], alignment="center"),
        ft.Container(content=img_animada, alignment=ft.alignment.center, padding=10) 
    ], horizontal_alignment="center", visible=True, scroll=ft.ScrollMode.AUTO)

    lista_historico = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
    view_historico = ft.Column([ft.Row([ft.Text("VENDAS", size=24, weight="bold"), ft.IconButton(ft.Icons.ASSESSMENT)], alignment="spaceBetween"), lista_historico], visible=False, expand=True)

    lista_clientes = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
    lista_alunos = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
    lista_bandeja_caderneta = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
    view_clientes = ft.Column([
        ft.Row([
            ft.Text("CADERNETA", size=24, weight="bold"), 
            ft.Row([
                ft.IconButton(ft.Icons.UPLOAD_FILE, tooltip="Restaurar Banco", on_click=lambda _: picker_restaurar.pick_files(allowed_extensions=["db"])),
                ft.IconButton(ft.Icons.DOWNLOAD, tooltip="Exportar Excel", on_click=exportar_excel), 
                ft.IconButton(ft.Icons.ADD_CIRCLE, on_click=lambda _: (setattr(dlg_cadastro, 'open', True), page.update()))
            ])
        ], alignment="spaceBetween"), 
        ft.TextField(label="Pesquisar...", prefix_icon=ft.Icons.SEARCH, on_change=filtrar_clientes, width=350), 
        ft.Tabs(selected_index=0, tabs=[ft.Tab(text="Clientes", content=lista_clientes), ft.Tab(text="Alunos", content=lista_alunos), ft.Tab(text="Bandeja", content=lista_bandeja_caderneta)], expand=True)
    ], visible=False, expand=True, horizontal_alignment="center")

    lista_checkbox_bandeja = ft.Column(scroll=ft.ScrollMode.AUTO, height=250)
    e_cardapio_texto = ft.TextField(label="Cardápio do Dia", multiline=True, min_lines=3, width=350)
    e_valor_bandeja = ft.TextField(label="Valor do Cardápio (R$)", width=350, keyboard_type=ft.KeyboardType.NUMBER)
    
    view_bandeja = ft.Column([
        ft.Text("BANDEJA DO DIA", size=24, weight="bold", color="orange"),
        e_cardapio_texto, e_valor_bandeja, 
        ft.ElevatedButton("ANEXAR FOTO DO PRATO", icon=ft.Icons.PHOTO_CAMERA, width=350),
        ft.Divider(),
        ft.Row([ft.Text("QUEM CONSUMIU HOJE?", weight="bold"), ft.TextButton("LIMPAR SELEÇÃO", on_click=limpar_selecao_bandeja)], alignment="spaceBetween", width=350),
        ft.Container(content=lista_checkbox_bandeja, border=ft.border.all(1, "grey"), border_radius=10, padding=10),
        ft.ElevatedButton("CONFIRMAR CONSUMO", on_click=salvar_consumo_bandeja, bgcolor="orange", color="white", width=350, height=50)
    ], visible=False, horizontal_alignment="center", scroll=ft.ScrollMode.AUTO)

    def mudar_aba(e):
        idx = e.control.selected_index
        view_vendas.visible = (idx == 0)
        view_historico.visible = (idx == 1)
        view_clientes.visible = (idx == 2)
        view_bandeja.visible = (idx == 3)
        if idx in [1, 2, 3]: 
            atualizar_historico()
            atualizar_clientes()
        page.update()

    nav_bar = ft.NavigationBar(
        on_change=mudar_aba, 
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.ADD_SHOPPING_CART, label="Vender"), 
            ft.NavigationBarDestination(icon=ft.Icons.HISTORY, label="Vendas"), 
            ft.NavigationBarDestination(icon=ft.Icons.PEOPLE, label="Clientes"), 
            ft.NavigationBarDestination(icon=ft.Icons.RESTAURANT, label="Bandeja")
        ],
        visible=False 
    )

    page.navigation_bar = nav_bar
    container_sistema = ft.Container(content=ft.Column([view_vendas, view_historico, view_clientes, view_bandeja], expand=True), expand=True, visible=False)
    page.overlay.extend([dlg_cadastro, dlg_editar, dlg_relatorio, dlg_confirmar, dlg_editar_venda])
    page.add(view_login, container_sistema)
    
    atualizar_clientes()
    atualizar_historico()

if __name__ == "__main__":
    ft.app(target=main)