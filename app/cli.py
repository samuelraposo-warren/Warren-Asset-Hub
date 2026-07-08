"""Comandos de linha de comando (Flask CLI).

Registrados em create_app() via register_cli(app). Exemplos:

    flask --app run:app seed-admin
    flask --app run:app seed-admin --email chefe@ti.com --password segredo123
    flask --app run:app seed-types
"""
import click
from flask.cli import with_appcontext

from app.extensions import db
from app.models.asset import AssetType
from app.models.enums import UserRole
from app.models.user import User


# Tipos de ativo padrão (name, slug).
_DEFAULT_TYPES = [
    ("Notebook", "notebook"),
    ("Desktop", "desktop"),
    ("Impressora", "printer"),
    ("Servidor", "server"),
    ("Rede", "network"),
]


def register_cli(app):
    @app.cli.command("seed-admin")
    @click.option("--email", default="admin@local", help="E-mail do admin.")
    @click.option("--password", default="admin123", help="Senha do admin.")
    @click.option("--name", default="Administrador", help="Nome do admin.")
    @with_appcontext
    def seed_admin(email, password, name):
        """Cria um usuário ADMIN inicial (idempotente)."""
        email = email.strip().lower()
        if User.query.filter_by(email=email).first():
            click.echo(f"Usuário '{email}' já existe — nada a fazer.")
            return

        user = User(name=name, email=email, role=UserRole.ADMIN, is_active=True)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo(f"Admin criado: {email} / {password}")
        click.echo("Troque a senha após o primeiro login.")

    @app.cli.command("seed-types")
    @with_appcontext
    def seed_types():
        """Popula os tipos de ativo padrão (idempotente)."""
        created = 0
        for name, slug in _DEFAULT_TYPES:
            if AssetType.query.filter_by(slug=slug).first():
                continue
            db.session.add(AssetType(name=name, slug=slug))
            created += 1
        db.session.commit()
        click.echo(f"{created} tipo(s) de ativo criado(s).")

    # --- Certificados -----------------------------------------------
    @app.cli.command("import-certs")
    @click.argument("path", type=click.Path(exists=True))
    @with_appcontext
    def import_certs(path):
        """Importa certificados de um arquivo JSON (crt.sh) ou Excel (.xlsx)."""
        if path.lower().endswith((".xlsx", ".xlsm")):
            from app.utils.cert_import import import_from_xlsx
            summary = import_from_xlsx(path)
        else:
            from app.utils.cert_import import import_from_json_text
            with open(path, encoding="utf-8") as f:
                summary = import_from_json_text(f.read())
        click.echo(
            f"Importação: {summary['created']} novo(s), "
            f"{summary['updated']} atualizado(s), {summary['domains']} domínio(s); "
            f"{summary['skipped']} ignorado(s) de {summary['total']} entrada(s)."
        )

    @app.cli.command("send-cert-alerts")
    @click.option("--dry-run", is_flag=True, help="Só simula; não envia e-mails.")
    @with_appcontext
    def send_cert_alerts(dry_run):
        """Verifica vencimentos e envia os alertas devidos (agendável)."""
        from app.utils.cert_alerts import run_alerts

        result = run_alerts(dry_run=dry_run)
        click.echo(
            f"Verificados: {result['checked']} | elegíveis: {result['due']} | "
            f"enviados: {result['sent']} | falhas: {result['failed']} | "
            f"já avisados: {result['skipped_recent']} | "
            f"destinatários: {len(result.get('recipients') or [])}"
        )
        for d in result["details"]:
            click.echo(f"  - {d['cert']} [{d['stage']}] {d['result']}")
