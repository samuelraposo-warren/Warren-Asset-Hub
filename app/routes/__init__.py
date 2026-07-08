"""Pacote de rotas (blueprints).

register_blueprints(app) é chamado em create_app() para registrar todos
os blueprints da aplicação.
"""


def register_blueprints(app):
    from app.routes.assets import assets_bp
    from app.routes.audit import audit_bp
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.maintenance import maintenance_bp
    from app.routes.registry import registry_bp
    from app.routes.access import access_bp
    from app.routes.certificates import certificates_bp
    from app.routes.employees import employees_bp
    from app.routes.network import network_bp
    from app.routes.settings import settings_bp
    from app.routes.users import users_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(assets_bp)
    app.register_blueprint(maintenance_bp)
    app.register_blueprint(registry_bp)
    app.register_blueprint(audit_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(employees_bp)
    app.register_blueprint(network_bp)
    app.register_blueprint(certificates_bp)
    app.register_blueprint(access_bp)
