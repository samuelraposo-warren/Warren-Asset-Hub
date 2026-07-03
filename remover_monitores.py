# -*- coding: utf-8 -*-
"""Remove o tipo de ativo 'Monitor' e todos os ativos desse tipo do banco.

O escopo do sistema passou a ser apenas máquinas e impressoras — monitores
são geridos por outra equipe. Este script apaga, de forma definitiva:
  - as specs de monitor (monitor_specs) dos ativos monitor;
  - o histórico (asset_movements) e manutenções (maintenance_records) desses ativos;
  - os próprios ativos monitor;
  - o tipo de ativo 'monitor' (asset_types).

Os registros de auditoria (audit_logs) são preservados como histórico.
Usa PyMySQL + credenciais do .env. Roda numa transação (tudo ou nada).
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
            cur.execute("SELECT id FROM asset_types WHERE slug = 'monitor'")
            row = cur.fetchone()
            if not row:
                print("Nenhum tipo 'monitor' encontrado — nada a fazer.")
                return
            type_id = row[0]

            cur.execute("SELECT COUNT(*) FROM assets WHERE asset_type_id = %s", (type_id,))
            n_assets = cur.fetchone()[0]

            sub = "(SELECT id FROM (SELECT id FROM assets WHERE asset_type_id = %s) AS t)"
            cur.execute(f"DELETE FROM monitor_specs WHERE asset_id IN {sub}", (type_id,))
            cur.execute(f"DELETE FROM asset_movements WHERE asset_id IN {sub}", (type_id,))
            cur.execute(f"DELETE FROM maintenance_records WHERE asset_id IN {sub}", (type_id,))
            cur.execute("DELETE FROM assets WHERE asset_type_id = %s", (type_id,))
            cur.execute("DELETE FROM asset_types WHERE id = %s", (type_id,))

        conn.commit()
        print(f"Removidos: {n_assets} ativo(s) do tipo Monitor + o tipo 'monitor'.")
        print("Concluído com sucesso.")
    except Exception as e:
        conn.rollback()
        print("\nERRO ao remover monitores (rollback — nada foi apagado):")
        print("   ", e)
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
