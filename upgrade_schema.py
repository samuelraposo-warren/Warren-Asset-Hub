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

            # 5) Módulo Infraestrutura: enriquecer net_areas (ambientes)
            if table_exists(cur, "net_areas"):
                for col, ddl in (
                    ("kind", "VARCHAR(40) NULL"),
                    ("description", "VARCHAR(255) NULL"),
                    ("notes", "TEXT NULL"),
                    ("created_at", "DATETIME NULL"),
                ):
                    if column_exists(cur, "net_areas", col):
                        print(f"• Coluna 'net_areas.{col}' já existe — ok.")
                    else:
                        cur.execute(f"ALTER TABLE net_areas ADD COLUMN {col} {ddl}")
                        print(f"• Coluna 'net_areas.{col}' adicionada.")
            else:
                print("• Tabela 'net_areas' ainda não existe (rode Importar_Rede.bat) — ok.")

            # 5b) Rack pertence a um ambiente (net_racks.area_id)
            if table_exists(cur, "net_racks"):
                if column_exists(cur, "net_racks", "area_id"):
                    print("• Coluna 'net_racks.area_id' já existe — ok.")
                else:
                    cur.execute("ALTER TABLE net_racks ADD COLUMN area_id INT NULL")
                    print("• Coluna 'net_racks.area_id' adicionada.")

            # 6) Módulo Infraestrutura: tabela de equipamentos por ambiente
            if table_exists(cur, "net_equipment"):
                print("• Tabela 'net_equipment' já existe — ok.")
            else:
                cur.execute(
                    """CREATE TABLE net_equipment (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        area_id INT NOT NULL,
                        name VARCHAR(160) NOT NULL,
                        kind VARCHAR(40) NULL,
                        quantity INT NOT NULL DEFAULT 1,
                        notes VARCHAR(255) NULL,
                        is_active TINYINT(1) NOT NULL DEFAULT 1,
                        created_at DATETIME NULL,
                        INDEX ix_net_equipment_area_id (area_id)
                    ) CHARACTER SET utf8mb4"""
                )
                print("• Tabela 'net_equipment' criada.")

            # 7) Ponto de rede pode referenciar um equipamento (opcional)
            if table_exists(cur, "net_points"):
                if column_exists(cur, "net_points", "equipment_id"):
                    print("• Coluna 'net_points.equipment_id' já existe — ok.")
                else:
                    cur.execute("ALTER TABLE net_points ADD COLUMN equipment_id INT NULL")
                    print("• Coluna 'net_points.equipment_id' adicionada.")

            # 8) Layout de ocupação: setores, mesas e posições
            new_tables = {
                "net_sectors": """CREATE TABLE net_sectors (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(120) NOT NULL UNIQUE,
                    is_active TINYINT(1) NOT NULL DEFAULT 1
                ) CHARACTER SET utf8mb4""",
                "net_desks": """CREATE TABLE net_desks (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    area_id INT NOT NULL,
                    name VARCHAR(120) NOT NULL,
                    notes TEXT NULL,
                    is_active TINYINT(1) NOT NULL DEFAULT 1,
                    created_at DATETIME NULL,
                    INDEX ix_net_desks_area_id (area_id)
                ) CHARACTER SET utf8mb4""",
                "net_seats": """CREATE TABLE net_seats (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    desk_id INT NOT NULL,
                    position INT NOT NULL DEFAULT 1,
                    employee_id INT NULL,
                    label VARCHAR(120) NULL,
                    notes VARCHAR(255) NULL,
                    is_active TINYINT(1) NOT NULL DEFAULT 1,
                    created_at DATETIME NULL,
                    INDEX ix_net_seats_desk_id (desk_id)
                ) CHARACTER SET utf8mb4""",
                "net_area_sectors": """CREATE TABLE net_area_sectors (
                    area_id INT NOT NULL,
                    sector_id INT NOT NULL,
                    PRIMARY KEY (area_id, sector_id)
                ) CHARACTER SET utf8mb4""",
                "net_desk_sectors": """CREATE TABLE net_desk_sectors (
                    desk_id INT NOT NULL,
                    sector_id INT NOT NULL,
                    PRIMARY KEY (desk_id, sector_id)
                ) CHARACTER SET utf8mb4""",
            }
            for tname, ddl in new_tables.items():
                if table_exists(cur, tname):
                    print(f"• Tabela '{tname}' já existe — ok.")
                else:
                    cur.execute(ddl)
                    print(f"• Tabela '{tname}' criada.")

            # 9) Centralizador: sub-setores, módulos e acesso por usuário
            access_tables = {
                "it_subsectors": """CREATE TABLE it_subsectors (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(120) NOT NULL UNIQUE,
                    slug VARCHAR(80) NOT NULL UNIQUE,
                    description VARCHAR(255) NULL,
                    icon VARCHAR(40) NULL,
                    is_active TINYINT(1) NOT NULL DEFAULT 1
                ) CHARACTER SET utf8mb4""",
                "it_modules": """CREATE TABLE it_modules (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(120) NOT NULL,
                    slug VARCHAR(80) NOT NULL UNIQUE,
                    description VARCHAR(255) NULL,
                    icon VARCHAR(40) NULL,
                    endpoint VARCHAR(120) NULL,
                    subsector_id INT NULL,
                    sort_order INT NOT NULL DEFAULT 0,
                    is_active TINYINT(1) NOT NULL DEFAULT 1
                ) CHARACTER SET utf8mb4""",
                "user_module_access": """CREATE TABLE user_module_access (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    module_id INT NOT NULL,
                    level VARCHAR(10) NOT NULL DEFAULT 'VIEW',
                    created_at DATETIME NULL,
                    UNIQUE KEY uq_user_module (user_id, module_id),
                    INDEX ix_uma_user (user_id),
                    INDEX ix_uma_module (module_id)
                ) CHARACTER SET utf8mb4""",
            }
            for tname, ddl in access_tables.items():
                if table_exists(cur, tname):
                    print(f"• Tabela '{tname}' já existe — ok.")
                else:
                    cur.execute(ddl)
                    print(f"• Tabela '{tname}' criada.")

            # users.subsector_id
            if column_exists(cur, "users", "subsector_id"):
                print("• Coluna 'users.subsector_id' já existe — ok.")
            else:
                cur.execute("ALTER TABLE users ADD COLUMN subsector_id INT NULL")
                print("• Coluna 'users.subsector_id' adicionada.")

            # 10) Módulo Certificados: certificados + domínios (SANs)
            cert_tables = {
                "certificates": """CREATE TABLE certificates (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    serial_number VARCHAR(160) NOT NULL UNIQUE,
                    crtsh_id BIGINT NULL,
                    issuer_ca_id INT NULL,
                    issuer_name VARCHAR(255) NULL,
                    common_name VARCHAR(255) NULL,
                    not_before DATETIME NULL,
                    not_after DATETIME NULL,
                    entry_timestamp DATETIME NULL,
                    result_count INT NULL,
                    notes TEXT NULL,
                    last_alert_stage VARCHAR(20) NULL,
                    last_alert_sent_on DATE NULL,
                    is_active TINYINT(1) NOT NULL DEFAULT 1,
                    created_at DATETIME NULL,
                    updated_at DATETIME NULL,
                    INDEX ix_certificates_common_name (common_name),
                    INDEX ix_certificates_not_after (not_after),
                    INDEX ix_certificates_is_active (is_active)
                ) CHARACTER SET utf8mb4""",
                "certificate_domains": """CREATE TABLE certificate_domains (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    certificate_id INT NOT NULL,
                    domain VARCHAR(255) NOT NULL,
                    is_wildcard TINYINT(1) NOT NULL DEFAULT 0,
                    environment VARCHAR(20) NULL,
                    INDEX ix_cert_domains_cert (certificate_id),
                    INDEX ix_cert_domains_domain (domain)
                ) CHARACTER SET utf8mb4""",
            }
            for tname, ddl in cert_tables.items():
                if table_exists(cur, tname):
                    print(f"• Tabela '{tname}' já existe — ok.")
                else:
                    cur.execute(ddl)
                    print(f"• Tabela '{tname}' criada.")

            # 10b) Aponta o módulo 'certificados' para a tela real (se ainda "em breve").
            if table_exists(cur, "it_modules"):
                cur.execute(
                    "UPDATE it_modules SET endpoint='certificates.list_certificates' "
                    "WHERE slug='certificados' AND (endpoint IS NULL OR endpoint='')"
                )
                if cur.rowcount:
                    print("• Módulo 'certificados' vinculado à tela (endpoint atualizado).")
                else:
                    print("• Módulo 'certificados' já vinculado (ou ainda não semeado) — ok.")

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
