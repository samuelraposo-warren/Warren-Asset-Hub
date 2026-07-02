"""Blueprint de ativos: listagem, criação, visualização, edição e baixa."""
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
from flask_login import current_user, login_required
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.asset import Asset, AssetType
from app.models.employee import Employee
from app.models.enums import AssetCondition, AssetStatus, UserRole
from app.models.location import Location
from app.models.maintenance import MaintenanceRecord
from app.models.movement import AssetMovement
from app.models.supplier import Supplier
from app.utils.decorators import role_required
from app.utils.spec_config import SPEC_CONFIG

assets_bp = Blueprint("assets", __name__, url_prefix="/assets")

# Papéis autorizados a criar/editar/baixar ativos.
_EDITORS = (UserRole.ADMIN, UserRole.TI)


# ---------------------------------------------------------------------------
# Helpers de coerção
# ---------------------------------------------------------------------------
def _str_or_none(value):
    value = (value or "").strip()
    return value or None


def _int_or_none(value):
    value = (value or "").strip()
    if not value:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _parse_date(value):
    value = (value or "").strip()
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def _parse_decimal(value):
    value = (value or "").strip()
    if not value:
        return None
    # Aceita formato BR (1.234,56) e internacional (1234.56).
    if "," in value:
        value = value.replace(".", "").replace(",", ".")
    try:
        return Decimal(value)
    except InvalidOperation:
        return None


def _enum_or_default(enum_cls, name, default):
    try:
        return enum_cls[name]
    except (KeyError, TypeError):
        return default


def _coerce_field(field, form, name):
    t = field["type"]
    if t == "checkbox":
        return name in form
    raw = (form.get(name) or "").strip()
    if raw == "":
        return None
    if t == "number":
        try:
            return int(raw)
        except ValueError:
            return None
    if t == "select":
        try:
            return field["enum"][raw]
        except (KeyError, TypeError):
            return None
    return raw


def _sync_spec(asset, asset_type, form):
    """Cria/atualiza a spec correspondente ao tipo do ativo."""
    cfg = SPEC_CONFIG.get(asset_type.slug)
    if not cfg:
        return
    spec = getattr(asset, cfg["rel"])
    if spec is None:
        spec = cfg["model"]()
        setattr(asset, cfg["rel"], spec)
    for field in cfg["fields"]:
        name = f"spec__{asset_type.slug}__{field['key']}"
        setattr(spec, field["key"], _coerce_field(field, form, name))


def _apply_form(asset, form):
    """Popula o asset a partir do formulário. Retorna msg de erro ou None."""
    tag = (form.get("asset_tag") or "").strip()
    if not tag:
        return "Informe o patrimônio (asset_tag)."

    type_id = _int_or_none(form.get("asset_type_id"))
    asset_type = db.session.get(AssetType, type_id) if type_id else None
    if asset_type is None:
        return "Selecione um tipo de ativo válido."

    asset.asset_tag = tag
    asset.serial_number = _str_or_none(form.get("serial_number"))
    asset.asset_type_id = asset_type.id
    asset.brand = _str_or_none(form.get("brand"))
    asset.model = _str_or_none(form.get("model"))
    asset.status = _enum_or_default(AssetStatus, form.get("status"), AssetStatus.ACTIVE)
    asset.condition = _enum_or_default(
        AssetCondition, form.get("condition"), AssetCondition.GOOD
    )
    asset.purchase_date = _parse_date(form.get("purchase_date"))
    asset.warranty_expiry_date = _parse_date(form.get("warranty_expiry_date"))
    asset.purchase_price = _parse_decimal(form.get("purchase_price"))
    asset.supplier_id = _int_or_none(form.get("supplier_id"))
    asset.invoice_number = _str_or_none(form.get("invoice_number"))
    asset.location_id = _int_or_none(form.get("location_id"))
    asset.assigned_to_id = _int_or_none(form.get("assigned_to_id"))
    asset.notes = _str_or_none(form.get("notes"))

    if asset.created_by_id is None and current_user.is_authenticated:
        asset.created_by_id = current_user.id

    _sync_spec(asset, asset_type, form)
    return None


def _form_context():
    """Dados compartilhados pelos selects do formulário."""
    return {
        "asset_types": AssetType.query.order_by(AssetType.name).all(),
        "locations": Location.query.order_by(Location.name).all(),
        "employees": Employee.query.filter_by(is_active=True)
        .order_by(Employee.name)
        .all(),
        "suppliers": Supplier.query.filter_by(is_active=True)
        .order_by(Supplier.name)
        .all(),
        "spec_config": SPEC_CONFIG,
    }


# ---------------------------------------------------------------------------
# Rotas
# ---------------------------------------------------------------------------
@assets_bp.route("/")
@login_required
def list_assets():
    query = Asset.query.filter(Asset.is_active.is_(True))

    status = request.args.get("status") or ""
    type_id = _int_or_none(request.args.get("type"))
    search = (request.args.get("q") or "").strip()

    if status:
        query = query.filter(Asset.status == _enum_or_default(AssetStatus, status, None))
    if type_id:
        query = query.filter(Asset.asset_type_id == type_id)
    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(
                Asset.asset_tag.ilike(like),
                Asset.serial_number.ilike(like),
                Asset.brand.ilike(like),
                Asset.model.ilike(like),
            )
        )

    assets = query.order_by(Asset.created_at.desc()).all()
    return render_template(
        "assets/list.html",
        assets=assets,
        asset_types=AssetType.query.order_by(AssetType.name).all(),
        filters={"status": status, "type": type_id, "q": search},
        can_edit=current_user.role in _EDITORS,
    )


@assets_bp.route("/<int:asset_id>")
@login_required
def view_asset(asset_id):
    asset = db.session.get(Asset, asset_id)
    if asset is None:
        abort(404)
    cfg = SPEC_CONFIG.get(asset.asset_type.slug) if asset.asset_type else None
    spec = getattr(asset, cfg["rel"]) if cfg else None
    movements = (
        AssetMovement.query.filter_by(asset_id=asset.id)
        .order_by(AssetMovement.moved_at.desc())
        .all()
    )
    maintenances = (
        MaintenanceRecord.query.filter_by(asset_id=asset.id)
        .order_by(MaintenanceRecord.id.desc())
        .all()
    )
    return render_template(
        "assets/detail.html",
        asset=asset,
        spec_cfg=cfg,
        spec=spec,
        movements=movements,
        maintenances=maintenances,
        can_edit=current_user.role in _EDITORS,
    )


@assets_bp.route("/new", methods=["GET", "POST"])
@role_required(*_EDITORS)
def new_asset():
    asset = Asset()
    if request.method == "POST":
        error = _apply_form(asset, request.form)
        if error is None:
            try:
                db.session.add(asset)
                db.session.commit()
                flash("Ativo criado com sucesso.", "success")
                return redirect(url_for("assets.view_asset", asset_id=asset.id))
            except IntegrityError:
                db.session.rollback()
                error = "Já existe um ativo com esse patrimônio (asset_tag)."
        flash(error, "danger")
    return render_template(
        "assets/form.html", asset=asset, is_new=True, **_form_context()
    )


@assets_bp.route("/<int:asset_id>/edit", methods=["GET", "POST"])
@role_required(*_EDITORS)
def edit_asset(asset_id):
    asset = db.session.get(Asset, asset_id)
    if asset is None:
        abort(404)
    if request.method == "POST":
        error = _apply_form(asset, request.form)
        if error is None:
            try:
                db.session.commit()
                flash("Ativo atualizado com sucesso.", "success")
                return redirect(url_for("assets.view_asset", asset_id=asset.id))
            except IntegrityError:
                db.session.rollback()
                error = "Já existe um ativo com esse patrimônio (asset_tag)."
        flash(error, "danger")
    return render_template(
        "assets/form.html", asset=asset, is_new=False, **_form_context()
    )


@assets_bp.route("/<int:asset_id>/delete", methods=["POST"])
@role_required(*_EDITORS)
def delete_asset(asset_id):
    asset = db.session.get(Asset, asset_id)
    if asset is None:
        abort(404)
    # Soft delete: nunca remove fisicamente.
    asset.is_active = False
    db.session.commit()
    flash(f"Ativo {asset.asset_tag} baixado (removido logicamente).", "info")
    return redirect(url_for("assets.list_assets"))


@assets_bp.route("/<int:asset_id>/assign", methods=["GET", "POST"])
@role_required(*_EDITORS)
def assign_asset(asset_id):
    """Atribui/transfere um ativo: grava histórico e atualiza o estado atual."""
    asset = db.session.get(Asset, asset_id)
    if asset is None:
        abort(404)

    if request.method == "POST":
        to_employee_id = _int_or_none(request.form.get("to_employee_id"))
        to_location_id = _int_or_none(request.form.get("to_location_id"))
        reason = _str_or_none(request.form.get("reason"))
        notes = _str_or_none(request.form.get("notes"))

        # Registra a movimentação (histórico / cadeia de custódia).
        movement = AssetMovement(
            asset_id=asset.id,
            from_employee_id=asset.assigned_to_id,
            to_employee_id=to_employee_id,
            from_location_id=asset.location_id,
            to_location_id=to_location_id,
            moved_by_id=current_user.id,
            reason=reason,
            notes=notes,
        )
        db.session.add(movement)

        # Atualiza o estado atual do ativo.
        asset.assigned_to_id = to_employee_id
        if to_location_id is not None:
            asset.location_id = to_location_id

        db.session.commit()
        flash("Movimentação registrada com sucesso.", "success")
        return redirect(url_for("assets.view_asset", asset_id=asset.id))

    return render_template(
        "assets/assign.html",
        asset=asset,
        locations=Location.query.order_by(Location.name).all(),
        employees=Employee.query.filter_by(is_active=True)
        .order_by(Employee.name)
        .all(),
    )
