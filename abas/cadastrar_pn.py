import customtkinter
import database
import webbrowser
from tkinter import messagebox

class AbaPN:
    def __init__(self, parent, controller):
        self.parent = parent
        self.controller = controller
        self.edit_id = None
        
        self.font_title = ("Arial", 18, "bold")
        self.font_label = ("Arial", 13, "bold")
        self.font_entry = ("Arial", 13)
        self.font_button = ("Arial", 13, "bold")
        self.font_lista_bold = ("Arial", 15, "bold")
        self.font_lista_small = ("Arial", 13, "italic")
        
        self.setup_ui()

    def setup_ui(self):
        for widget in self.parent.winfo_children(): widget.destroy()
        self.pane = customtkinter.CTkFrame(self.parent, fg_color="transparent")
        self.pane.pack(fill="both", expand=True)

        acesso = self.controller.nivel_acesso
        self.entries = {}

        if acesso == "engenharia":
            self.left_col = customtkinter.CTkFrame(self.pane, width=380)
            self.left_col.pack(side="left", fill="both", padx=(10, 5), pady=10)
            self.left_col.pack_propagate(False) 
            
            customtkinter.CTkLabel(self.left_col, text="📦 Gestão Técnica de PN", font=self.font_title).pack(pady=(15, 10))
            self.form_container = customtkinter.CTkScrollableFrame(self.left_col, fg_color="transparent")
            self.form_container.pack(fill="both", expand=True, padx=15)

            campos = [
                ("Código do PN:", "cod", "Ex: 123456-A"),
                ("Descrição da Peça:", "desc", "Ex: Suporte de Bateria"),
                ("Cliente / Linha:", "cli", "Ex: VW / Linha 01"),
                ("Nome do Projeto:", "proj", "Ex: Tiger 2026"),
                ("Nº do Desenho:", "des_num", "Ex: DES-9988"),
                ("Rev. do Desenho:", "des_rev", "Ex: A02"),
                ("Link do Desenho:", "link_des", "http://..."),
                ("Característica 1:", "obs1", "Ex: Cor do Tecido"),
                ("Característica 2:", "obs2", "Ex: Tipo de Trama"),
                ("Característica 3:", "obs3", "Ex: Fornecedor Base")
            ]

            for label_text, key, placeholder in campos:
                customtkinter.CTkLabel(self.form_container, text=label_text, font=self.font_label).pack(anchor="w", pady=(8, 0))
                entry = customtkinter.CTkEntry(self.form_container, placeholder_text=placeholder, height=35, font=self.font_entry)
                entry.pack(fill="x", pady=2)
                self.entries[key] = entry

            customtkinter.CTkLabel(self.form_container, text="Status do PN:", font=self.font_label).pack(anchor="w", pady=(8, 0))
            self.combo_status = customtkinter.CTkOptionMenu(self.form_container, values=["Ativo", "Obsoleto", "Protótipo"], height=35)
            self.combo_status.pack(fill="x", pady=2)

            customtkinter.CTkLabel(self.form_container, text="Vincular à IT Pai:", font=self.font_label).pack(anchor="w", pady=(10, 0))
            self.ent_filtro_it_form = customtkinter.CTkEntry(self.form_container, placeholder_text="🔍 Filtrar ITs...", height=30)
            self.ent_filtro_it_form.pack(fill="x", pady=(5, 0))
            self.ent_filtro_it_form.bind("<KeyRelease>", lambda e: self.carregar_opcoes_it())

            self.scroll_its_form = customtkinter.CTkScrollableFrame(self.form_container, height=150, fg_color="#1e1e1e")
            self.scroll_its_form.pack(fill="x", pady=5)
            self.it_pai_var = customtkinter.IntVar(value=0)
            self.carregar_opcoes_it()

            self.btn_novo = customtkinter.CTkButton(self.left_col, text="➕ Novo PN", command=self.novo_pn, height=40, font=self.font_button, fg_color="#2c3e50")
            self.btn_novo.pack(pady=(10, 0), padx=20, fill="x")

            self.btn_save = customtkinter.CTkButton(self.left_col, text="Salvar PN", command=self.save_pn, height=45, font=self.font_button)
            self.btn_save.pack(pady=(10, 5), padx=20, fill="x")
            customtkinter.CTkButton(self.left_col, text="Cancelar", command=self.reset_form, height=40, font=self.font_button, fg_color="#a83232").pack(padx=20, fill="x", pady=(0, 15))
            self.set_fields_state("disabled")

        self.right_col = customtkinter.CTkFrame(self.pane)
        self.right_col.pack(side="right", fill="both", expand=True, padx=(5, 10), pady=10)
        
        self.filter_f = customtkinter.CTkFrame(self.right_col, fg_color="transparent"); self.filter_f.pack(fill="x", padx=15, pady=(15, 5))
        self.ent_busca_pn = customtkinter.CTkEntry(self.filter_f, placeholder_text="🔍 Buscar PN, Desc ou Projeto...", height=35)
        self.ent_busca_pn.pack(side="left", fill="x", expand=True, padx=(0, 5)); self.ent_busca_pn.bind("<KeyRelease>", lambda e: self.load_pns_list())
        
        self.combo_filtro_cat = customtkinter.CTkOptionMenu(self.filter_f, values=["Todas Categ.", "Ativo", "Obsoleto", "Protótipo"], command=lambda e: self.load_pns_list(), width=130)
        self.combo_filtro_cat.pack(side="left", padx=(0, 5))

        self.combo_filtro_it = customtkinter.CTkOptionMenu(self.filter_f, values=["Todas ITs"], command=lambda e: self.load_pns_list(), width=130)
        self.combo_filtro_it.pack(side="left", padx=(0, 5)); self.atualizar_filtro_it_combobox()

        self.scroll = customtkinter.CTkScrollableFrame(self.right_col); self.scroll.pack(fill="both", expand=True, padx=10, pady=10)
        self.load_pns_list()

    def carregar_opcoes_it(self):
        filtro = self.ent_filtro_it_form.get().lower()
        for w in self.scroll_its_form.winfo_children(): w.destroy()
        conn = database.connect_db(); cursor = conn.cursor()
        cursor.execute("SELECT id, numero, descricao FROM its ORDER BY numero ASC")
        for it_id, it_num, it_desc in cursor.fetchall():
            if filtro in str(it_num).lower() or filtro in str(it_desc).lower():
                customtkinter.CTkRadioButton(self.scroll_its_form, text=f"IT: {it_num} - {it_desc}", variable=self.it_pai_var, value=it_id, font=("Arial", 11)).pack(anchor="w", pady=2)
        conn.close()

    def atualizar_filtro_it_combobox(self):
        conn = database.connect_db(); cursor = conn.cursor()
        cursor.execute("SELECT numero FROM its ORDER BY numero ASC")
        its = [row[0] for row in cursor.fetchall()]; conn.close()
        self.combo_filtro_it.configure(values=["Todas ITs"] + its)

    def load_pns_list(self):
        for widget in self.scroll.winfo_children(): widget.destroy()
        termo, it_filtro, cat_sel = f"%{self.ent_busca_pn.get()}%", self.combo_filtro_it.get(), self.combo_filtro_cat.get()
        acesso = self.controller.nivel_acesso
        
        filtro_sql = " AND i.numero = ?" if it_filtro != "Todas ITs" else ""
        if cat_sel != "Todas Categ.": filtro_sql += " AND p.status = ?"

        conn = database.connect_db(); cursor = conn.cursor()
        query = f"""SELECT p.id, p.codigo, p.descricao, p.cliente, i.numero, i.descricao, p.projeto, 
                          p.desenho_num, p.desenho_rev, p.link_desenho, i.link_documento, p.it_id,
                          i.status, p.status, p.obs1, p.obs2, p.obs3
                   FROM pns p JOIN its i ON p.it_id = i.id 
                   WHERE (p.codigo LIKE ? OR p.descricao LIKE ? OR p.projeto LIKE ?) {filtro_sql} ORDER BY p.codigo ASC"""
        
        params = [termo, termo, termo]
        if it_filtro != "Todas ITs": params.append(it_filtro)
        if cat_sel != "Todas Categ.": params.append(cat_sel)

        cursor.execute(query, params)
        for row in cursor.fetchall():
            pn_id, pn_cod, pn_desc, pn_cli, it_num, it_desc_full, proj, des_num, des_rev, link_des, link_it, it_id_pai, it_st, pn_st, o1, o2, o3 = row
            
            cor_card, cor_borda = ("#2d3436", "#0984e3")
            if it_st == "Obsoleto" or pn_st == "Obsoleto": cor_card, cor_borda = "#1e1e1e", "#3d3d3d"
            elif pn_st == "Protótipo": cor_borda = "#27ae60"

            f_item = customtkinter.CTkFrame(self.scroll, fg_color=cor_card, border_width=2, border_color=cor_borda); f_item.pack(fill="x", pady=4, padx=5)
            f_res = customtkinter.CTkFrame(f_item, fg_color="transparent"); f_res.pack(fill="x", padx=12, pady=10)
            
            customtkinter.CTkLabel(f_res, text=f"📦 PN: {pn_cod} | {pn_desc}", font=self.font_lista_bold).pack(side="left")
            
            if acesso == "engenharia":
                customtkinter.CTkButton(f_res, text="⚙️", width=35, height=28, command=lambda r=row: self.preparar_edicao(r)).pack(side="right", padx=2)
                customtkinter.CTkButton(f_res, text="🗑️ Excluir", width=90, height=28, fg_color="#c0392b", command=lambda pid=pn_id, c=pn_cod: self.deletar_pn(pid, c)).pack(side="right", padx=2)
            
            customtkinter.CTkButton(f_res, text="📂 Detalhes", width=85, height=28, fg_color="#3d3d3d", command=lambda f=f_item, r=row: self.mostrar_detalhes_pn(f, r)).pack(side="right", padx=2)
            
            f_l2 = customtkinter.CTkFrame(f_item, fg_color="transparent"); f_l2.pack(fill="x", padx=12, pady=(0, 10))
            txt_l2 = f"Projeto: {proj if proj else '---'} | Cliente: {pn_cli} | IT: {it_num}"
            customtkinter.CTkLabel(f_l2, text=txt_l2, font=self.font_lista_small, text_color="#bdc3c7").pack(side="left", padx=22)
        conn.close()

    def mostrar_detalhes_pn(self, container, r):
        if len(container.winfo_children()) > 2: container.winfo_children()[2].destroy(); return
        det = customtkinter.CTkFrame(container, fg_color="#181818"); det.pack(fill="x", padx=10, pady=(0, 10))
        
        if r[14] or r[15] or r[16]:
            customtkinter.CTkLabel(det, text="📝 Características Técnicas:", font=("Arial", 13, "bold"), text_color="#aaa").pack(anchor="w", padx=20, pady=(10,5))
            if r[14]: customtkinter.CTkLabel(det, text=f"   • {r[14]}", font=("Arial", 13)).pack(anchor="w", padx=25)
            if r[15]: customtkinter.CTkLabel(det, text=f"   • {r[15]}", font=("Arial", 13)).pack(anchor="w", padx=25)
            if r[16]: customtkinter.CTkLabel(det, text=f"   • {r[16]}", font=("Arial", 13)).pack(anchor="w", padx=25)

        f_top = customtkinter.CTkFrame(det, fg_color="transparent"); f_top.pack(fill="x", padx=20, pady=(15, 5))
        customtkinter.CTkLabel(f_top, text=f"📄 Instrução: {r[4]} - {r[5]}", font=("Arial", 13, "bold"), text_color="#2ecc71").pack(anchor="w")
        if r[10]: customtkinter.CTkButton(f_top, text="🔗 Abrir IT", width=130, height=25, fg_color="#2980b9", font=("Arial", 12, "bold"), command=lambda l=r[10]: webbrowser.open(l)).pack(anchor="w", pady=5, padx=15)

        customtkinter.CTkLabel(det, text=f"📐 Desenho: {r[7] if r[7] else '---'} | Rev: {r[8] if r[8] else '---'}", font=("Arial", 13, "bold"), text_color="#3498db").pack(anchor="w", padx=20, pady=(15,0))
        if r[9]: customtkinter.CTkButton(det, text="🎨 Abrir Desenho", width=130, height=25, fg_color="#d35400", font=("Arial", 12, "bold"), command=lambda l=r[9]: webbrowser.open(l)).pack(anchor="w", pady=5, padx=35)

    def preparar_edicao(self, r):
        self.set_fields_state("normal"); self.edit_id = r[0]
        self.btn_save.configure(text="Salvar Alterações", fg_color="#e67e22")
        campos = ["cod", "desc", "cli", "proj", "des_num", "des_rev", "link_des", "obs1", "obs2", "obs3"]
        indices = [1, 2, 3, 6, 7, 8, 9, 14, 15, 16]
        for i, key in enumerate(campos):
            self.entries[key].delete(0, 'end'); self.entries[key].insert(0, str(r[indices[i]]) if r[indices[i]] else "")
        self.it_pai_var.set(r[11]); self.combo_status.set(r[13]); self.carregar_opcoes_it()

    def save_pn(self):
        v = {k: self.entries[k].get() for k in self.entries}
        it_pai, status_pn = self.it_pai_var.get(), self.combo_status.get()
        if not v["cod"] or it_pai == 0: return messagebox.showwarning("Aviso", "Código e IT são obrigatórios!")
        
        conn = database.connect_db(); cursor = conn.cursor()
        
        # --- CORREÇÃO DOS PLACEHOLDERS (12 COLUNAS = 12 ?) ---
        if self.edit_id:
            cursor.execute("""UPDATE pns SET codigo=?, descricao=?, cliente=?, it_id=?, projeto=?, desenho_num=?, 
                              desenho_rev=?, link_desenho=?, status=?, obs1=?, obs2=?, obs3=? WHERE id=?""", 
                           (v["cod"], v["desc"], v["cli"], it_pai, v["proj"], v["des_num"], v["des_rev"], v["link_des"], status_pn, v["obs1"], v["obs2"], v["obs3"], self.edit_id))
        else:
            cursor.execute("""INSERT INTO pns (codigo, descricao, cliente, it_id, projeto, desenho_num, desenho_rev, 
                              link_desenho, status, obs1, obs2, obs3) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""", 
                           (v["cod"], v["desc"], v["cli"], it_pai, v["proj"], v["des_num"], v["des_rev"], v["link_des"], status_pn, v["obs1"], v["obs2"], v["obs3"]))
        
        conn.commit(); conn.close(); self.reset_form(); self.load_pns_list()

    def deletar_pn(self, pid, pn_cod):
        if messagebox.askyesno("Excluir", f"Deseja remover o PN {pn_cod}?"):
            conn = database.connect_db(); cursor = conn.cursor()
            cursor.execute("DELETE FROM pns WHERE id = ?", (pid,))
            conn.commit(); conn.close(); self.load_pns_list()

    def reset_form(self):
        self.edit_id = None
        if hasattr(self, 'btn_save'): self.btn_save.configure(text="Salvar PN", fg_color="#1f538d")
        for e in self.entries.values(): e.configure(state="normal"); e.delete(0, 'end')
        self.it_pai_var.set(0); self.combo_status.set("Ativo"); self.set_fields_state("disabled")

    def novo_pn(self): self.reset_form(); self.set_fields_state("normal"); self.entries["cod"].focus()

    def set_fields_state(self, st):
        if hasattr(self, 'entries'):
            for k, w in self.entries.items(): w.configure(state=st)
            self.combo_status.configure(state=st)
        if hasattr(self, 'btn_save'): self.btn_save.configure(state=st)