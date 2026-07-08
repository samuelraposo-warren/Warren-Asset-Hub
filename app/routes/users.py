"""Gestão de usuários do sistema (somente ADMIN).

Permite cadastrar novos usuários (com senha temporária definida pelo ADMIN),
editar papel/situação, redefinir senha e desativar. Protegido por
@role_required(ADMIN). O próprio model User não é auditado (decisão de
projeto), mas as ações críticas têm salvaguardas (não remover o último
ADMIN, não se auto-desativar).
"""
from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.access import ITSubsector, Module, UserModuleAccess
from app.models.enums import ModuleAccessLevel, UserRole
from app.models.user import User
from app.utils.decorators import role_required


def _access_form_ctx(user=None):
    """Sub-setores, módulos e o mapa de acesso atual do usuário."""
    access_map = {}
    if user is not None:
        access_map = {a.module_id: a.level.name for a in user.module_access}
    return {
        "subsectors": ITSubsector.query.filter_by(is_active=True).order_by(ITSubsector.name).all(),
        "modules": Module.query.filter_by(is_active=True).order_by(Module.sort_order, Module.name).all(),
        "access_map": access_map,
    }


def _apply_module_access(user, form):
    """Aplica os acessos por módulo enviados no formulário (Sem / Ver / Gerenciar)."""
    existing = {a.module_id: a for a in user.module_access}
    for m in Module.query.filter_by(is_active=True).all():
        val = form.get(f"access_{m.id}") or ""
        if val in ("VIEW", "MANAGE"):
            lvl = ModuleAccessLevel[val]
            if m.id in existing:
                existing[m.id].level = lvl
            else:
                db.session.add(UserModuleAccess(user_id=user.id, module_id=m.id, level=lvl))
        elif m.id in existing:
            db.session.delete(existing[m.id])

users_bp = Blueprint("users", __name__, url_prefix="/users")


def _admin_count(exclude_id=None):
    q = User.query.filter(User.role == UserRole.ADMIN, User.is_active.is_(True))
    if exclude_id is not None:
        q = q.filter(User.id != exclude_id)
    return q.count()


@users_bp.route("/")
@role_required(UserRole.ADMIN)
def list_users():
    q = (request.args.get("q") or "").strip()
    role = (request.args.get("role") or "").strip()
    status = (request.args.get("status") or "").strip()

    query = User.query
    if q:
        like = f"%{q}%"
        query = query.filter(or_(User.name.ilike(like), User.email.ilike(like)))
    if role in UserRole.__members__:
        query = query.filter(User.role == UserRole[role])
    if status == "active":
        query = query.filter(User.is_active.is_(True))
    elif status == "inactive":
        query = query.filter(User.is_active.is_(False))

    users = query.order_by(User.name).all()
    return render_template(
        "users/list.html",
        users=users,
        roles=list(UserRole),
        filters={"q": q, "role": role, "status": status},
    )


@users_bp.route("/new", methods=["GET", "POST"])
@role_required(UserRole.ADMIN)
def new_user():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        role_name = request.form.get("role") or "VIEWER"
        password = request.form.get("password") or ""
        is_active = "is_active" in request.form

        error = None
        if not name:
            error = "Informe o nome."
        elif not email:
            error = "Informe o e-mail."
        elif len(password) < 6:
            error = "A senha temporária deve ter ao menos 6 caracteres."
        elif User.query.filter_by(email=email).first():
            error = "Já existe um usuário com esse e-mail."

        if error is None:
            user = User(
                name=name,
                email=email,
                role=_role_or_default(role_name),
                is_active=is_active,
                subsector_id=request.form.get("subsector_id", type=int) or None,
                must_change_password=True,
            )
            user.set_password(password)
            try:
                db.session.add(user)
                db.session.flush()
                _apply_module_access(user, request.form)
                db.session.commit()
                flash(
                    f"Usuário '{email}' criado. Entregue a senha temporária "
                    "e peça para trocá-la no primeiro acesso.",
                    "success",
                )
                return redirect(url_for("users.list_users"))
            except IntegrityError:
                db.session.rollback()
                error = "Já existe um usuário com esse e-mail."
        flash(error, "danger")

    return render_template(
        "users/form.html", user=None, is_new=True, roles=list(UserRole),
        **_access_form_ctx(),
    )


@users_bp.route("/<int:user_id>/edit", methods=["GET", "POST"])
@role_required(UserRole.ADMIN)
def edit_user(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        abort(404)

    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        role_name = request.form.get("role") or user.role.name
        is_active = "is_active" in request.form
        new_role = _role_or_default(role_name)

        error = None
        if not name:
            error = "Informe o nome."
        # Não permitir remover o último ADMIN ativo (rebaixar ou desativar).
        elif user.role == UserRole.ADMIN and (
            new_role != UserRole.ADMIN or not is_active
        ) and _admin_count(exclude_id=user.id) == 0:
            error = "Este é o único ADMIN ativo — não é possível rebaixá-lo ou desativá-lo."
        # Não permitir se auto-desativar.
        elif user.id == current_user.id and not is_active:
            error = "Você não pode desativar a própria conta."

        if error is None:
            user.name = name
            user.role = new_role
            user.is_active = is_active
            user.subsector_id = request.form.get("subsector_id", type=int) or None
            _apply_module_access(user, request.form)
            db.session.commit()
            flash("Usuário atualizado.", "success")
            return redirect(url_for("users.list_users"))
        flash(error, "danger")

    return render_template(
        "users/form.html", user=user, is_new=False, roles=list(UserRole),
        **_access_form_ctx(user),
    )


@users_bp.route("/<int:user_id>/reset-password", methods=["POST"])
@role_required(UserRole.ADMIN)
def reset_password(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        abort(404)
    password = request.form.get("password") or ""
    if len(password) < 6:
        flash("A nova senha deve ter ao menos 6 caracteres.", "danger")
    else:
        user.set_password(password)
        db.session.commit()
        flash(f"Senha de '{user.email}' redefinida com sucesso.", "success")
    return redirect(url_for("users.edit_user", user_id=user.id))


def _role_or_default(name):
    try:
        return UserRole[name]
    except (KeyError, TypeError):
        return UserRole.VIEWER
