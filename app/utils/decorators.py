"""Decorators de autorização por papel (role)."""
from functools import wraps

from flask import abort, current_app
from flask_login import current_user


def role_required(*roles):
    """Restringe uma rota a usuários com um dos papéis informados.

    Uso:
        @role_required(UserRole.ADMIN, UserRole.TI)
        def editar_ativo(...):
            ...

    - Não autenticado -> redireciona para o login (mesmo comportamento de
      @login_required), via login_manager.
    - Autenticado sem o papel necessário -> 403.
    """
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                return current_app.login_manager.unauthorized()
            if current_user.role not in roles:
                abort(403)
            return view(*args, **kwargs)

        return wrapped

    return decorator
