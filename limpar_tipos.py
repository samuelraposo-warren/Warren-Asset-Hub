# -*- coding: utf-8 -*-
"""Remove do banco os tipos fora de escopo (Monitor e Periférico).

O sistema cobre apenas máquinas (notebook, desktop, servidor, rede) e
impressoras. Este script, de forma idempotente e definitiva:
  - apaga os ativos dos tipos 'monitor' e 'peripheral' (e seu histórico:
    movimentações e manutenções);
  - remove os tipos 'monitor' e 'peripheral' de asset_types;
  - DROPA as tabelas monitor_specs e peripheral_specs.

Auditoria (audit_logs) é preservada. Usa PyMySQL + .env. Pode rodar mais
de uma vez sem problema. Substitui o antigo Remover_Monitores.
"""
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(BASE, ".env")
SLUGS = ("monitor", "peripheral")
SPEC_TABLES = ("monitor_specs", "peripheral_specs")


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
            # 1) Dropa PRIMEIRO as tabelas de spec (remove a FK que aponta para
            #    assets), senão o DELETE dos ativos falharia. DDL faz auto-commit.
            for tbl in SPEC_TABLES:
                cur.execute(f"DROP TABLE IF EXISTS {tbl}")
                print(f"• Tabela '{tbl}' removida (ou já inexistente).")

            # 2) Remove os ativos (e histórico) e o tipo de cada slug fora de escopo.
            for slug in SLUGS:
                cur.execute("SELECT id FROM asset_types WHERE slug = %s", (slug,))
                row = cur.fetchone()
                if not row:
                    print(f"• Tipo '{slug}' não existe — ok.")
                    continue
                type_id = row[0]
                cur.execute("SELECT COUNT(*) FROM assets WHERE asset_type_id = %s", (type_id,))
                n = cur.fetchone()[0]

                sub = "(SELECT id FROM (SELECT id FROM assets WHERE asset_type_id = %s) AS t)"
                cur.execute(f"DELETE FROM asset_movements WHERE asset_id IN {sub}", (type_id,))
                cur.execute(f"DELETE FROM maintenance_records WHERE asset_id IN {sub}", (type_id,))
                cur.execute("DELETE FROM assets WHERE asset_type_id = %s", (type_id,))
                cur.execute("DELETE FROM asset_types WHERE id = %s", (type_id,))
                print(f"• Tipo '{slug}' removido ({n} ativo(s) apagado(s)).")

            conn.commit()

        print("\nLimpeza concluída com sucesso.")
    except Exception as e:
        conn.rollback()
        print("\nERRO durante a limpeza (as exclusões foram revertidas):")
        print("   ", e)
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
