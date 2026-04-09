import customtkinter
from tkinter import messagebox
import database
from abas.consultar import AbaConsultar
from abas.cadastrar_pn import AbaPN
from abas.cadastrar_it import AbaIT
from abas.controle_pfmea import AbaPFMEA
from abas.usuarios import AbaUsuarios
import sqlite3

# Garante a criação das tabelas ao iniciar (essencial para o executável)
database.create_tables()

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        
        # 1. ESTADO INICIAL
        self.nivel_acesso = "basico"
        self.usuario_logado = None

        # 2. CONFIGURAÇÃO DA JANELA
        self.title("Sistema Índice - Gestão Modular")
        self.geometry("1200x850")
        customtkinter.set_appearance_mode("dark")

        # 3. BARRA SUPERIOR
        self.top_frame = customtkinter.CTkFrame(self, height=50)
        self.top_frame.pack(fill="x", padx=10, pady=(5, 0))
        
        self.btn_login = customtkinter.CTkButton(
            self.top_frame, 
            text="🔑 Login Engenharia", 
            command=self.abrir_janela_login, 
            width=150
        )
        self.btn_login.pack(side="right", padx=10, pady=10)
        
        self.lbl_user = customtkinter.CTkLabel(
            self.top_frame, 
            text="Modo: Somente Leitura", 
            font=("Arial", 12, "italic")
        )
        self.lbl_user.pack(side="left", padx=20)

        # 4. ABAS (NOMES ATUALIZADOS)
        self.tabview = customtkinter.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        # Adicionando as abas iniciais com as novas nomenclaturas
        self.aba_consultar = AbaConsultar(self.tabview.add("📊 Dashboard"), self)
        self.aba_pn = AbaPN(self.tabview.add("📦 Controle de PNs"), self)
        self.aba_it = AbaIT(self.tabview.add("⚙️ Controle de ITs"), self)
        self.aba_pfmea = AbaPFMEA(self.tabview.add("📄 Controle de PFMEA"), self)

    def abrir_janela_login(self):
        if self.nivel_acesso == "engenharia":
            if messagebox.askyesno("Logout", "Deseja sair do modo de edição?"):
                self.nivel_acesso = "basico"
                self.usuario_logado = None
                self.atualizar_acesso()
            return

        self.janela_login = customtkinter.CTkToplevel(self)
        self.janela_login.title("Login de Engenharia")
        self.janela_login.geometry("300x250")
        
        self.janela_login.attributes("-topmost", True)
        self.janela_login.grab_set() 

        customtkinter.CTkLabel(self.janela_login, text="Usuário:").pack(pady=(20, 0))
        self.ent_user = customtkinter.CTkEntry(self.janela_login)
        self.ent_user.pack(pady=5)
        self.ent_user.focus_set()

        customtkinter.CTkLabel(self.janela_login, text="Senha:").pack(pady=(10, 0))
        self.ent_pass = customtkinter.CTkEntry(self.janela_login, show="*")
        self.ent_pass.pack(pady=5)

        customtkinter.CTkButton(
            self.janela_login, 
            text="Entrar", 
            command=self.validar_login
        ).pack(pady=20)

    def validar_login(self):
        user = self.ent_user.get()
        senha = self.ent_pass.get()

        conn = database.connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT nivel FROM usuarios WHERE username = ? AND password = ?", (user, senha))
        result = cursor.fetchone()
        conn.close()

        if result:
            self.nivel_acesso = result[0]
            self.usuario_logado = user
            
            self.janela_login.grab_release()
            self.janela_login.destroy()
            
            self.atualizar_acesso()
            messagebox.showinfo("Sucesso", f"Bem-vindo, {user}!")
        else:
            messagebox.showerror("Erro", "Usuário ou senha inválidos!")

    def atualizar_acesso(self):
        """Atualiza a interface e todas as abas conforme o nível de acesso logado."""
        if self.nivel_acesso == "engenharia":
            self.btn_login.configure(text="🔓 Logout", fg_color="#a83232")
            self.lbl_user.configure(text=f"Usuário: {self.usuario_logado}", text_color="#27ae60")
            
            # Adiciona aba de usuários apenas para engenharia
            try:
                self.aba_usuarios = AbaUsuarios(self.tabview.add("👥 Usuários"), self)
            except:
                pass 
        else:
            self.btn_login.configure(text="🔑 Login Engenharia", fg_color=['#3a7ebf', '#1f538d'])
            self.lbl_user.configure(text="Modo: Somente Leitura", text_color="white")
            
            # Remove aba de usuários em modo básico
            try:
                self.tabview.delete("👥 Usuários")
            except:
                pass

        # REFRESH OBRIGATÓRIO: Garante que as abas redesenhem seus formulários/botões
        self.aba_pn.setup_ui()
        self.aba_it.setup_ui()
        self.aba_pfmea.setup_ui()
        self.aba_consultar.load_data() # Atualiza os dados do dashboard

if __name__ == "__main__":
    app = App()
    app.mainloop()