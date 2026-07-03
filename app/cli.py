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
