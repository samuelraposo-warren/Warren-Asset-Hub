"""Factory da aplicação Flask.

Segue o padrão Application Factory: ``create_app()`` monta e configura a
aplicação, inicializa as extensões (SQLAlchemy, Migrate, Login) e registra
os models e os event listeners de auditoria.
"""
import os

from flask import Flask

from config import config
from app.extensions import csrf, db, login_manager, migrate


def create_app(config_name=None):
    """Cria e configura uma instância da aplicação.

    :param config_name: "development" | "production" | "default".
        Se omitido, usa FLASK_ENV (ou "default").
    """
    config_name = config_name or os.environ.get("FLASK_ENV", "default")
    config_class = config.get(config_name, config["default"])

    app = Flask(__name__)
    app.config.from_object(config_class)

    # --- Extensões ---------------------------------------------------
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    # --- Models + auditoria -----------------------------------------
    # Importar o pacote de models registra todas as tabelas no metadata
    # do SQLAlchemy (necessário para o Flask-Migrate detectar) e ativa os
    # event listeners de auditoria via decorator @audit_model.
    from app import models  # noqa: F401

    # --- Flask-Login: carregador de usuário -------------------------
    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # --- Rotas -------------------------------------------------------
    from app.routes import register_blueprints

    register_blueprints(app)

    # --- Comandos CLI ------------------------------------------------
    from app.cli import register_cli

    register_cli(app)

    # --- Filtros/helpers de template --------------------------------
    from app.utils.template_helpers import register_template_helpers

    register_template_helpers(app)

    return app
