"""CRUD genérico dos cadastros de apoio (config-driven).

Uma única família de rotas atende todas as entidades definidas em
app/utils/registry_config.py:

    /registry/<entity>/            -> lista
    /registry/<entity>/new         -> criar
    /registry/<entity>/<id>/edit   -> editar
    /registry/<entity>/<id>/delete -> excluir (soft delete se tiver is_active)
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
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.enums import UserRole
from app.utils.decorators import role_required
from app.utils.registry_config import REGISTRY

registry_bp = Blueprint("registry", __name__, url_prefix="/registry")

_EDITORS = (UserRole.ADMIN, UserRole.TI)


def _cfg_or_404(entity):
    cfg = REGISTRY.get(entity)
    if cfg is None:
        abort(404)
    return cfg


def _coerce(field, form):
    t = field["type"]
    raw = (form.get(field["key"]) or "").strip()
    if t == "number":
        try:
            return int(raw) if raw else None
        except ValueError:
            return None
    if t == "fk":
        try:
            return int(raw) if raw else None
        except ValueError:
            return None
    return raw or None


def _query_active(model):
    """Lista apenas registros ativos quando o model tem is_active."""
    query = model.query
    if hasattr(model, "is_active"):
        query = query.filter(model.is_active.is_(True))
    return query


def _apply(cfg, obj, form):
    for field in cfg["fields"]:
        value = _coerce(field, form)
        if field["required"] and not value:
            return f"O campo '{field['label']}' é obrigatório."
        setattr(obj, field["key"], value)
    return None


@registry_bp.route("/<entity>/")
@login_required
def list_entity(entity):
    cfg = _cfg_or_404(entity)
    model = cfg["model"]
    order_col = getattr(model, cfg["fields"][0]["key"])
    items = _query_active(model).order_by(order_col).all()
    return render_template(
        "registry/list.html",
        cfg=cfg,
        entity=entity,
        items=items,
        can_edit=current_user.role in _EDITORS,
    )


@registry_bp.route("/<entity>/new", methods=["GET", "POST"])
@role_required(*_EDITORS)
def new_entity(entity):
    cfg = _cfg_or_404(entity)
    obj = cfg["model"]()
    if request.method == "POST":
        error = _apply(cfg, obj, request.form)
        if error is None:
            try:
                db.session.add(obj)
                db.session.commit()
                flash(f"{cfg['singular']} cadastrado(a) com sucesso.", "success")
                return redirect(url_for("registry.list_entity", entity=entity))
            except IntegrityError:
                db.session.rollback()
                error = "Já existe um registro com esses dados (valor único duplicado)."
        flash(error, "danger")
    return render_template(
        "registry/form.html", cfg=cfg, entity=entity, obj=obj, is_new=True,
        fk_options=_fk_options(cfg),
    )


@registry_bp.route("/<entity>/<int:item_id>/edit", methods=["GET", "POST"])
@role_required(*_EDITORS)
def edit_entity(entity, item_id):
    cfg = _cfg_or_404(entity)
    obj = db.session.get(cfg["model"], item_id)
    if obj is None:
        abort(404)
    if request.method == "POST":
        error = _apply(cfg, obj, request.form)
        if error is None:
            try:
                db.session.commit()
                flash(f"{cfg['singular']} atualizado(a) com sucesso.", "success")
                return redirect(url_for("registry.list_entity", entity=entity))
            except IntegrityError:
                db.session.rollback()
                error = "Já existe um registro com esses dados (valor único duplicado)."
        flash(error, "danger")
    return render_template(
        "registry/form.html", cfg=cfg, entity=entity, obj=obj, is_new=False,
        fk_options=_fk_options(cfg),
    )


@registry_bp.route("/<entity>/<int:item_id>/delete", methods=["POST"])
@role_required(*_EDITORS)
def delete_entity(entity, item_id):
    cfg = _cfg_or_404(entity)
    model = cfg["model"]
    obj = db.session.get(model, item_id)
    if obj is None:
        abort(404)

    if hasattr(model, "is_active"):
        # Soft delete quando o model suporta.
        obj.is_active = False
        db.session.commit()
        flash(f"{cfg['singular']} removido(a).", "info")
    else:
        # Hard delete; se houver vínculos (FK), avisa em vez de quebrar.
        try:
            db.session.delete(obj)
            db.session.commit()
            flash(f"{cfg['singular']} removido(a).", "info")
        except IntegrityError:
            db.session.rollback()
            flash(
                f"Não é possível excluir: há registros vinculados a este(a) "
                f"{cfg['singular'].lower()}.",
                "danger",
            )
    return redirect(url_for("registry.list_entity", entity=entity))


def _fk_options(cfg):
    """Opções para cada campo FK do formulário: {key: [objs]}."""
    options = {}
    for field in cfg["fields"]:
        if field["type"] == "fk":
            fk_model = field["model"]
            query = _query_active(fk_model)
            display = getattr(fk_model, field["display"])
            options[field["key"]] = query.order_by(display).all()
    return options
