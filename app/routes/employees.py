"""Ficha do funcionário: máquinas atuais e histórico de movimentações.

Complementa a visão "pela máquina" (detalhe do ativo) com a visão "pela
pessoa": o que está sob responsabilidade dela agora e tudo que já passou
pelas suas mãos (recebido/entregue).
"""
from flask import Blueprint, abort, render_template
from sqlalchemy import or_

from app.extensions import db
from app.models.asset import Asset
from app.models.employee import Employee
from app.models.movement import AssetMovement
from app.utils.decorators import can_manage_slug, module_required

employees_bp = Blueprint("employees", __name__, url_prefix="/employees")

# Ficha de funcionário faz parte do módulo "Inventário de Máquinas".
MODULE_SLUG = "inventario-maquinas"


@employees_bp.route("/<int:employee_id>")
@module_required(MODULE_SLUG)
def view_employee(employee_id):
    emp = db.session.get(Employee, employee_id)
    if emp is None:
        abort(404)

    # Máquinas atualmente sob responsabilidade da pessoa.
    current_assets = (
        Asset.query.filter(
            Asset.assigned_to_id == emp.id,
            Asset.is_active.is_(True),
        )
        .order_by(Asset.asset_tag)
        .all()
    )

    # Histórico: toda movimentação em que a pessoa aparece (recebeu ou entregou).
    movements = (
        AssetMovement.query.filter(
            or_(
                AssetMovement.to_employee_id == emp.id,
                AssetMovement.from_employee_id == emp.id,
            )
        )
        .order_by(AssetMovement.moved_at.desc())
        .all()
    )

    return render_template(
        "employees/detail.html",
        emp=emp,
        current_assets=current_assets,
        movements=movements,
        can_edit=can_manage_slug(MODULE_SLUG),
    )
