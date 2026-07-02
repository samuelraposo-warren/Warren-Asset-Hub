"""Configuração da aplicação.

Carrega as variáveis do arquivo .env via python-dotenv e expõe as classes
de configuração usadas pela factory create_app().
"""
import os

from dotenv import load_dotenv

# Carrega o .env que está na raiz do projeto (mesma pasta deste arquivo).
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))


class Config:
    """Configuração base — compartilhada por todos os ambientes."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-production")

    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Recicla conexões antes do timeout padrão do MySQL (evita
    # "MySQL server has gone away") e valida a conexão antes de usar.
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }


class DevelopmentConfig(Config):
    """Ambiente de desenvolvimento."""

    DEBUG = True


class ProductionConfig(Config):
    """Ambiente de produção."""

    DEBUG = False
    TESTING = False


# Mapa usado por create_app(config_name) para selecionar a configuração.
config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
