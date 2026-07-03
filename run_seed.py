# -*- coding: utf-8 -*-
"""Executa o seed_demo.sql no banco usando PyMySQL + credenciais do .env.

Não depende do cliente `mysql` de linha de comando: usa o mesmo driver
(PyMySQL) que a aplicação Flask já usa. É chamado pelo Popular_Banco.bat.
"""
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
SQL_FILE = os.path.join(BASE, "seed_demo.sql")
ENV_FILE = os.path.join(BASE, ".env")


def get_database_url():
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, encoding="utf-8") as f:
            for line in f:
                s = line.strip()
                if s.startswith("DATABASE_URL="):
                    return s.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get("DATABASE_URL")


def split_statements(sql):
    """Remove comentários e divide o script em statements por ';'."""
    lines = []
    for raw in sql.splitlines():
        s = raw.strip()
        if not s or s.startswith("--"):
            continue
        lines.append(raw)
    joined = "\n".join(lines)
    return [p.strip() for p in joined.split(";") if p.strip()]


def main():
    url = get_database_url()
    if not url:
        print("ERRO: não encontrei DATABASE_URL no .env.")
        sys.exit(1)

    try:
        from sqlalchemy.engine import make_url
        u = make_url(url)
        host = u.host or "localhost"
        port = u.port or 3306
        user = u.username
        pwd = u.password
        db = u.database
    except Exception as e:
        print("ERRO: não consegui interpretar a DATABASE_URL:", e)
        sys.exit(1)

    try:
        import pymysql
    except ImportError:
        print("ERRO: PyMySQL não está instalado no venv.")
        sys.exit(1)

    if not os.path.exists(SQL_FILE):
        print("ERRO: seed_demo.sql não foi encontrado ao lado deste script.")
        sys.exit(1)

    with open(SQL_FILE, encoding="utf-8") as f:
        statements = split_statements(f.read())

    print(f"Conectando em {host}:{port}/{db} como '{user}'...")
    conn = pymysql.connect(
        host=host, port=int(port), user=user, password=pwd,
        database=db, charset="utf8mb4",
    )

    selects = []
    try:
        with conn.cursor() as cur:
            for stmt in statements:
                up = stmt.lstrip().upper()
                if up.startswith(("START TRANSACTION", "COMMIT", "SET NAMES")):
                    continue  # a transação é controlada aqui pelo Python
                if up.startswith("SELECT"):
                    selects.append(stmt)
                    continue
                cur.execute(stmt)
        conn.commit()
        print("\nDados de demonstração inseridos com sucesso!")

        with conn.cursor() as cur:
            for s in selects:
                cur.execute(s)
                cols = [d[0] for d in cur.description]
                rows = cur.fetchall()
                print("\nConferência (contagem por tabela):")
                print("  " + " | ".join(cols))
                for r in rows:
                    print("  " + " | ".join(str(x) for x in r))
    except Exception as e:
        conn.rollback()
        print("\nERRO ao popular o banco — nada foi gravado (rollback):")
        print("   ", e)
        print(
            "\nDica: se você já rodou antes, os dados já existem "
            "(patrimônios e matrículas são únicos). Rode apenas uma vez."
        )
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
