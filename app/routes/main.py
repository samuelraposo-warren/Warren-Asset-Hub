"""Blueprint principal: painel/dashboard."""
from datetime import date, timedelta

from flask import Blueprint, render_template
from flask_login import login_required
from sqlalchemy import func

from app.extensions import db
from app.models.asset import Asset
from app.models.employee import Employee
from app.models.enums import AssetStatus
from app.models.maintenance import MaintenanceRecord

main_bp = Blueprint("main", __name__)

# Janela (em dias) para considerar uma garantia "vencendo".
_WARRANTY_WINDOW_DAYS = 30


@main_bp.route("/")
@main_bp.route("/dashboard")
@login_required
def dashboard():
    active = Asset.query.filter(Asset.is_active.is_(True))

    status_counts = {
        status: active.filter(Asset.status == status).count()
        for status in AssetStatus
    }

    # Valor total do inventário (ativos vigentes).
    total_value = (
        db.session.query(func.coalesce(func.sum(Asset.purchase_price), 0))
        .filter(Asset.is_active.is_(True))
        .scalar()
    )

    # Garantias vencendo nos próximos N dias.
    today = date.today()
    horizon = today + timedelta(days=_WARRANTY_WINDOW_DAYS)
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
    return render_template(
        "main/dashboard.html",
        stats=stats,
        warranty_expiring=warranty_expiring,
        unassigned=unassigned[:8],
        unassigned_total=len(unassigned),
        open_maintenances=open_maintenances[:8],
        warranty_window=_WARRANTY_WINDOW_DAYS,
        today=today,
    )
