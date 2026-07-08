"""Blueprint de manutenções (MaintenanceRecord)."""
from datetime import datetime
from decimal import Decimal, InvalidOperation

from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user

from app.extensions import db
from app.models.asset import Asset
from app.models.enums import MaintenanceType
from app.models.maintenance import MaintenanceRecord
from app.utils.decorators import can_manage_slug, module_required

maintenance_bp = Blueprint("maintenance", __name__, url_prefix="/maintenance")

# Manutenções fazem parte do módulo "Inventário de Máquinas".
MODULE_SLUG = "inventario-maquinas"


def _str_or_none(value):
    value = (value or "").strip()
    return value or None


def _int_or_none(value):
    value = (value or "").strip()
    try:
        return int(value) if value else None
    except ValueError:
        return None


def _parse_datetime(value):
    value = (value or "").strip()
    if not value:
        return None
    # <input type="datetime-local"> envia 'YYYY-MM-DDTHH:MM'.
    for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def _parse_decimal(value):
    value = (value or "").strip()
    if not value:
        return None
    if "," in value:
        value = value.replace(".", "").replace(",", ".")
    try:
        return Decimal(value)
    except InvalidOperation:
        return None


def _apply(record, form):
    asset_id = _int_or_none(form.get("asset_id"))
    if asset_id is None or db.session.get(Asset, asset_id) is None:
        return "Selecione um ativo válido."
    try:
        m_type = MaintenanceType[form.get("type")]
    except (KeyError, TypeError):
        return "Selecione o tipo de manutenção."

    record.asset_id = asset_id
    record.type = m_type
    record.description = _str_or_none(form.get("description"))
    record.performed_by = _str_or_none(form.get("performed_by"))
    record.started_at = _parse_datetime(form.get("started_at"))
    record.finished_at = _parse_datetime(form.get("finished_at"))
    record.cost = _parse_decimal(form.get("cost"))
    if record.created_by_id is None and current_user.is_authenticated:
        record.created_by_id = current_user.id
    return None


def _form_context():
    return {
        "assets": Asset.query.filter(Asset.is_active.is_(True))
        .order_by(Asset.asset_tag)
        .all(),
    }


@maintenance_bp.route("/")
@module_required(MODULE_SLUG)
def list_maintenance():
    status = request.args.get("status") or ""
    m_type = request.args.get("type") or ""

    query = MaintenanceRecord.query
    if m_type:
        try:
            query = query.filter(MaintenanceRecord.type == MaintenanceType[m_type])
        except KeyError:
            pass
    if status == "open":
        query = query.filter(MaintenanceRecord.finished_at.is_(None))
    elif status == "closed":
        query = query.filter(MaintenanceRecord.finished_at.isnot(None))

    records = query.order_by(MaintenanceRecord.id.desc()).all()
    return render_template(
        "maintenance/list.html",
        records=records,
        filters={"status": status, "type": m_type},
        can_edit=can_manage_slug(MODULE_SLUG),
    )


@maintenance_bp.route("/new", methods=["GET", "POST"])
@module_required(MODULE_SLUG, manage=True)
def new_maintenance():
    record = MaintenanceRecord()
    if request.method == "POST":
        error = _apply(record, request.form)
        if error is None:
            db.session.add(record)
            db.session.commit()
            flash("Manutenção registrada com sucesso.", "success")
            return redirect(url_for("maintenance.list_maintenance"))
        flash(error, "danger")
    else:
        # Pré-seleção do ativo quando vem do detalhe do ativo (?asset_id=).
        record.asset_id = _int_or_none(request.args.get("asset_id"))
    return render_template(
        "maintenance/form.html", record=record, is_new=True, **_form_context()
    )


@maintenance_bp.route("/<int:record_id>/edit", methods=["GET", "POST"])
@module_required(MODULE_SLUG, manage=True)
def edit_maintenance(record_id):
    record = db.session.get(MaintenanceRecord, record_id)
    if record is None:
        abort(404)
    if request.method == "POST":
        error = _apply(record, request.form)
        if error is None:
            db.session.commit()
            flash("Manutenção atualizada com sucesso.", "success")
            return redirect(url_for("maintenance.list_maintenance"))
        flash(error, "danger")
    return render_template(
        "maintenance/form.html", record=record, is_new=False, **_form_context()
    )


@maintenance_bp.route("/<int:record_id>/delete", methods=["POST"])
@module_required(MODULE_SLUG, manage=True)
def delete_maintenance(record_id):
    record = db.session.get(MaintenanceRecord, record_id)
    if record is None:
        abort(404)
    db.session.delete(record)
    db.session.commit()
    flash("Registro de manutenção removido.", "info")
    return redirect(url_for("maintenance.list_maintenance"))
