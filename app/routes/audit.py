"""Blueprint de auditoria (somente leitura, restrito a ADMIN).

Exibe os registros do AuditLog gerados automaticamente pelos event
listeners. Nunca cria/edita/exclui — a tabela é imutável.
"""
from flask import Blueprint, abort, render_template, request

from app.extensions import db
from app.models.audit import AuditLog
from app.models.enums import AuditAction, UserRole
from app.utils.decorators import role_required

audit_bp = Blueprint("audit", __name__, url_prefix="/audit")


@audit_bp.route("/")
@role_required(UserRole.ADMIN)
def list_logs():
    page = request.args.get("page", 1, type=int)
    table = request.args.get("table") or ""
    action = request.args.get("action") or ""

    query = AuditLog.query
    if table:
        query = query.filter(AuditLog.table_name == table)
    if action:
        try:
            query = query.filter(AuditLog.action == AuditAction[action])
        except KeyError:
            pass

    # Itens por página vem da preferência de aparência do usuário.
    try:
        from flask_login import current_user
        per_page = int((current_user.get_pref("appearance", {}) or {}).get("rows_per_page", 30))
    except Exception:  # noqa: BLE001
        per_page = 30

    query = query.order_by(AuditLog.changed_at.desc(), AuditLog.id.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    tables = [
        row[0]
        for row in db.session.query(AuditLog.table_name)
        .distinct()
        .order_by(AuditLog.table_name)
        .all()
    ]

    return render_template(
        "audit/list.html",
        pagination=pagination,
        logs=pagination.items,
        tables=tables,
        filters={"table": table, "action": action},
    )


@audit_bp.route("/<int:log_id>")
@role_required(UserRole.ADMIN)
def view_log(log_id):
    log = db.session.get(AuditLog, log_id)
    if log is None:
        abort(404)

    old = log.old_values or {}
    new = log.new_values or {}
    keys = sorted(set(old) | set(new))
    rows = [
        {"key": k, "old": old.get(k), "new": new.get(k), "changed": old.get(k) != new.get(k)}
        for k in keys
    ]

    return render_template("audit/detail.html", log=log, rows=rows)
