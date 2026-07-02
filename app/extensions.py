"""Instâncias das extensões Flask.

Ficam isoladas neste módulo para evitar importações circulares: os models
importam ``db`` daqui, e a factory ``create_app`` inicializa as extensões
com a aplicação via ``init_app``.
"""
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()

# View para redirecionamento quando um usuário não autenticado acessa
# uma rota protegida (será registrada quando as rotas existirem).
login_manager.login_view = "auth.login"
login_manager.login_message = "Faça login para acessar esta página."
login_manager.login_message_category = "warning"
