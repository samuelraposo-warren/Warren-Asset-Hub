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

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(assets_bp)
    app.register_blueprint(maintenance_bp)
    app.register_blueprint(registry_bp)
    app.register_blueprint(audit_bp)
