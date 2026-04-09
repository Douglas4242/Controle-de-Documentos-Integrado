import sqlite3
import sqlite3
import os
import sys

def connect_db():
    # Isso garante que o DB seja criado na mesma pasta do executável
    if getattr(sys, 'frozen', False):
        # Se estiver rodando como executável
        base_path = os.path.dirname(sys.executable)
    else:
        # Se estiver rodando como script .py
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    db_path = os.path.join(base_path, "indice_documentos.db")
    return sqlite3.connect(db_path)

def connect_db():
    """Estabelece conexão com o banco de dados."""
    return sqlite3.connect("indice_documentos.db")

def create_tables():
    conn = connect_db()
    cursor = conn.cursor()

    # 1. TABELA DE PFMEAs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pfmeas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero TEXT NOT NULL,
        descricao TEXT,
        cliente TEXT,
        data_inicial TEXT,
        data_atual TEXT,
        revisao TEXT,
        status TEXT DEFAULT 'Ativo',
        ciclo_revisao INTEGER DEFAULT 2,
        link_documento TEXT
    )
    """)

    # 2. TABELA DE HISTÓRICO DE PFMEAs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS historico_pfmeas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pfmea_id INTEGER,
        data_rev TEXT,
        indice_rev TEXT,
        link_rev TEXT,
        FOREIGN KEY (pfmea_id) REFERENCES pfmeas (id)
    )
    """)

    # 3. TABELA DE ITs (Instruções de Trabalho)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS its (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero TEXT NOT NULL,
        descricao TEXT,
        cliente TEXT,
        data_atual TEXT,
        revisao_indice TEXT,
        link_documento TEXT,    
        link_treinamento TEXT,
        treinamento_status INTEGER DEFAULT 0,
        status TEXT DEFAULT 'Ativo'
    )
    """)

    # 4. TABELA DE HISTÓRICO DE ITs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS historico_its (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        it_id INTEGER,
        data_rev TEXT,
        indice_rev TEXT,
        link_rev TEXT,
        link_trein_rev TEXT,
        trein_status_rev INTEGER DEFAULT 0,
        FOREIGN KEY (it_id) REFERENCES its (id)
    )
    """)

    # 5. TABELA DE PNs (Part Numbers / Peças)
    # ATUALIZADO: Incluindo coluna 'status' para obsolescência manual/herdada
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo TEXT UNIQUE NOT NULL,
        descricao TEXT,
        cliente TEXT,
        projeto TEXT,
        desenho_num TEXT,
        desenho_rev TEXT,
        link_desenho TEXT,
        pcs_embalagem INTEGER,
        nivel TEXT,
        it_id INTEGER,
        status TEXT DEFAULT 'Ativo',
        obs1 TEXT,
        obs2 TEXT,
        obs3 TEXT,
        FOREIGN KEY (it_id) REFERENCES its (id)
    )
    """)

    # 6. TABELA DE LIGAÇÃO (N:N entre PFMEA e IT)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pfmea_it (
        pfmea_id INTEGER,
        it_id INTEGER,
        FOREIGN KEY (pfmea_id) REFERENCES pfmeas (id),
        FOREIGN KEY (it_id) REFERENCES its (id),
        PRIMARY KEY (pfmea_id, it_id)
    )
    """)

    # 7. TABELA DE USUÁRIOS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        nivel TEXT NOT NULL
    )
    """)

    # Cria usuário padrão caso o banco seja novo
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO usuarios (username, password, nivel) VALUES (?, ?, ?)", 
                    ('admin', '1234', 'engenharia'))

    conn.commit()
    conn.close()
    print("Banco de dados pronto para o executável! ✅")

# --- FUNÇÕES DE AUXÍLIO PARA AS ABAS ---

def get_all_its():
    conn = connect_db(); cursor = conn.cursor()
    cursor.execute("SELECT id, numero, descricao FROM its ORDER BY numero ASC")
    data = cursor.fetchall(); conn.close()
    return data 

def get_all_pfmeas():
    conn = connect_db(); cursor = conn.cursor()
    cursor.execute("SELECT id, numero, status FROM pfmeas ORDER BY CAST(numero AS INTEGER), numero")
    data = cursor.fetchall(); conn.close()
    return data

def get_todos_usuarios():
    conn = connect_db(); cursor = conn.cursor()
    cursor.execute("SELECT id, username, nivel FROM usuarios")
    users = cursor.fetchall(); conn.close()
    return users

def deletar_usuario(user_id):
    conn = connect_db(); cursor = conn.cursor()
    cursor.execute("DELETE FROM usuarios WHERE id = ?", (user_id,))
    conn.commit(); conn.close()

def adicionar_usuario(user, password, nivel):
    conn = connect_db(); cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO usuarios (username, password, nivel) VALUES (?, ?, ?)", (user, password, nivel))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    create_tables()

