import customtkinter
import database
from tkinter import messagebox

class AbaUsuarios:
    def __init__(self, parent, controller):
        self.parent = parent
        self.controller = controller
        self.setup_ui()

    def setup_ui(self):
        for widget in self.parent.winfo_children(): widget.destroy()
        
        # Coluna Esquerda: Cadastro
        self.left = customtkinter.CTkFrame(self.parent, width=350)
        self.left.pack(side="left", fill="both", padx=10, pady=10)
        
        customtkinter.CTkLabel(self.left, text="👤 Novo Usuário", font=("Arial", 16, "bold")).pack(pady=20)
        
        self.ent_new_user = customtkinter.CTkEntry(self.left, placeholder_text="Nome de Usuário", height=35)
        self.ent_new_user.pack(fill="x", padx=20, pady=5)
        
        self.ent_new_pass = customtkinter.CTkEntry(self.left, placeholder_text="Senha", show="*", height=35)
        self.ent_new_pass.pack(fill="x", padx=20, pady=5)
        
        self.combo_nivel = customtkinter.CTkOptionMenu(self.left, values=["engenharia", "basico"])
        self.combo_nivel.pack(fill="x", padx=20, pady=10)
        
        customtkinter.CTkButton(self.left, text="Cadastrar", command=self.registrar).pack(pady=20, padx=20, fill="x")

        # Coluna Direita: Lista
        self.right = customtkinter.CTkFrame(self.parent)
        self.right.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        self.scroll = customtkinter.CTkScrollableFrame(self.right, label_text="Usuários Cadastrados")
        self.scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.atualizar_lista()

    def registrar(self):
        u, p, n = self.ent_new_user.get(), self.ent_new_pass.get(), self.combo_nivel.get()
        if u and p:
            if database.adicionar_usuario(u, p, n):
                messagebox.showinfo("Sucesso", f"Usuário {u} criado!")
                self.ent_new_user.delete(0, 'end'); self.ent_new_pass.delete(0, 'end')
                self.atualizar_lista()
            else:
                messagebox.showerror("Erro", "Usuário já existe!")

    def atualizar_lista(self):
        for widget in self.scroll.winfo_children(): widget.destroy()
        users = database.get_todos_usuarios()
        for uid, uname, nivel in users:
            f = customtkinter.CTkFrame(self.scroll)
            f.pack(fill="x", pady=2, padx=5)
            customtkinter.CTkLabel(f, text=f"{uname} ({nivel})").pack(side="left", padx=10)
            # Não deixa o admin se deletar sozinho para não travar o sistema
            if uname != self.controller.usuario_logado:
                customtkinter.CTkButton(f, text="🗑️", width=30, fg_color="#a83232", 
                                         command=lambda id=uid: self.remover(id)).pack(side="right", padx=5)

    def remover(self, uid):
        if messagebox.askyesno("Confirmar", "Deletar este usuário?"):
            database.deletar_usuario(uid)
            self.atualizar_lista()