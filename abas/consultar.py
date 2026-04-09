import customtkinter
import database
import webbrowser
from datetime import datetime

class AbaConsultar:
    def __init__(self, parent, controller):
        self.parent = parent
        self.controller = controller
        
        # Estilos de fonte
        self.font_card_value = ("Arial", 22, "bold")
        self.font_sec_title = ("Arial", 14, "bold")
        self.font_item = ("Arial", 13)
        self.font_impact = ("Arial", 11, "italic")
        
        self.setup_ui()

    def setup_ui(self):
        for widget in self.parent.winfo_children(): widget.destroy()
        
        # Scroll principal da página
        self.main_scroll = customtkinter.CTkScrollableFrame(self.parent, fg_color="transparent")
        self.main_scroll.pack(fill="both", expand=True, padx=10, pady=10)

        # --- KPIs INDICADORES (Organizados em 2 linhas) ---
        self.frame_kpi = customtkinter.CTkFrame(self.main_scroll, fg_color="transparent")
        self.frame_kpi.pack(fill="x", pady=(0, 20))
        
        # --- GRID DE SEÇÕES (2x2 - Tamanho Fixo) ---
        self.grid_container = customtkinter.CTkFrame(self.main_scroll, fg_color="transparent")
        self.grid_container.pack(fill="both", expand=True)
        self.grid_container.grid_columnconfigure((0, 1), weight=1)

        self.load_data()

    def navegar(self, nome_aba):
        try: self.controller.tabview.set(nome_aba)
        except: pass

    def load_data(self):
        for w in self.frame_kpi.winfo_children(): w.destroy()
        for w in self.grid_container.winfo_children(): w.destroy()

        conn = database.connect_db(); cursor = conn.cursor()

        # 1. Contagens Base (Ativos)
        cursor.execute("SELECT COUNT(*) FROM pns WHERE status = 'Ativo'")
        cpn = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM pfmeas WHERE status = 'Ativo'")
        cpf = cursor.fetchone()[0]
        cursor.execute("""SELECT COUNT(*) FROM its i WHERE EXISTS 
                          (SELECT 1 FROM pfmeas f JOIN pfmea_it pi ON f.id = pi.pfmea_id 
                           WHERE pi.it_id = i.id AND f.status != 'Obsoleto')""")
        cit = cursor.fetchone()[0]

        # 2. Pendências
        cursor.execute("""SELECT COUNT(*) FROM its i WHERE (link_treinamento IS NULL OR link_treinamento = '') 
                          AND (treinamento_status = 0 OR treinamento_status = '0')
                          AND EXISTS (SELECT 1 FROM pfmeas f JOIN pfmea_it pi ON f.id = pi.pfmea_id WHERE pi.it_id = i.id AND f.status != 'Obsoleto')""")
        ctrein = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM its WHERE (link_documento IS NULL OR link_documento = '') AND status != 'Obsoleto'")
        cdoc = cursor.fetchone()[0]

        # 3. Atrasados
        cursor.execute("""SELECT COUNT(*) FROM its i WHERE EXISTS 
                          (SELECT 1 FROM pfmeas f JOIN pfmea_it pi ON f.id = pi.pfmea_id WHERE pi.it_id = i.id AND f.status != 'Obsoleto')
                          AND (SELECT MAX(substr(f.data_atual,7,4)||substr(f.data_atual,4,2)||substr(f.data_atual,1,2)) FROM pfmeas f JOIN pfmea_it pi ON f.id = pi.pfmea_id WHERE pi.it_id = i.id) 
                          > (substr(i.data_atual,7,4)||substr(i.data_atual,4,2)||substr(i.data_atual,1,2))""")
        atraso_it = cursor.fetchone()[0]
        
        atraso_pf = 0
        cursor.execute("SELECT data_atual, ciclo_revisao FROM pfmeas WHERE status = 'Ativo'")
        for dt, ciclo in cursor.fetchall():
            if self.calcular_dias(dt, ciclo) < 0: atraso_pf += 1

        # --- LINHA 1 INDICADORES: ATIVOS (AZUL) ---
        self.criar_card_kpi(self.frame_kpi, "PNs ATIVOS", cpn, "#1f538d", 0, 0, "📦 Controle de PNs")
        self.criar_card_kpi(self.frame_kpi, "ITs ATIVAS", cit, "#1f538d", 0, 1, "⚙️ Controle de ITs")
        self.criar_card_kpi(self.frame_kpi, "PFMEAs ATIVOS", cpf, "#1f538d", 0, 2, "📄 Controle de PFMEA")

        # --- LINHA 2 INDICADORES: PENDENTES (CORES DAS SEÇÕES) ---
        self.criar_card_kpi(self.frame_kpi, "PFMEAs ATRASADOS", atraso_pf, "#c0392b", 1, 0, "📄 Controle de PFMEA")
        self.criar_card_kpi(self.frame_kpi, "ITs ATRASADAS", atraso_it, "#c0392b", 1, 1, "⚙️ Controle de ITs")
        self.criar_card_kpi(self.frame_kpi, "TREINAMENTOS PENDENTES", ctrein, "#e67e22", 1, 2, "⚙️ Controle de ITs")
        self.criar_card_kpi(self.frame_kpi, "PENDENTE DOC. SISTEMA", cdoc, "#555", 1, 3, "⚙️ Controle de ITs")

        # --- GRID 2x2 SEÇÕES (TAMANHO FIXO) ---
        self.criar_secao(self.grid_container, "🚩 Ciclo de revisão PFMEA", self.get_lista_pfmea(cursor), "#c0392b", 0, 0)
        self.criar_secao(self.grid_container, "🚨 ITs com Revisão Atrasada", self.get_its_atrasadas(cursor), "#c0392b", 0, 1)
        self.criar_secao(self.grid_container, "📂 Pendente documento no sistema", self.get_its_sem_link(cursor, "link_documento", "📂 SEM DOC"), "#555", 1, 0)
        self.criar_secao(self.grid_container, "🎓 Treinamentos Pendentes", self.get_its_sem_link(cursor, "link_treinamento", "🎓 PENDENTE"), "#e67e22", 1, 1)
        
        conn.close()

    def calcular_dias(self, data_str, ciclo_anos):
        try:
            hoje = datetime.now()
            dt = datetime.strptime(data_str, "%d/%m/%Y")
            try: venc = dt.replace(year=dt.year + ciclo_anos)
            except: venc = dt.replace(year=dt.year + ciclo_anos, day=28)
            return (venc - hoje).days
        except: return 9999

    def get_lista_pfmea(self, cursor):
        cursor.execute("SELECT id, numero, descricao, data_atual, ciclo_revisao FROM pfmeas WHERE status = 'Ativo'")
        res = []
        for tid, num, desc, data, ciclo in cursor.fetchall():
            dias = self.calcular_dias(data, ciclo)
            if dias < 0:
                res.append({'txt': f"🔴 ATRASADO | {num}: {desc[:20]}...", 'id': tid, 'tipo': 'pfmeas', 'dias': dias, 'status_venc': 'atrasado'})
            elif 0 <= dias <= 120:
                m = dias // 30
                txt = f"{m} meses" if m >= 1 else f"{dias} dias"
                res.append({'txt': f"🟠 {txt.upper()} | {num}: {desc[:20]}...", 'id': tid, 'tipo': 'pfmeas', 'dias': dias, 'status_venc': 'alerta'})
        return res

    def get_its_atrasadas(self, cursor):
        query = """
            SELECT i.id, i.numero, i.descricao, i.data_atual,
            (SELECT MAX(f.data_atual) FROM pfmeas f JOIN pfmea_it pi ON f.id = pi.pfmea_id WHERE pi.it_id = i.id) as dt_pai
            FROM its i 
            WHERE EXISTS (SELECT 1 FROM pfmeas f JOIN pfmea_it pi ON f.id = pi.pfmea_id WHERE pi.it_id = i.id AND f.status != 'Obsoleto')
            AND (SELECT MAX(substr(f.data_atual,7,4)||substr(f.data_atual,4,2)||substr(f.data_atual,1,2)) FROM pfmeas f JOIN pfmea_it pi ON f.id = pi.pfmea_id WHERE pi.it_id = i.id) 
                > (substr(i.data_atual,7,4)||substr(i.data_atual,4,2)||substr(i.data_atual,1,2))
        """
        cursor.execute(query)
        return [{'txt': f"🔴 REVISAR | IT {r[1]}: {r[2][:20]}...", 'id': r[0], 'tipo': 'its', 'dias': -1, 'status_venc': 'atrasado', 'dt_pai': r[4]} for r in cursor.fetchall()]

    def get_its_sem_link(self, cursor, campo, prefixo):
        cursor.execute(f"SELECT id, numero FROM its WHERE ({campo} IS NULL OR {campo} = '') AND EXISTS (SELECT 1 FROM pfmeas f JOIN pfmea_it pi ON f.id = pi.pfmea_id WHERE pi.it_id = its.id AND f.status != 'Obsoleto')")
        return [{'txt': f"{prefixo} | IT {r[1]}", 'id': r[0], 'tipo': 'its_pend', 'dias': 0, 'status_venc': 'doc'} for r in cursor.fetchall()]

    def criar_card_kpi(self, master, label, value, color, row, col, destino):
        card = customtkinter.CTkFrame(master, border_width=2, border_color=color, cursor="hand2")
        card.grid(row=row, column=col, padx=10, pady=5, sticky="nsew")
        master.grid_columnconfigure(col, weight=1)
        l1 = customtkinter.CTkLabel(card, text=label, font=("Arial", 11, "bold"), text_color="#aaa")
        l1.pack(pady=(10, 0))
        l2 = customtkinter.CTkLabel(card, text=str(value), font=self.font_card_value, text_color=color)
        l2.pack(pady=(0, 10))
        for w in [card, l1, l2]: w.bind("<Button-1>", lambda e: self.navegar(destino))

    def criar_secao(self, master, titulo, itens, color, row, col):
        cor_header = "#27ae60" if not itens else color
        # Card com altura mínima para manter o alinhamento
        container = customtkinter.CTkFrame(master, fg_color="#1e1e1e", border_width=1, border_color="#333", height=380)
        container.grid(row=row, column=col, padx=5, pady=10, sticky="nsew")
        container.grid_propagate(False) # Mantém o tamanho fixo
        
        h = customtkinter.CTkFrame(container, fg_color=cor_header, height=35); h.pack(fill="x")
        customtkinter.CTkLabel(h, text=titulo, font=("Arial", 13, "bold"), text_color="white").pack(pady=5)
        
        inner_scroll = customtkinter.CTkScrollableFrame(container, fg_color="transparent")
        inner_scroll.pack(fill="both", expand=True)

        if not itens:
            customtkinter.CTkLabel(inner_scroll, text="Tudo em dia! ✅", font=("Arial", 11, "italic"), text_color="#27ae60").pack(pady=20)
            return
            
        for item in itens:
            f = customtkinter.CTkFrame(inner_scroll, fg_color="transparent")
            f.pack(fill="x", pady=1)
            btn = customtkinter.CTkButton(f, text=item['txt'], anchor="w", fg_color="transparent", hover_color="#2d3436", font=self.font_item, text_color="white", height=32, command=lambda frm=f, i=item: self.toggle(frm, i))
            btn.pack(fill="x")
            f.box = None

    def toggle(self, frame, item):
        if frame.box: frame.box.destroy(); frame.box = None; return
        frame.box = customtkinter.CTkFrame(frame, fg_color="transparent")
        frame.box.pack(fill="x", padx=15, pady=0)
        
        if item['status_venc'] == 'atrasado':
            txt = f"⚠️ REVISAR" if item['tipo'] == 'its' else f"⚠️ VENCIDO HÁ {abs(item['dias'])} DIAS"
            c = "#e74c3c"
        elif item['status_venc'] == 'alerta':
            txt = f"⏳ VENCE EM {item['dias']} DIAS"
            c = "#f39c12"
        else:
            txt = "AÇÃO: CADASTRAR LINK"; c = "#777"
        
        customtkinter.CTkLabel(frame.box, text=txt, font=("Arial", 10, "bold"), text_color=c).pack(anchor="w")

        conn = database.connect_db(); cursor = conn.cursor()
        if item['tipo'] == "pfmeas":
            lbl = "⚙️ ITs Afetadas:"
            cursor.execute("SELECT i.numero FROM its i JOIN pfmea_it pi ON i.id = pi.it_id WHERE pi.pfmea_id = ?", (item['id'],))
        elif item['tipo'] == "its":
            lbl = "📦 PNs Afetados:"
            cursor.execute("SELECT codigo FROM pns WHERE it_id = ?", (item['id'],))
        else: conn.close(); return

        res = cursor.fetchall()
        afetados = [r[0] for r in res[:10]]
        txt_f = f"{lbl} " + ", ".join(afetados)
        if len(res) > 10: txt_f += f" (+{len(res)-10} itens)"
        customtkinter.CTkLabel(frame.box, text=txt_f, font=self.font_impact, text_color="#888", wraplength=350, justify="left").pack(anchor="w", pady=(0, 5))
        conn.close()