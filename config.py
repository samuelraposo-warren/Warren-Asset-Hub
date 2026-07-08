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

    # --- E-mail (SMTP) ----------------------------------------------
    # Usado pelos alertas de vencimento de certificados. Padrão: Google
    # Workspace/Gmail (smtp.gmail.com:587 STARTTLS, senha de app).
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", "587"))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() in ("1", "true", "yes")
    MAIL_USE_SSL = os.environ.get("MAIL_USE_SSL", "false").lower() in ("1", "true", "yes")
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    # Remetente exibido. Se vazio, cai no MAIL_USERNAME.
    MAIL_FROM = os.environ.get("MAIL_FROM") or os.environ.get("MAIL_USERNAME")
    MAIL_FROM_NAME = os.environ.get("MAIL_FROM_NAME", "Centralizador de TI")
    # Destinatário extra fixo (opcional): sempre recebe cópia dos alertas.
    MAIL_ALERT_EXTRA = os.environ.get("MAIL_ALERT_EXTRA")


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
