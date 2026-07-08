# -*- coding: utf-8 -*-
"""Vincula os racks R02 e R03 ao ambiente 'CPD' (idempotente).

Evita ter que editar cada rack na mão. Se o ambiente 'CPD' não existir,
avisa para criá-lo primeiro. Usa PyMySQL + credenciais do .env.
"""
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(BASE, ".env")

RACK_CODES = ("R02", "R03")
AREA_NAME = "CPD"


def get_database_url():
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, encoding="utf-8") as f:
            for line in f:
                s = line.strip()
                if s.startswith("DATABASE_URL="):
                    return s.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get("DATABASE_URL")


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
            cur.execute(
                "SELECT id FROM net_areas WHERE name = %s AND (is_active = 1 OR is_active IS NULL) LIMIT 1",
                (AREA_NAME,),
            )
            row = cur.fetchone()
            if not row:
                print(f"ERRO: ambiente '{AREA_NAME}' não encontrado. "
                      f"Crie-o em Infraestrutura → Ambientes e rode de novo.")
                sys.exit(1)
            area_id = row[0]

            fmt = ",".join(["%s"] * len(RACK_CODES))
            cur.execute(
                f"UPDATE net_racks SET area_id = %s WHERE code IN ({fmt})",
                (area_id, *RACK_CODES),
            )
            affected = cur.rowcount
        conn.commit()
        print(f"OK: {affected} rack(s) vinculados ao ambiente '{AREA_NAME}' "
              f"(id {area_id}): {', '.join(RACK_CODES)}.")
        print("Concluído.")
    except Exception as e:
        conn.rollback()
        print("\nERRO (rollback):", e)
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
