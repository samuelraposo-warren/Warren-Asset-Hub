"""Decorators de autorização por papel (role) e por módulo do Centralizador."""
from functools import wraps

from flask import abort, current_app
from flask_login import current_user


def module_by_slug(slug):
    """Retorna o Module com o slug informado (ou None)."""
    from app.models.access import Module
    return Module.query.filter_by(slug=slug).first()


def can_manage_slug(slug):
    """True se o usuário atual pode GERENCIAR o módulo (Gestor sempre pode).
    Se o módulo ainda não existe no banco, cai no papel de Gestor."""
    module = module_by_slug(slug)
    if module is None:
        return getattr(current_user, "is_gestor", False)
    return current_user.can_manage(module)


def can_view_slug(slug):
    """True se o usuário atual pode VER o módulo."""
    module = module_by_slug(slug)
    if module is None:
        return getattr(current_user, "is_gestor", False)
    return current_user.can_view(module)


def module_required(slug, manage=False):
    """Restringe uma rota ao acesso a um módulo do Centralizador.

    Uso:
        @module_required("certificados")            # exige Ver
        @module_required("certificados", manage=True)  # exige Gerenciar

    Gestor de TI (ADMIN) sempre passa. Não autenticado -> login;
    autenticado sem o nível necessário -> 403. Se o módulo não existir
    no banco (ainda não semeado), apenas exige autenticação para não
    travar o acesso durante a implantação.
    """
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                return current_app.login_manager.unauthorized()
            from app.models.access import Module

            module = Module.query.filter_by(slug=slug).first()
            if module is None:
                return view(*args, **kwargs)  # módulo ainda não cadastrado
            allowed = (current_user.can_manage(module) if manage
                       else current_user.can_view(module))
            if not allowed:
                abort(403)
            return view(*args, **kwargs)

        return wrapped

    return decorator


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
