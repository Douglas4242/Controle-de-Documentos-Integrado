import customtkinter
import database
from tkinter import messagebox, Toplevel, simpledialog
from tkcalendar import Calendar
from datetime import datetime
import re
import webbrowser

class AbaIT:
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
        
        self.pfmea_vars = {} 
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
            
            customtkinter.CTkLabel(self.left_col, text="🛠️ Gestão de IT", font=self.font_title).pack(pady=(15, 10))
            self.form_container = customtkinter.CTkScrollableFrame(self.left_col, fg_color="transparent")
            self.form_container.pack(fill="both", expand=True, padx=15)

            campos = [
                ("Número da IT:", "num", "Ex: IT-53.1"),
                ("Descrição da Operação:", "desc", "Ex: Montagem Manual"),
                ("Cliente / Linha:", "cli", "Ex: VW / Linha A"),
                ("Data da IT:", "dat", "DD/MM/AAAA"),
                ("Índice de Revisão:", "rev", "Ex: Rev. 01"),
                ("Link do Documento:", "link", "http://..."),
                ("Link do Treinamento:", "link_trein", "http://...")
            ]

            for label_text, key, placeholder in campos:
                customtkinter.CTkLabel(self.form_container, text=label_text, font=self.font_label).pack(anchor="w", pady=(8, 0))
                row_f = customtkinter.CTkFrame(self.form_container, fg_color="transparent")
                row_f.pack(fill="x", pady=2)
                entry = customtkinter.CTkEntry(row_f, placeholder_text=placeholder, height=35, font=self.font_entry)
                entry.pack(side="left", fill="x", expand=True)
                self.entries[key] = entry
                if "dat" in key:
                    btn_cal = customtkinter.CTkButton(row_f, text="📅", width=35, height=35, command=lambda k=key: self.abrir_calendario(k))
                    btn_cal.pack(side="right", padx=(5, 0))
                    self.entries[key+"_btn"] = btn_cal

            customtkinter.CTkLabel(self.form_container, text="Vincular a PFMEAs:", font=self.font_label).pack(anchor="w", pady=(10, 0))
            self.ent_filtro_pf = customtkinter.CTkEntry(self.form_container, placeholder_text="🔍 Filtrar PFMEAs...", height=30)
            self.ent_filtro_pf.pack(fill="x", pady=(5, 0))
            self.ent_filtro_pf.bind("<KeyRelease>", lambda e: self.carregar_checkbox_pfmeas())

            self.scroll_pfmeas = customtkinter.CTkScrollableFrame(self.form_container, height=150, fg_color="#1e1e1e")
            self.scroll_pfmeas.pack(fill="x", pady=5)
            self.carregar_checkbox_pfmeas()

            self.btn_novo = customtkinter.CTkButton(self.left_col, text="➕ Criar Nova IT", command=self.nova_it, height=40, font=self.font_button, fg_color="#2c3e50")
            self.btn_novo.pack(pady=(10, 0), padx=20, fill="x")
            self.btn_save = customtkinter.CTkButton(self.left_col, text="Salvar IT", command=self.save_it, height=45, font=self.font_button)
            self.btn_save.pack(pady=(10, 5), padx=20, fill="x")
            customtkinter.CTkButton(self.left_col, text="Cancelar / Limpar", command=self.reset_form, height=40, font=self.font_button, fg_color="#a83232").pack(padx=20, fill="x", pady=(0, 15))
            self.set_fields_state("disabled")

        self.right_col = customtkinter.CTkFrame(self.pane)
        self.right_col.pack(side="right", fill="both", expand=True, padx=(5, 10), pady=10)
        
        # --- FILTROS DA LISTA ---
        self.filter_f = customtkinter.CTkFrame(self.right_col, fg_color="transparent")
        self.filter_f.pack(fill="x", padx=15, pady=(15, 5))
        
        self.ent_busca = customtkinter.CTkEntry(self.filter_f, placeholder_text="🔍 Buscar IT/Desc...", height=35, width=150)
        self.ent_busca.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.ent_busca.bind("<KeyRelease>", lambda e: self.load_its_list())

        # Novo filtro por número de PFMEA
        self.ent_busca_pf_num = customtkinter.CTkEntry(self.filter_f, placeholder_text="📂 Nº PFMEA (ex: 53, 20)", height=35, width=160)
        self.ent_busca_pf_num.pack(side="left", padx=(0, 5))
        self.ent_busca_pf_num.bind("<KeyRelease>", lambda e: self.load_its_list())
        
        self.combo_filtro_cat = customtkinter.CTkOptionMenu(self.filter_f, values=["Todas Categ.", "Ativo", "Obsoleto", "⚠️ Revisar"], command=lambda e: self.load_its_list(), width=120)
        self.combo_filtro_cat.pack(side="left", padx=(0, 5))
        
        self.combo_ordem = customtkinter.CTkOptionMenu(self.filter_f, values=["Nº Documento", "Mais Novo", "Mais Antigo", "Cliente"], command=lambda e: self.load_its_list(), width=130)
        self.combo_ordem.pack(side="right")
        
        self.scroll = customtkinter.CTkScrollableFrame(self.right_col)
        self.scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.load_its_list()

    def carregar_checkbox_pfmeas(self):
        filtro = self.ent_filtro_pf.get().lower() if hasattr(self, 'ent_filtro_pf') else ""
        for w in self.scroll_pfmeas.winfo_children(): w.destroy()
        conn = database.connect_db(); cursor = conn.cursor()
        cursor.execute("SELECT id, numero, status FROM pfmeas ORDER BY CAST(numero AS INTEGER), numero")
        pfs = cursor.fetchall(); conn.close()
        for pf_id, num, status in pfs:
            if filtro in str(num).lower():
                if pf_id not in self.pfmea_vars: self.pfmea_vars[pf_id] = customtkinter.BooleanVar()
                cb = customtkinter.CTkCheckBox(self.scroll_pfmeas, text=f"PF: {num} ({status})", variable=self.pfmea_vars[pf_id], font=("Arial", 11))
                cb.pack(anchor="w", pady=2)

    def save_it(self):
        v = {k: self.entries[k].get() for k in ["num", "desc", "cli", "dat", "rev", "link", "link_trein"]}
        pf_selecionados = [pid for pid, var in self.pfmea_vars.items() if var.get()]
        if not v["num"] or not pf_selecionados: return messagebox.showwarning("Aviso", "Número e PFMEA são obrigatórios!")
        conn = database.connect_db(); cursor = conn.cursor()
        check_id = self.edit_id if self.edit_id else -1
        cursor.execute("SELECT id FROM its WHERE numero = ? AND id != ?", (v["num"], check_id))
        if cursor.fetchone(): conn.close(); return messagebox.showerror("Erro", f"A IT {v['num']} já existe!")

        cursor.execute(f"SELECT data_atual FROM pfmeas WHERE id IN ({','.join(['?']*len(pf_selecionados))})", pf_selecionados)
        datas_pais = [datetime.strptime(d[0], "%d/%m/%Y") for d in cursor.fetchall() if d[0]]
        if datas_pais:
            max_pai = max(datas_pais)
            try:
                if datetime.strptime(v["dat"], "%d/%m/%Y") < max_pai:
                    if not messagebox.askyesno("Aviso", f"Data IT ({v['dat']}) anterior ao PFMEA ({max_pai.strftime('%d/%m/%Y')}). Salvar?"):
                        conn.close(); return
            except: pass

        if self.edit_id:
            if self.is_nova_revisao:
                cursor.execute("SELECT data_atual, revisao_indice, link_documento, link_treinamento, treinamento_status FROM its WHERE id=?", (self.edit_id,))
                old = cursor.fetchone()
                cursor.execute("INSERT INTO historico_its (it_id, data_rev, indice_rev, link_rev, link_trein_rev, trein_status_rev) VALUES (?,?,?,?,?,?)", 
                               (self.edit_id, old[0], old[1], old[2], old[3], old[4]))
            cursor.execute("UPDATE its SET numero=?, descricao=?, cliente=?, data_atual=?, revisao_indice=?, link_documento=?, link_treinamento=? WHERE id=?", 
                           (v["num"], v["desc"], v["cli"], v["dat"], v["rev"], v["link"], v["link_trein"], self.edit_id))
            cursor.execute("DELETE FROM pfmea_it WHERE it_id = ?", (self.edit_id,))
        else:
            cursor.execute("INSERT INTO its (numero, descricao, cliente, data_atual, revisao_indice, link_documento, link_treinamento) VALUES (?,?,?,?,?,?,?)", 
                           (v["num"], v["desc"], v["cli"], v["dat"], v["rev"], v["link"], v["link_trein"]))
            self.edit_id = cursor.lastrowid

        for pid in pf_selecionados: cursor.execute("INSERT INTO pfmea_it (pfmea_id, it_id) VALUES (?,?)", (pid, self.edit_id))
        conn.commit(); conn.close(); self.reset_form(); self.load_its_list(); self.controller.aba_consultar.load_data()

    def load_its_list(self):
        for widget in self.scroll.winfo_children(): widget.destroy()
        termo, acesso = f"%{self.ent_busca.get()}%", self.controller.nivel_acesso
        ordem_sel, cat_sel = self.combo_ordem.get(), self.combo_filtro_cat.get()
        busca_pf_val = self.ent_busca_pf_num.get().replace(" ", "")
        
        ordem_sql = "i.numero ASC"
        if ordem_sel == "Mais Novo": ordem_sql = "substr(i.data_atual,7,4)||substr(i.data_atual,4,2)||substr(i.data_atual,1,2) DESC"
        elif ordem_sel == "Mais Antigo": ordem_sql = "substr(i.data_atual,7,4)||substr(i.data_atual,4,2)||substr(i.data_atual,1,2) ASC"
        elif ordem_sel == "Cliente": ordem_sql = "i.cliente ASC"

        params = [termo, termo]
        filtro_status_sql = ""
        
        if cat_sel == "Ativo":
            filtro_status_sql = " AND EXISTS (SELECT 1 FROM pfmeas f JOIN pfmea_it pi ON f.id = pi.pfmea_id WHERE pi.it_id = i.id AND f.status != 'Obsoleto')"
        elif cat_sel == "Obsoleto":
            filtro_status_sql = " AND NOT EXISTS (SELECT 1 FROM pfmeas f JOIN pfmea_it pi ON f.id = pi.pfmea_id WHERE pi.it_id = i.id AND f.status != 'Obsoleto')"
        elif cat_sel == "⚠️ Revisar":
            filtro_status_sql = """ 
                AND EXISTS (SELECT 1 FROM pfmeas f JOIN pfmea_it pi ON f.id = pi.pfmea_id WHERE pi.it_id = i.id AND f.status != 'Obsoleto')
                AND (SELECT MAX(substr(f.data_atual,7,4)||substr(f.data_atual,4,2)||substr(f.data_atual,1,2)) FROM pfmeas f JOIN pfmea_it pi ON f.id = pi.pfmea_id WHERE pi.it_id = i.id) > (substr(i.data_atual,7,4)||substr(i.data_atual,4,2)||substr(i.data_atual,1,2))
            """

        # Filtro de múltiplos números de PFMEA
        filtro_pf_num_sql = ""
        if busca_pf_val:
            lista_pfs = busca_pf_val.split(",")
            placeholders = ",".join(["?"] * len(lista_pfs))
            filtro_pf_num_sql = f" AND EXISTS (SELECT 1 FROM pfmeas f JOIN pfmea_it pi ON f.id = pi.pfmea_id WHERE pi.it_id = i.id AND f.numero IN ({placeholders}))"
            params.extend(lista_pfs)

        if cat_sel in ["Ativo", "Obsoleto"]: # Apenas se a query precisar do parâmetro
            pass # Nesses casos a lógica é interna à subconsulta

        conn = database.connect_db(); cursor = conn.cursor()
        query = f"""
            SELECT i.id, i.numero, i.descricao, i.cliente, i.data_atual, i.revisao_indice, i.link_treinamento,
            (SELECT GROUP_CONCAT(f.status) FROM pfmeas f JOIN pfmea_it pi ON f.id = pi.pfmea_id WHERE pi.it_id = i.id) as st_pais,
            (SELECT MAX(substr(f.data_atual,7,4)||substr(f.data_atual,4,2)||substr(f.data_atual,1,2)) FROM pfmeas f JOIN pfmea_it pi ON f.id = pi.pfmea_id WHERE pi.it_id = i.id) as dt_pai_iso,
            i.link_documento, i.treinamento_status
            FROM its i WHERE (i.numero LIKE ? OR i.descricao LIKE ?){filtro_status_sql}{filtro_pf_num_sql} ORDER BY {ordem_sql}
        """
        
        cursor.execute(query, params)
        for row in cursor.fetchall():
            it_id, it_num, it_desc, it_cli, it_data, it_rev, it_link_t, st_pais, dt_pai_iso, it_link_doc, it_t_status = row
            lista_st = st_pais.split(",") if st_pais else []
            todos_obs = all(s == "Obsoleto" for s in lista_st) if lista_st else False
            cor_card, cor_borda = ("#2d3436", "#0984e3")
            if todos_obs: cor_card, cor_borda = "#1e1e1e", "#3d3d3d"
            tag_rev = ""
            if not todos_obs and dt_pai_iso and it_data:
                it_iso = it_data[6:10] + it_data[3:5] + it_data[0:2]
                if it_iso < dt_pai_iso: tag_rev = "  ⚠️ REVISAR"; cor_borda = "#a83232"

            f_item = customtkinter.CTkFrame(self.scroll, fg_color=cor_card, border_width=2, border_color=cor_borda); f_item.pack(fill="x", pady=4, padx=5)
            f_res = customtkinter.CTkFrame(f_item, fg_color="transparent"); f_res.pack(fill="x", padx=12, pady=10)
            t_cor = "#2ecc71" if (it_link_t or it_t_status == 1) else "#e74c3c"
            customtkinter.CTkLabel(f_res, text="●", text_color=t_cor, font=("Arial", 18)).pack(side="left", padx=(0, 5))
            customtkinter.CTkLabel(f_res, text=f"IT: {it_num} | Rev: {it_rev} | {it_data}{tag_rev}", font=self.font_lista_bold).pack(side="left")
            
            if acesso == "engenharia":
                customtkinter.CTkButton(f_res, text="⚙️ Editar", width=75, height=28, command=lambda r=row: self.preparar_edicao(r)).pack(side="right", padx=2)
                if not todos_obs: customtkinter.CTkButton(f_res, text="♻️ Rev", width=65, height=28, fg_color="#27ae60", command=lambda r=row: self.preparar_revisao_rapida(r)).pack(side="right", padx=2)
            if it_link_t: customtkinter.CTkButton(f_res, text="🎓 Reg.", width=75, height=28, fg_color="#34495e", command=lambda l=it_link_t: webbrowser.open(l)).pack(side="right", padx=2)
            if it_link_doc: customtkinter.CTkButton(f_res, text="🔗 link", width=65, height=28, fg_color="#34495e", command=lambda l=it_link_doc: webbrowser.open(l)).pack(side="right", padx=2)
            customtkinter.CTkButton(f_res, text="📂 Detalhes", width=85, height=28, fg_color="#3d3d3d", command=lambda f=f_item, pid=it_id, r=row: self.mostrar_detalhes_it(f, pid, r)).pack(side="right", padx=2)
            
            f_l2 = customtkinter.CTkFrame(f_item, fg_color="transparent"); f_l2.pack(fill="x", padx=12, pady=(0, 10))
            customtkinter.CTkLabel(f_l2, text=f"Desc: {it_desc} | Cliente: {it_cli}", font=self.font_lista_small, text_color="#bdc3c7").pack(side="left", padx=22)
        conn.close()

    def mostrar_detalhes_it(self, container, it_id, row):
        if len(container.winfo_children()) > 2: container.winfo_children()[2].destroy(); return
        det = customtkinter.CTkFrame(container, fg_color="#181818"); det.pack(fill="x", padx=10, pady=(0, 10))
        acesso, conn = self.controller.nivel_acesso, database.connect_db(); cursor = conn.cursor()
        t_info = "TREINAMENTO OK" if (row[6] or row[10] == 1) else "TREINAMENTO PENDENTE"
        t_cor = "#2ecc71" if t_info == "TREINAMENTO OK" else "#e74c3c"
        customtkinter.CTkLabel(det, text=f"🎓 Status: {t_info}", text_color=t_cor, font=("Arial", 12, "bold")).pack(anchor="w", padx=20, pady=5)
        customtkinter.CTkLabel(det, text="📑 PFMEAs Vinculados:", text_color="#3498db", font=("Arial", 12, "bold")).pack(anchor="w", padx=20, pady=5)
        cursor.execute("SELECT f.numero, f.status, f.data_atual FROM pfmeas f JOIN pfmea_it pi ON f.id = pi.pfmea_id WHERE pi.it_id = ?", (it_id,))
        for p_num, p_st, p_dt in cursor.fetchall():
            it_iso = row[4][6:10] + row[4][3:5] + row[4][0:2]
            p_iso = p_dt[6:10] + p_dt[3:5] + p_dt[0:2]
            p_cor = "#2ecc71" if it_iso >= p_iso else "#e74c3c"
            f_pf = customtkinter.CTkFrame(det, fg_color="transparent"); f_pf.pack(anchor="w", padx=30)
            customtkinter.CTkLabel(f_pf, text="●", text_color=p_cor, font=("Arial", 16)).pack(side="left")
            customtkinter.CTkLabel(f_pf, text=f" PF: {p_num} ({p_st})", text_color="#777").pack(side="left")
        customtkinter.CTkLabel(det, text="📦 Peças (PNs):", text_color="#3498db", font=("Arial", 12, "bold")).pack(anchor="w", padx=20, pady=5)
        cursor.execute("SELECT codigo FROM pns WHERE it_id = ?", (it_id,))
        for pn in cursor.fetchall(): customtkinter.CTkLabel(det, text=f"   └─ PN: {pn[0]}").pack(anchor="w", padx=20)
        f_hist_h = customtkinter.CTkFrame(det, fg_color="transparent"); f_hist_h.pack(fill="x", padx=20, pady=10)
        customtkinter.CTkLabel(f_hist_h, text="📜 Histórico:", text_color="#2ecc71", font=("Arial", 12, "bold")).pack(side="left")
        f_itens = customtkinter.CTkFrame(det, fg_color="transparent")
        def toggle(): 
            if f_itens.winfo_viewable(): f_itens.pack_forget(); btn.configure(text="▼")
            else: f_itens.pack(fill="x", padx=20); btn.configure(text="▲")
        btn = customtkinter.CTkButton(f_hist_h, text="▼", width=30, height=20, fg_color="#2ecc71", text_color="black", command=toggle)
        btn.pack(side="left", padx=10)
        cursor.execute("SELECT id, data_rev, indice_rev, link_rev, link_trein_rev, trein_status_rev FROM historico_its WHERE it_id = ? ORDER BY id DESC", (it_id,))
        for h_id, d, i, l, lt, ts in cursor.fetchall():
            h_row = customtkinter.CTkFrame(f_itens, fg_color="transparent"); h_row.pack(fill="x", pady=2)
            t_cor_h = "#2ecc71" if (lt or ts == 1) else "#e74c3c"
            customtkinter.CTkLabel(h_row, text="●", text_color=t_cor_h, font=("Arial", 14)).pack(side="left", padx=5)
            customtkinter.CTkLabel(h_row, text=f"Rev: {i} - {d}", font=self.font_hist).pack(side="left")
            if acesso == "engenharia":
                customtkinter.CTkButton(h_row, text="🗑", width=35, height=25, fg_color="#c0392b", command=lambda hid=h_id: self.deletar_rev(hid)).pack(side="right", padx=2)
                customtkinter.CTkButton(h_row, text="✎", width=35, height=25, fg_color="#d35400", command=lambda hid=h_id, doc=l, tr=lt: self.editar_link_h_it(hid, doc, tr)).pack(side="right", padx=2)
                if not lt and ts == 0: customtkinter.CTkButton(h_row, text="✅", width=35, height=25, fg_color="#27ae60", command=lambda hid=h_id: self.flag_treinamento_ok(hid)).pack(side="right", padx=2)
            if lt: customtkinter.CTkButton(h_row, text="🎓", width=35, height=25, fg_color="#34495e", command=lambda url=lt: webbrowser.open(url)).pack(side="right", padx=2)
            if l: customtkinter.CTkButton(h_row, text="🔗", width=35, height=25, fg_color="#2980b9", command=lambda url=l: webbrowser.open(url)).pack(side="right", padx=2)
        conn.close()

    def flag_treinamento_ok(self, h_id):
        if messagebox.askyesno("Treinamento", "Marcar treinamento como concluído?"):
            conn = database.connect_db(); cursor = conn.cursor()
            cursor.execute("UPDATE historico_its SET trein_status_rev = 1 WHERE id = ?", (h_id,))
            conn.commit(); conn.close(); self.load_its_list()

    def editar_link_h_it(self, h_id, doc_at, tr_at):
        dialog = customtkinter.CTkToplevel(self.parent); dialog.title("Editar Links"); dialog.geometry("450x250"); dialog.grab_set(); dialog.attributes("-topmost", True)
        customtkinter.CTkLabel(dialog, text="Link do Documento:", font=self.font_label).pack(pady=(20, 0))
        ent_doc = customtkinter.CTkEntry(dialog, width=400); ent_doc.insert(0, doc_at if doc_at else ""); ent_doc.pack(pady=5)
        customtkinter.CTkLabel(dialog, text="Link do Treinamento:", font=self.font_label).pack(pady=(10, 0))
        ent_tr = customtkinter.CTkEntry(dialog, width=400); ent_tr.insert(0, tr_at if tr_at else ""); ent_tr.pack(pady=5)
        def salvar():
            conn = database.connect_db(); cursor = conn.cursor()
            cursor.execute("UPDATE historico_its SET link_rev = ?, link_trein_rev = ? WHERE id = ?", (ent_doc.get(), ent_tr.get(), h_id))
            conn.commit(); conn.close(); dialog.destroy(); self.load_its_list()
        customtkinter.CTkButton(dialog, text="Salvar Alterações", command=salvar).pack(pady=20)

    def preparar_edicao(self, r):
        self.set_fields_state("normal"); self.edit_id, self.is_nova_revisao = r[0], False
        self.btn_save.configure(text="Salvar Alterações (Edit)", fg_color="#e67e22")
        for i, k in enumerate(["num", "desc", "cli", "dat", "rev"]):
            self.entries[k].delete(0, 'end'); self.entries[k].insert(0, str(r[i+1]))
        self.entries["link"].delete(0, 'end'); self.entries["link"].insert(0, str(r[9]) if r[9] else "")
        self.entries["link_trein"].delete(0, 'end'); self.entries["link_trein"].insert(0, str(r[6]) if r[6] else "")
        conn = database.connect_db(); cursor = conn.cursor()
        cursor.execute("SELECT pfmea_id FROM pfmea_it WHERE it_id = ?", (r[0],))
        vinc = [x[0] for x in cursor.fetchall()]; conn.close()
        for pid, var in self.pfmea_vars.items(): var.set(pid in vinc)
        self.carregar_checkbox_pfmeas()

    def preparar_revisao_rapida(self, r):
        self.set_fields_state("normal"); self.edit_id, self.is_nova_revisao = r[0], True
        self.btn_save.configure(text="Confirmar Nova Revisão", fg_color="#27ae60")
        for i, k in enumerate(["num", "desc", "cli"]):
            self.entries[k].delete(0, 'end'); self.entries[k].insert(0, str(r[i+1]))
        self.entries["dat"].delete(0, 'end'); self.entries["dat"].insert(0, datetime.now().strftime("%d/%m/%Y"))
        rev_at = str(r[5]); nums = re.findall(r'\d+', rev_at)
        self.entries["rev"].delete(0, 'end'); self.entries["rev"].insert(0, rev_at.replace(nums[-1], str(int(nums[-1]) + 1)) if nums else rev_at + " 1")
        conn = database.connect_db(); cursor = conn.cursor()
        cursor.execute("SELECT pfmea_id FROM pfmea_it WHERE it_id = ?", (r[0],))
        vinc = [x[0] for x in cursor.fetchall()]; conn.close()
        for pid, var in self.pfmea_vars.items(): var.set(pid in vinc)
        self.carregar_checkbox_pfmeas()

    def nova_it(self): self.reset_form(); self.set_fields_state("normal"); self.entries["num"].focus()
    def reset_form(self):
        self.edit_id, self.is_nova_revisao = None, False
        self.btn_save.configure(text="Salvar IT", fg_color="#1f538d")
        if hasattr(self, 'entries'):
            for e in self.entries.values(): 
                if hasattr(e, 'delete'): e.configure(state="normal"); e.delete(0, 'end')
        for v in self.pfmea_vars.values(): v.set(False)
        self.set_fields_state("disabled")

    def set_fields_state(self, st):
        if hasattr(self, 'entries'):
            for k, w in self.entries.items(): w.configure(state=st)
            self.btn_save.configure(state=st)

    def abrir_calendario(self, key):
        top = Toplevel(self.parent); top.geometry("300x400"); top.grab_set()
        cal = Calendar(top, selectmode='day', locale='pt_BR', date_pattern='dd/mm/yyyy'); cal.pack(fill="both", expand=True)
        customtkinter.CTkButton(top, text="Ok", command=lambda: [self.entries[key].delete(0, 'end'), self.entries[key].insert(0, cal.get_date()), top.destroy()]).pack()

    def deletar_rev(self, hid):
        if messagebox.askyesno("Excluir", "Remover histórico?"):
            conn = database.connect_db(); cursor = conn.cursor(); cursor.execute("DELETE FROM historico_its WHERE id=?", (hid,))
            conn.commit(); conn.close(); self.load_its_list()