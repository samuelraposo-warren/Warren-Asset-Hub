"""Blueprint principal: painel/dashboard."""
from datetime import date, timedelta

from flask import Blueprint, jsonify, render_template, request
from flask_login import current_user, login_required
from sqlalchemy import func

from app.extensions import db
from app.models.asset import Asset, AssetType
from app.models.employee import Employee
from app.models.enums import AssetStatus
from app.models.maintenance import MaintenanceRecord
from app.utils.settings import warranty_window_days

main_bp = Blueprint("main", __name__)

# Ordem/identificadores padrão dos widgets do painel (usado quando o
# usuário ainda não personalizou seu layout).
DEFAULT_WIDGETS = [
    "stats",
    "chart_status",
    "chart_type",
    "warranty",
    "unassigned",
    "open_maintenance",
    "status_table",
]


@main_bp.route("/")
@main_bp.route("/dashboard")
@login_required
def dashboard():
    active = Asset.query.filter(Asset.is_active.is_(True))

    status_counts = {
        status: active.filter(Asset.status == status).count()
        for status in AssetStatus
    }

    # Contagem por tipo de ativo (para o gráfico de barras).
    type_rows = (
        db.session.query(AssetType.name, func.count(Asset.id))
        .outerjoin(Asset, (Asset.asset_type_id == AssetType.id) & (Asset.is_active.is_(True)))
        .group_by(AssetType.id)
        .order_by(AssetType.name)
        .all()
    )
    type_counts = {name: count for name, count in type_rows}

    # Valor total do inventário (ativos vigentes).
    total_value = (
        db.session.query(func.coalesce(func.sum(Asset.purchase_price), 0))
        .filter(Asset.is_active.is_(True))
        .scalar()
    )

    # Garantias vencendo nos próximos N dias (janela configurável).
    window = warranty_window_days()
    today = date.today()
    horizon = today + timedelta(days=window)
    warranty_expiring = (
        active.filter(
            Asset.warranty_expiry_date.isnot(None),
            Asset.warranty_expiry_date >= today,
            Asset.warranty_expiry_date <= horizon,
        )
        .order_by(Asset.warranty_expiry_date)
        .all()
    )

    # Ativos ativos sem responsável.
    unassigned = (
        active.filter(
            Asset.assigned_to_id.is_(None),
            Asset.status == AssetStatus.ACTIVE,
        )
        .order_by(Asset.asset_tag)
        .all()
    )

    # Manutenções em aberto (sem data de conclusão).
    open_maintenances = (
        MaintenanceRecord.query.filter(MaintenanceRecord.finished_at.is_(None))
        .order_by(MaintenanceRecord.id.desc())
        .all()
    )

    stats = {
        "total_assets": active.count(),
        "total_value": total_value,
        "in_maintenance": status_counts.get(AssetStatus.MAINTENANCE, 0),
        "loaned": status_counts.get(AssetStatus.LOANED, 0),
        "employees": Employee.query.filter_by(is_active=True).count(),
        "unassigned_count": len(unassigned),
        "warranty_count": len(warranty_expiring),
        "open_maintenance_count": len(open_maintenances),
        "status_counts": status_counts,
    }

    # Dados dos gráficos, prontos para o Chart.js (labels em PT-BR).
    from app.utils.template_helpers import STATUS_LABELS
    chart_status = {
        "labels": [STATUS_LABELS.get(s.value, s.value) for s in AssetStatus],
        "data": [status_counts[s] for s in AssetStatus],
    }
    chart_type = {
        "labels": list(type_counts.keys()),
        "data": list(type_counts.values()),
    }

    # Layout personalizado do usuário (ordem + ocultos).
    layout = current_user.get_pref("dashboard", {}) or {}
    saved_order = [w for w in (layout.get("order") or []) if w in set(DEFAULT_WIDGETS)]
    # Garante que widgets novos (não presentes num layout antigo) apareçam.
    order = saved_order + [w for w in DEFAULT_WIDGETS if w not in saved_order]

    return render_template(
        "main/dashboard.html",
        stats=stats,
        warranty_expiring=warranty_expiring,
        unassigned=unassigned[:8],
        unassigned_total=len(unassigned),
        open_maintenances=open_maintenances[:8],
        warranty_window=window,
        today=today,
        chart_status=chart_status,
        chart_type=chart_type,
        default_widgets=DEFAULT_WIDGETS,
        layout_order=order,
        layout_hidden=layout.get("hidden") or [],
    )


@main_bp.route("/dashboard/layout", methods=["POST"])
@login_required
def save_layout():
    """Salva o layout do painel (ordem e widgets ocultos) do usuário."""
    payload = request.get_json(silent=True) or {}
    order = payload.get("order")
    hidden = payload.get("hidden")

    # Valida contra a lista conhecida de widgets (evita lixo no JSON).
    valid = set(DEFAULT_WIDGETS)
    order = [w for w in (order or []) if w in valid] or DEFAULT_WIDGETS
    hidden = [w for w in (hidden or []) if w in valid]

    current_user.set_pref("dashboard", {"order": order, "hidden": hidden})
    db.session.commit()
    return jsonify({"ok": True})


@main_bp.route("/dashboard/layout/reset", methods=["POST"])
@login_required
def reset_layout():
    current_user.set_pref("dashboard", {})
    db.session.commit()
    return jsonify({"ok": True})
