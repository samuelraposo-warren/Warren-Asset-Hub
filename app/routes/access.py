"""Gestão do Centralizador (só Gestor de TI): sub-setores e módulos."""
import re

from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import login_required
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.access import ITSubsector, Module
from app.models.enums import UserRole
from app.utils.decorators import role_required

access_bp = Blueprint("access", __name__, url_prefix="/gestao")

# Endpoints oferecidos ao vincular um módulo a uma tela existente.
KNOWN_ENDPOINTS = [
    ("", "— (em breve, sem tela)"),
    ("assets.list_assets", "Inventário de Máquinas"),
    ("network.overview", "Infraestrutura de Rede"),
    ("audit.list_logs", "Auditoria"),
]


def _slugify(text):
    text = (text or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text or "item"


# ---------------------------------------------------------------------------
# Sub-setores
# ---------------------------------------------------------------------------
@access_bp.route("/subsetores")
@role_required(UserRole.ADMIN)
def subsectors():
    return render_template(
        "access/subsectors.html",
        subsectors=ITSubsector.query.order_by(ITSubsector.name).all(),
    )


@access_bp.route("/subsetores/new", methods=["GET", "POST"])
@access_bp.route("/subsetores/<int:sub_id>/edit", methods=["GET", "POST"])
@role_required(UserRole.ADMIN)
def edit_subsector(sub_id=None):
    sub = db.session.get(ITSubsector, sub_id) if sub_id else ITSubsector()
    if sub_id and sub is None:
        abort(404)
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        if not name:
            flash("Informe o nome.", "danger")
        else:
            sub.name = name
            sub.slug = (request.form.get("slug") or "").strip() or _slugify(name)
            sub.description = (request.form.get("description") or "").strip() or None
            sub.icon = (request.form.get("icon") or "").strip() or None
            try:
                if not sub_id:
                    db.session.add(sub)
                db.session.commit()
                flash("Sub-setor salvo.", "success")
                return redirect(url_for("access.subsectors"))
            except IntegrityError:
                db.session.rollback()
                flash("Já existe um sub-setor com esse nome/slug.", "danger")
    return render_template("access/subsector_form.html", sub=sub, is_new=not sub_id)


@access_bp.route("/subsetores/<int:sub_id>/delete", methods=["POST"])
@role_required(UserRole.ADMIN)
def delete_subsector(sub_id):
    sub = db.session.get(ITSubsector, sub_id)
    if sub is None:
        abort(404)
    sub.is_active = False
    db.session.commit()
    flash("Sub-setor removido.", "info")
    return redirect(url_for("access.subsectors"))


# ---------------------------------------------------------------------------
# Módulos
# ---------------------------------------------------------------------------
@access_bp.route("/modulos")
@role_required(UserRole.ADMIN)
def modules():
    return render_template(
        "access/modules.html",
        modules=Module.query.order_by(Module.sort_order, Module.name).all(),
    )


@access_bp.route("/modulos/new", methods=["GET", "POST"])
@access_bp.route("/modulos/<int:mod_id>/edit", methods=["GET", "POST"])
@role_required(UserRole.ADMIN)
def edit_module(mod_id=None):
    mod = db.session.get(Module, mod_id) if mod_id else Module()
    if mod_id and mod is None:
        abort(404)
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        if not name:
            flash("Informe o nome do módulo.", "danger")
        else:
            mod.name = name
            mod.slug = (request.form.get("slug") or "").strip() or _slugify(name)
            mod.description = (request.form.get("description") or "").strip() or None
            mod.icon = (request.form.get("icon") or "").strip() or None
            mod.endpoint = (request.form.get("endpoint") or "").strip() or None
            mod.subsector_id = request.form.get("subsector_id", type=int) or None
            mod.sort_order = request.form.get("sort_order", type=int) or 0
            try:
                if not mod_id:
                    db.session.add(mod)
                db.session.commit()
                flash("Módulo salvo.", "success")
                return redirect(url_for("access.modules"))
            except IntegrityError:
                db.session.rollback()
                flash("Já existe um módulo com esse slug.", "danger")
    return render_template(
        "access/module_form.html",
        mod=mod, is_new=not mod_id,
        subsectors=ITSubsector.query.filter_by(is_active=True).order_by(ITSubsector.name).all(),
        endpoints=KNOWN_ENDPOINTS,
    )


@access_bp.route("/modulos/<int:mod_id>/delete", methods=["POST"])
@role_required(UserRole.ADMIN)
def delete_module(mod_id):
    mod = db.session.get(Module, mod_id)
    if mod is None:
        abort(404)
    mod.is_active = False
    db.session.commit()
    flash("Módulo removido.", "info")
    return redirect(url_for("access.modules"))
