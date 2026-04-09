import customtkinter
import database
from tkinter import messagebox, Toplevel, simpledialog
from tkcalendar import Calendar
from datetime import datetime
import re
import webbrowser

class AbaPFMEA:
    def __init__(self, parent, controller):
        self.parent = parent
        self.controller = controller
        self.edit_id = None
        self.is_nova_revisao = False 
        
        self.font_title = ("Arial", 18, "bold")
        self.font_label = ("Arial", 13, "bold")
        self.font_entry = ("Arial", 13)
        self.font_button = ("Arial", 13, "bold")
        self.font_lista_bold = ("Arial", 15, "bold")
        self.font_lista_small = ("Arial", 13, "italic")
        self.font_hist = ("Arial", 14)
        
        self.setup_ui()

    def setup_ui(self):
        for widget in self.parent.winfo_children(): widget.destroy()
        self.pane = customtkinter.CTkFrame(self.parent, fg_color="transparent")
        self.pane.pack(fill="both", expand=True)

        acesso = self.controller.nivel_acesso

        if acesso == "engenharia":
            self.left_col = customtkinter.CTkFrame(self.pane, width=380)
            self.left_col.pack(side="left", fill="both", padx=(10, 5), pady=10)
            self.left_col.pack_propagate(False) 
            
            customtkinter.CTkLabel(self.left_col, text="📝 Gestão de PFMEA", font=self.font_title).pack(pady=(15, 10))
            self.form_container = customtkinter.CTkScrollableFrame(self.left_col, fg_color="transparent")
            self.form_container.pack(fill="both", expand=True, padx=15)

            self.entries = {}
            campos = [
                ("Número do PFMEA:", "num", "Ex: 53"),
                ("Descrição:", "desc", "Ex: Processo de Estamparia"),
                ("Cliente / Projeto:", "cli", "Ex: Toyota"),
                ("Data Inicial:", "dat_ini", "DD/MM/AAAA"),
                ("Data da Revisão Atual:", "dat_rev", "DD/MM/AAAA"),
                ("Índice da Revisão:", "rev_ind", "Ex: Rev. 02"),
                ("Ciclo (Anos):", "ciclo", "2"),
                ("Link do Documento:", "link", "http://...")
            ]

            for label_text, key, placeholder in campos:
                customtkinter.CTkLabel(self.form_container, text=label_text, font=self.font_label).pack(anchor="w", pady=(8, 0))
                row_input = customtkinter.CTkFrame(self.form_container, fg_color="transparent")
                row_input.pack(fill="x", pady=2)
                entry = customtkinter.CTkEntry(row_input, placeholder_text=placeholder, height=35, font=self.font_entry)
                entry.pack(side="left", fill="x", expand=True)
                self.entries[key] = entry
                if "dat" in key:
                    btn_cal = customtkinter.CTkButton(row_input, text="📅", width=35, height=35, command=lambda k=key: self.abrir_calendario(k))
                    btn_cal.pack(side="right", padx=(5, 0))
                    self.entries[key+"_btn"] = btn_cal

            customtkinter.CTkLabel(self.form_container, text="Categoria do Documento:", font=self.font_label).pack(anchor="w", pady=(8, 0))
            self.combo_status = customtkinter.CTkOptionMenu(self.form_container, values=["Ativo", "Pré-lançamento", "Protótipo", "Obsoleto"], height=35)
            self.combo_status.pack(fill="x", pady=(5, 15))

            self.btn_novo = customtkinter.CTkButton(self.left_col, text="➕ Criar Novo PFMEA", command=self.novo_pfmea, height=40, font=self.font_button, fg_color="#2c3e50")
            self.btn_novo.pack(pady=(10, 0), padx=20, fill="x")

            self.btn_save = customtkinter.CTkButton(self.left_col, text="Salvar PFMEA", command=self.save_pf, height=45, font=self.font_button)
            self.btn_save.pack(pady=(10, 5), padx=20, fill="x")
            
            customtkinter.CTkButton(self.left_col, text="Cancelar / Limpar", command=self.reset_form, height=40, font=self.font_button, fg_color="#a83232").pack(padx=20, fill="x", pady=(0, 15))
            
            self.set_fields_state("disabled")

        self.right_col = customtkinter.CTkFrame(self.pane)
        self.right_col.pack(side="right", fill="both", expand=True, padx=(5, 10), pady=10)
        self.filter_frame = customtkinter.CTkFrame(self.right_col, fg_color="transparent")
        self.filter_frame.pack(fill="x", padx=15, pady=(15, 5))
        self.ent_busca = customtkinter.CTkEntry(self.filter_frame, placeholder_text="🔍 Buscar PFMEA...", height=35)
        self.ent_busca.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.ent_busca.bind("<KeyRelease>", lambda e: self.load_pfmeas_list())
        self.combo_filtro_cat = customtkinter.CTkOptionMenu(self.filter_frame, values=["Todas Categ.", "Ativo", "Pré-lançamento", "Protótipo", "Obsoleto"], command=lambda e: self.load_pfmeas_list(), width=130)
        self.combo_filtro_cat.pack(side="left", padx=(0, 10))
        self.combo_ordem = customtkinter.CTkOptionMenu(self.filter_frame, values=["Nº Documento", "Mais Novo", "Mais Antigo", "Cliente"], command=lambda e: self.load_pfmeas_list(), width=140)
        self.combo_ordem.pack(side="right")
        self.scroll = customtkinter.CTkScrollableFrame(self.right_col)
        self.scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.load_pfmeas_list()

    def load_pfmeas_list(self):
        for widget in self.scroll.winfo_children(): widget.destroy()
        acesso = self.controller.nivel_acesso
        termo = f"%{self.ent_busca.get()}%"
        ordem_sel, cat_sel = self.combo_ordem.get(), self.combo_filtro_cat.get()
        ordem_sql = "numero ASC"
        if ordem_sel == "Mais Novo": ordem_sql = "substr(data_atual,7,4)||substr(data_atual,4,2)||substr(data_atual,1,2) DESC"
        elif ordem_sel == "Mais Antigo": ordem_sql = "substr(data_atual,7,4)||substr(data_atual,4,2)||substr(data_atual,1,2) ASC"
        elif ordem_sel == "Cliente": ordem_sql = "cliente ASC"
        
        filtro_cat_sql = ""
        params = [termo, termo]
        if cat_sel != "Todas Categ.": filtro_cat_sql = " AND status = ?"; params.append(cat_sel)
        
        conn = database.connect_db(); cursor = conn.cursor()
        cursor.execute(f"SELECT id, numero, descricao, cliente, data_inicial, data_atual, revisao, status, ciclo_revisao, link_documento FROM pfmeas WHERE (numero LIKE ? OR descricao LIKE ?){filtro_cat_sql} ORDER BY {ordem_sql}", params)
        
        for row in cursor.fetchall():
            pf_id, num, desc, cli, d_ini, d_rev, rev_ind, status, ciclo, link = row
            
            # --- BUSCA DA DATA MAIS RECENTE EM TODA A HISTÓRIA ---
            cursor.execute("""
                SELECT data_rev FROM (
                    SELECT data_rev FROM historico_pfmeas WHERE pfmea_id = ?
                    UNION ALL
                    SELECT data_atual as data_rev FROM pfmeas WHERE id = ?
                ) ORDER BY substr(data_rev,7,4)||substr(data_rev,4,2)||substr(data_rev,1,2) DESC LIMIT 1
            """, (pf_id, pf_id))
            res_data = cursor.fetchone()
            data_mais_recente = res_data[0] if res_data else d_rev

            # Definição das cores padrão baseadas no status
            if status == "Ativo":
                cor_card, cor_borda = "#2d3436", "#0984e3" # Fundo Padrão, Borda Azul
            elif status == "Pré-lançamento":
                cor_card, cor_borda = "#2d3436", "#f39c12" 
            elif status == "Protótipo":
                cor_card, cor_borda = "#2d3436", "#16a085" 
            else:
                cor_card, cor_borda = "#1e1e1e", "#3d3d3d" 

            tag_revisar = ""
            
            # Cálculo de Ciclo e alteração visual se vencido
            if status == "Ativo" and data_mais_recente:
                try:
                    dt_limite = datetime.strptime(data_mais_recente, "%d/%m/%Y")
                    if datetime.now() > dt_limite.replace(year=dt_limite.year + int(ciclo)):
                        tag_revisar = "  ⚠️ REVISAR"
                        # AJUSTE SOLICITADO: Fundo mantém o padrão, borda muda para o vermelho do cancelar
                        cor_card = "#2d3436" 
                        cor_borda = "#a83232" # Vermelho do botão cancelar
                except: pass

            f_item = customtkinter.CTkFrame(self.scroll, fg_color=cor_card, border_width=2, border_color=cor_borda); f_item.pack(fill="x", pady=5, padx=5)
            f_l1 = customtkinter.CTkFrame(f_item, fg_color="transparent"); f_l1.pack(fill="x", padx=12, pady=(10, 0))
            st_icon = "🟢" if status == "Ativo" else "🟠" if status == "Pré-lançamento" else "🔵" if status == "Protótipo" else "⚪"
            
            # Formatação solicitada: PFMEA: 101 | Rev: 1 | Data Recente
            customtkinter.CTkLabel(f_l1, text=f"{st_icon} PFMEA: {num} | Rev: {rev_ind} | {data_mais_recente}{tag_revisar}", font=self.font_lista_bold).pack(side="left")
            
            if acesso == "engenharia":
                customtkinter.CTkButton(f_l1, text="⚙️ Editar", width=75, height=28, font=("Arial", 11, "bold"), command=lambda r=row: self.preparar_edicao(r)).pack(side="right", padx=2)
                if status in ["Ativo", "Pré-lançamento", "Protótipo"]:
                    customtkinter.CTkButton(f_l1, text="♻️ Rev", width=65, height=28, font=("Arial", 11, "bold"), fg_color="#27ae60", hover_color="#1e8449", command=lambda r=row: self.preparar_revisao_rapida(r)).pack(side="right", padx=2)
            
            if link: customtkinter.CTkButton(f_l1, text="🔗 link", width=65, height=28, font=("Arial", 11, "bold"), fg_color="#34495e", command=lambda l=link: webbrowser.open(l)).pack(side="right", padx=2)
            customtkinter.CTkButton(f_l1, text="📂 Detalhes", width=85, height=28, font=("Arial", 11, "bold"), fg_color="#3d3d3d", command=lambda f=f_item, pid=pf_id, r=row: self.mostrar_detalhes_arvore(f, pid, r)).pack(side="right", padx=2)
            
            f_l2 = customtkinter.CTkFrame(f_item, fg_color="transparent"); f_l2.pack(fill="x", padx=12, pady=(0, 10))
            customtkinter.CTkLabel(f_l2, text=f"Desc: {desc} | Cliente: {cli}", font=self.font_lista_small, text_color="#bdc3c7", justify="left").pack(side="left", padx=22)
        conn.close()

    def mostrar_detalhes_arvore(self, container, pf_id, row):
        if len(container.winfo_children()) > 2: container.winfo_children()[2].destroy(); return
        det = customtkinter.CTkFrame(container, fg_color="#181818"); det.pack(fill="x", padx=10, pady=(0, 10))
        acesso = self.controller.nivel_acesso
        conn = database.connect_db(); cursor = conn.cursor()
        
        header_text = f"📅 Início: {row[4]} | ⏳ Ciclo: {row[8]} anos | Categoria: {row[7]}"
        customtkinter.CTkLabel(det, text=header_text, text_color="#3498db", font=("Arial", 12, "bold")).pack(anchor="w", padx=20, pady=10)
        
        customtkinter.CTkLabel(det, text="🛠️ Estrutura Vinculada:", text_color="#3498db", font=("Arial", 12, "bold")).pack(anchor="w", padx=20, pady=(10, 5))
        cursor.execute("SELECT i.numero, i.id, i.data_atual FROM its i JOIN pfmea_it pi ON i.id = pi.it_id WHERE pi.pfmea_id = ?", (pf_id,))
        for it_num, it_id, it_date in cursor.fetchall():
            it_f = customtkinter.CTkFrame(det, fg_color="transparent"); it_f.pack(fill="x", padx=30)
            st_c = "#2ecc71"
            try:
                if datetime.strptime(it_date, "%d/%m/%Y") < datetime.strptime(row[5], "%d/%m/%Y"): st_c = "#e74c3c"
            except: pass
            customtkinter.CTkLabel(it_f, text="●", text_color=st_c, font=("Arial", 18)).pack(side="left", padx=5)
            customtkinter.CTkLabel(it_f, text=f"IT: {it_num} ({it_date})", font=("Arial", 13, "bold")).pack(side="left")
            cursor.execute("SELECT codigo FROM pns WHERE it_id = ?", (it_id,))
            for pn in cursor.fetchall(): customtkinter.CTkLabel(det, text=f"         └─ 📦 PN: {pn[0]}", text_color="#777", font=("Arial", 12)).pack(anchor="w", padx=85)
        
        # --- HISTÓRICO RETRÁTIL (MAIS NOVA PRIMEIRO, MAIS ANTIGA POR ÚLTIMO) ---
        f_hist_header = customtkinter.CTkFrame(det, fg_color="transparent")
        f_hist_header.pack(fill="x", padx=20, pady=(15, 5))
        customtkinter.CTkLabel(f_hist_header, text="📜 Histórico:", text_color="#2ecc71", font=("Arial", 12, "bold")).pack(side="left")
        
        f_itens_hist = customtkinter.CTkFrame(det, fg_color="transparent")
        def toggle_hist():
            if f_itens_hist.winfo_viewable(): f_itens_hist.pack_forget(); btn_toggle.configure(text="▼")
            else: f_itens_hist.pack(fill="x", padx=20, pady=5); btn_toggle.configure(text="▲")

        btn_toggle = customtkinter.CTkButton(f_hist_header, text="▼", width=30, height=20, fg_color="#2ecc71", text_color="black", hover_color="#27ae60", command=toggle_hist)
        btn_toggle.pack(side="left", padx=10)

        # Ordenação por data (Mais recente primeiro, mais antiga por último no final da lista)
        cursor.execute("SELECT id, data_rev, indice_rev, link_rev FROM historico_pfmeas WHERE pfmea_id = ? ORDER BY substr(data_rev,7,4)||substr(data_rev,4,2)||substr(data_rev,1,2) DESC", (pf_id,))
        rows_hist = cursor.fetchall()
        
        if not rows_hist:
            customtkinter.CTkLabel(f_itens_hist, text="   🕒 Sem histórico registrado", font=self.font_hist, text_color="gray").pack(anchor="w")
        
        for h_id, d, i, l in rows_hist:
            h_row = customtkinter.CTkFrame(f_itens_hist, fg_color="transparent"); h_row.pack(fill="x", pady=2)
            customtkinter.CTkLabel(h_row, text=f"   🕒 Rev: {i} - {d}", font=self.font_hist).pack(side="left")
            if acesso == "engenharia":
                customtkinter.CTkButton(h_row, text="🗑", width=35, height=25, font=("Arial", 12), fg_color="#c0392b", hover_color="#e74c3c", command=lambda hid=h_id: self.deletar_rev(hid)).pack(side="right", padx=2)
                customtkinter.CTkButton(h_row, text="✎", width=35, height=25, font=("Arial", 14), fg_color="#d35400", hover_color="#e67e22", command=lambda hid=h_id, link=l: self.editar_link_h(hid, link)).pack(side="right", padx=2)
            if l: customtkinter.CTkButton(h_row, text="🔗", width=35, height=25, font=("Arial", 12), fg_color="#2980b9", hover_color="#3498db", command=lambda url=l: webbrowser.open(url)).pack(side="right", padx=2)
        conn.close()

    def set_fields_state(self, state):
        if hasattr(self, 'entries'):
            for key, widget in self.entries.items(): widget.configure(state=state)
            self.combo_status.configure(state=state)
            self.btn_save.configure(state=state)

    def novo_pfmea(self):
        self.reset_form(); self.set_fields_state("normal"); self.entries["num"].focus()

    def save_pf(self):
        v = {k: self.entries[k].get() for k in ["num", "desc", "cli", "dat_ini", "dat_rev", "rev_ind", "ciclo", "link"]}
        if not v["num"]: return messagebox.showwarning("Aviso", "Número obrigatório!")
        conn = database.connect_db(); cursor = conn.cursor()
        check_id = self.edit_id if self.edit_id else -1
        cursor.execute("SELECT id FROM pfmeas WHERE numero = ? AND id != ?", (v["num"], check_id))
        if cursor.fetchone():
            conn.close(); return messagebox.showerror("Erro", f"O número {v['num']} já pertence a outro documento!")
        if self.edit_id:
            if self.is_nova_revisao:
                cursor.execute("SELECT id FROM historico_pfmeas WHERE pfmea_id = ? AND (data_rev = ? OR indice_rev = ?)", (self.edit_id, v["dat_rev"], v["rev_ind"]))
                if cursor.fetchone():
                    conn.close(); return messagebox.showerror("Erro", "Data ou Revisão já existem.")
                cursor.execute("SELECT data_atual, revisao, link_documento FROM pfmeas WHERE id=?", (self.edit_id,))
                old = cursor.fetchone()
                if old: cursor.execute("INSERT INTO historico_pfmeas (pfmea_id, data_rev, indice_rev, link_rev) VALUES (?,?,?,?)", (self.edit_id, old[0], old[1], old[2]))
            cursor.execute("UPDATE pfmeas SET numero=?, descricao=?, cliente=?, data_inicial=?, data_atual=?, revisao=?, ciclo_revisao=?, link_documento=?, status=? WHERE id=?", 
                           (v["num"], v["desc"], v["cli"], v["dat_ini"], v["dat_rev"], v["rev_ind"], v["ciclo"], v["link"], self.combo_status.get(), self.edit_id))
        else:
            cursor.execute("INSERT INTO pfmeas (numero, descricao, cliente, data_inicial, data_atual, revisao, ciclo_revisao, link_documento, status) VALUES (?,?,?,?,?,?,?,?,?)", 
                           (v["num"], v["desc"], v["cli"], v["dat_ini"], v["dat_rev"], v["rev_ind"], v["ciclo"], v["link"], self.combo_status.get()))
        conn.commit(); conn.close(); self.reset_form(); self.load_pfmeas_list(); self.controller.aba_consultar.load_data()

    def preparar_edicao(self, row):
        self.set_fields_state("normal"); self.is_nova_revisao = False; self.edit_id = row[0]
        self.btn_save.configure(text="Salvar Alterações (Edit)", fg_color="#e67e22")
        self.entries["num"].delete(0, 'end'); self.entries["num"].insert(0, str(row[1]))
        self.entries["desc"].delete(0, 'end'); self.entries["desc"].insert(0, str(row[2]))
        self.entries["cli"].delete(0, 'end'); self.entries["cli"].insert(0, str(row[3]))
        self.entries["dat_ini"].delete(0, 'end'); self.entries["dat_ini"].insert(0, str(row[4]))
        self.entries["dat_rev"].delete(0, 'end'); self.entries["dat_rev"].insert(0, str(row[5]))
        self.entries["rev_ind"].delete(0, 'end'); self.entries["rev_ind"].insert(0, str(row[6]))
        self.combo_status.set(row[7]); self.entries["ciclo"].delete(0, 'end'); self.entries["ciclo"].insert(0, str(row[8]))
        self.entries["link"].delete(0, 'end'); self.entries["link"].insert(0, str(row[9]) if row[9] else "")

    def preparar_revisao_rapida(self, row):
        self.set_fields_state("normal"); self.is_nova_revisao = True; self.edit_id = row[0]
        self.btn_save.configure(text="Confirmar Nova Revisão", fg_color="#27ae60")
        self.entries["num"].delete(0, 'end'); self.entries["num"].insert(0, str(row[1]))
        self.entries["desc"].delete(0, 'end'); self.entries["desc"].insert(0, str(row[2]))
        self.entries["cli"].delete(0, 'end'); self.entries["cli"].insert(0, str(row[3]))
        self.entries["dat_ini"].delete(0, 'end'); self.entries["dat_ini"].insert(0, str(row[4]))
        self.entries["dat_rev"].delete(0, 'end'); self.entries["dat_rev"].insert(0, datetime.now().strftime("%d/%m/%Y"))
        self.entries["ciclo"].delete(0, 'end'); self.entries["ciclo"].insert(0, str(row[8]))
        self.entries["link"].delete(0, 'end'); self.entries["link"].insert(0, str(row[9]) if row[9] else "")
        rev_atual = str(row[6]); nums = re.findall(r'\d+', rev_atual)
        nova_rev = rev_atual.replace(nums[-1], str(int(nums[-1]) + 1)) if nums else rev_atual + " 1"
        self.entries["rev_ind"].delete(0, 'end'); self.entries["rev_ind"].insert(0, nova_rev)

    def reset_form(self):
        self.edit_id, self.is_nova_revisao = None, False
        self.btn_save.configure(text="Salvar PFMEA", fg_color="#1f538d")
        if hasattr(self, 'entries'):
            for k, widget in self.entries.items():
                if not k.endswith("_btn"): widget.configure(state="normal"); widget.delete(0, 'end')
        self.set_fields_state("disabled")

    def abrir_calendario(self, key):
        top = Toplevel(self.parent); top.geometry("300x400"); top.grab_set()
        cal = Calendar(top, selectmode='day', locale='pt_BR', date_pattern='dd/mm/yyyy'); cal.pack(fill="both", expand=True)
        customtkinter.CTkButton(top, text="Ok", command=lambda: [self.entries[key].delete(0, 'end'), self.entries[key].insert(0, cal.get_date()), top.destroy()]).pack()

    def deletar_rev(self, h_id):
        if messagebox.askyesno("Excluir", "Remover esta revisão?"):
            conn = database.connect_db(); cursor = conn.cursor(); cursor.execute("DELETE FROM historico_pfmeas WHERE id = ?", (h_id,))
            conn.commit(); conn.close(); self.load_pfmeas_list()

    def editar_link_h(self, h_id, l_atual):
        novo = simpledialog.askstring("Link", "Insira o novo link:", initialvalue=l_atual)
        if novo is not None:
            conn = database.connect_db(); cursor = conn.cursor(); cursor.execute("UPDATE historico_pfmeas SET link_rev = ? WHERE id = ?", (novo, h_id))
            conn.commit(); conn.close(); self.load_pfmeas_list()