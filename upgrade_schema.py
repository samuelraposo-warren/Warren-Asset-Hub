# -*- coding: utf-8 -*-
"""Atualiza o schema do banco para os novos recursos (idempotente).

Cria a tabela `settings` (parâmetros do sistema) e adiciona a coluna
`preferences` (JSON) na tabela `users` — só faz o que ainda não existe.
Usa PyMySQL + credenciais do .env, igual ao run_seed.py (não depende do
cliente mysql de linha de comando). Pode ser executado quantas vezes quiser.
"""
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(BASE, ".env")


def get_database_url():
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, encoding="utf-8") as f:
            for line in f:
                s = line.strip()
                if s.startswith("DATABASE_URL="):
                    return s.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get("DATABASE_URL")


def column_exists(cur, table, column):
    cur.execute(
        """SELECT COUNT(*) FROM information_schema.COLUMNS
           WHERE TABLE_SCHEMA = DATABASE()
             AND TABLE_NAME = %s AND COLUMN_NAME = %s""",
        (table, column),
    )
    return cur.fetchone()[0] > 0


def table_exists(cur, table):
    cur.execute(
        """SELECT COUNT(*) FROM information_schema.TABLES
           WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s""",
        (table,),
    )
    return cur.fetchone()[0] > 0


def main():
    url = get_database_url()
    if not url:
        print("ERRO: não encontrei DATABASE_URL no .env.")
        sys.exit(1)

    try:
        from sqlalchemy.engine import make_url
        u = make_url(url)
        host, port = u.host or "localhost", u.port or 3306
        user, pwd, db = u.username, u.password, u.database
    except Exception as e:
        print("ERRO: DATABASE_URL inválida:", e)
        sys.exit(1)

    try:
        import pymysql
    except ImportError:
        print("ERRO: PyMySQL não está instalado no venv.")
        sys.exit(1)

    print(f"Conectando em {host}:{port}/{db} como '{user}'...")
    conn = pymysql.connect(host=host, port=int(port), user=user, password=pwd,
                           database=db, charset="utf8mb4")
    try:
        with conn.cursor() as cur:
            # 1) Tabela settings
            if table_exists(cur, "settings"):
                print("• Tabela 'settings' já existe — ok.")
            else:
                cur.execute(
                    """CREATE TABLE settings (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        `key` VARCHAR(80) NOT NULL UNIQUE,
                        value VARCHAR(500) NULL
                    ) CHARACTER SET utf8mb4"""
                )
                print("• Tabela 'settings' criada.")

            # 2) Coluna users.preferences (JSON)
            if column_exists(cur, "users", "preferences"):
                print("• Coluna 'users.preferences' já existe — ok.")
            else:
                cur.execute("ALTER TABLE users ADD COLUMN preferences JSON NULL")
                print("• Coluna 'users.preferences' adicionada.")

            # 3) Coluna users.must_change_password (troca obrigatória de senha)
            if column_exists(cur, "users", "must_change_password"):
                print("• Coluna 'users.must_change_password' já existe — ok.")
            else:
                cur.execute(
                    "ALTER TABLE users ADD COLUMN must_change_password "
                    "TINYINT(1) NOT NULL DEFAULT 0"
                )
                print("• Coluna 'users.must_change_password' adicionada.")

            # 4) Coluna assets.image_url (link da foto — ex.: Google Drive)
            if column_exists(cur, "assets", "image_url"):
                print("• Coluna 'assets.image_url' já existe — ok.")
            else:
                cur.execute("ALTER TABLE assets ADD COLUMN image_url VARCHAR(1000) NULL")
                print("• Coluna 'assets.image_url' adicionada.")

        conn.commit()
        print("\nSchema atualizado com sucesso!")
    except Exception as e:
        conn.rollback()
        print("\nERRO ao atualizar o schema (rollback):")
        print("   ", e)
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
