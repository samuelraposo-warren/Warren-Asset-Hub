"""Blueprint do módulo Certificados (Centralizador Warren).

Listagem/busca de certificados (com foco em validade), detalhe, cadastro
manual, importação do JSON do crt.sh (colar ou enviar arquivo) e disparo
manual dos alertas de vencimento.

Autorização por módulo do Centralizador (slug 'certificados'):
  - ver: qualquer usuário com acesso (Gestor sempre);
  - gerenciar (criar/editar/importar/excluir/alertar): acesso "Gerenciar".
"""
from datetime import datetime

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
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.certificate import Certificate, CertificateDomain
from app.utils.cert_import import _detect_env, _split_domains, import_from_json_text
from app.utils.decorators import module_required

certificates_bp = Blueprint("certificates", __name__, url_prefix="/certificados")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _str_or_none(value):
    value = (value or "").strip()
    return value or None


def _parse_dt(value):
    value = (value or "").strip()
    if not value:
        return None
    for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def _rows_per_page():
    try:
        return int((current_user.get_pref("appearance", {}) or {}).get("rows_per_page", 30))
    except Exception:  # noqa: BLE001
        return 30


def _can_manage():
    """True se o usuário atual pode gerenciar o módulo de certificados."""
    from app.models.access import Module
    module = Module.query.filter_by(slug="certificados").first()
    if module is None:
        return current_user.is_gestor
    return current_user.can_manage(module)


# ---------------------------------------------------------------------------
# Listagem
# ---------------------------------------------------------------------------
def _filtered_query(args):
    """Constrói a query de certificados ativos aplicando busca (q), ambiente
    (env) e situação (status). Reutilizada pela listagem e pela exclusão em
    lote (para 'selecionar todos do filtro atual')."""
    from datetime import date, timedelta

    status = (args.get("status") or "").strip()
    q = (args.get("q") or "").strip()
    env = (args.get("env") or "").strip()

    query = Certificate.query.filter(Certificate.is_active.is_(True))

    # Um único JOIN com os domínios (busca + ambiente) — evita join duplicado.
    if q or env:
        query = query.outerjoin(CertificateDomain)
        if q:
            like = f"%{q}%"
            query = query.filter(
                or_(
                    Certificate.common_name.ilike(like),
                    Certificate.issuer_name.ilike(like),
                    Certificate.serial_number.ilike(like),
                    CertificateDomain.domain.ilike(like),
                )
            )
        if env:
            query = query.filter(CertificateDomain.environment == env)
        query = query.distinct()

    today = date.today()
    if status == "expired":
        query = query.filter(Certificate.not_after < today)
    elif status == "expiring":  # próximos 30 dias (inclui crítico)
        query = query.filter(
            Certificate.not_after >= today,
            Certificate.not_after <= today + timedelta(days=30),
        )
    elif status == "critical":  # próximos 7 dias
        query = query.filter(
            Certificate.not_after >= today,
            Certificate.not_after <= today + timedelta(days=7),
        )
    elif status == "valid":
        query = query.filter(Certificate.not_after > today + timedelta(days=30))
    elif status == "novalidity":  # sem data de validade (a resolver)
        query = query.filter(Certificate.not_after.is_(None))

    return query, {"status": status, "q": q, "env": env}


@certificates_bp.route("/")
@module_required("certificados")
def list_certificates():
    from datetime import date, timedelta

    query, filters = _filtered_query(request.args)
    today = date.today()

    # --- Ordenação (cabeçalhos clicáveis) --------------------------------
    sort = (request.args.get("sort") or "expiry").strip()
    direction = (request.args.get("dir") or "asc").strip()
    is_desc = direction == "desc"

    # Quantidade de domínios via subconsulta correlacionada (não interfere
    # nos joins/distinct dos filtros).
    domain_count = (
        select(func.count(CertificateDomain.id))
        .where(CertificateDomain.certificate_id == Certificate.id)
        .correlate(Certificate)
        .scalar_subquery()
    )
    sort_cols = {
        "cn": Certificate.common_name,
        "issuer": Certificate.issuer_name,
        "expiry": Certificate.not_after,
        "status": Certificate.not_after,  # situação deriva do vencimento
        "domains": domain_count,
    }
    col = sort_cols.get(sort, Certificate.not_after)
    if sort in ("expiry", "status"):
        # "sem data" (nulos) sempre por último, independente da direção.
        query = query.order_by(
            Certificate.not_after.is_(None),
            col.desc() if is_desc else col.asc(),
        )
    else:
        query = query.order_by(col.desc() if is_desc else col.asc())

    filters["sort"] = sort
    filters["dir"] = direction

    page = request.args.get("page", 1, type=int)
    pagination = query.paginate(page=page, per_page=_rows_per_page(), error_out=False)

    # Contadores para os "chips" de resumo no topo.
    base = Certificate.query.filter(Certificate.is_active.is_(True))
    counts = {
        "total": base.count(),
        "expired": base.filter(Certificate.not_after < today).count(),
        "critical": base.filter(
            Certificate.not_after >= today,
            Certificate.not_after <= today + timedelta(days=7),
        ).count(),
        "expiring": base.filter(
            Certificate.not_after >= today,
            Certificate.not_after <= today + timedelta(days=30),
        ).count(),
        "novalidity": base.filter(Certificate.not_after.is_(None)).count(),
    }

    return render_template(
        "certificates/list.html",
        certificates=pagination.items,
        pagination=pagination,
        counts=counts,
        can_manage=_can_manage(),
        filters=filters,
    )


@certificates_bp.route("/<int:cert_id>")
@module_required("certificados")
def view_certificate(cert_id):
    cert = db.session.get(Certificate, cert_id)
    if cert is None or not cert.is_active:
        abort(404)
    return render_template(
        "certificates/detail.html", cert=cert, can_manage=_can_manage()
    )


# ---------------------------------------------------------------------------
# Cadastro manual (criar/editar)
# ---------------------------------------------------------------------------
def _apply_form(cert, form):
    serial = (form.get("serial_number") or "").strip()
    if not serial:
        return "Informe o número de série (serial)."
    cert.serial_number = serial
    cert.common_name = _str_or_none(form.get("common_name"))
    cert.issuer_name = _str_or_none(form.get("issuer_name"))
    cert.not_before = _parse_dt(form.get("not_before"))
    cert.not_after = _parse_dt(form.get("not_after"))
    cert.notes = _str_or_none(form.get("notes"))

    # Domínios: um por linha no textarea.
    cert.domains.clear()
    for dom in _split_domains(form.get("domains")):
        cert.domains.append(CertificateDomain(
            domain=dom, is_wildcard=dom.startswith("*."), environment=_detect_env(dom)
        ))
    return None


@certificates_bp.route("/new", methods=["GET", "POST"])
@module_required("certificados", manage=True)
def new_certificate():
    cert = Certificate()
    if request.method == "POST":
        error = _apply_form(cert, request.form)
        if error is None:
            db.session.add(cert)
            try:
                db.session.commit()
                flash("Certificado cadastrado.", "success")
                return redirect(url_for("certificates.view_certificate", cert_id=cert.id))
            except IntegrityError:
                db.session.rollback()
                error = "Já existe um certificado com esse serial."
        flash(error, "danger")
    return render_template("certificates/form.html", cert=cert, is_new=True)


@certificates_bp.route("/<int:cert_id>/edit", methods=["GET", "POST"])
@module_required("certificados", manage=True)
def edit_certificate(cert_id):
    cert = db.session.get(Certificate, cert_id)
    if cert is None or not cert.is_active:
        abort(404)
    if request.method == "POST":
        error = _apply_form(cert, request.form)
        if error is None:
            try:
                db.session.commit()
                flash("Certificado atualizado.", "success")
                return redirect(url_for("certificates.view_certificate", cert_id=cert.id))
            except IntegrityError:
                db.session.rollback()
                error = "Já existe um certificado com esse serial."
        flash(error, "danger")
    return render_template("certificates/form.html", cert=cert, is_new=False)


@certificates_bp.route("/<int:cert_id>/delete", methods=["POST"])
@module_required("certificados", manage=True)
def delete_certificate(cert_id):
    cert = db.session.get(Certificate, cert_id)
    if cert is None:
        abort(404)
    cert.is_active = False
    db.session.commit()
    flash("Certificado removido.", "info")
    return redirect(url_for("certificates.list_certificates"))


@certificates_bp.route("/excluir-lote", methods=["POST"])
@module_required("certificados", manage=True)
def bulk_delete():
    """Exclui (soft-delete) vários certificados de uma vez: os IDs marcados,
    ou TODOS os que casam com o filtro atual (select_all_filtered)."""
    keep_filters = {k: request.form.get(k, "") for k in ("status", "q", "env")}

    if request.form.get("select_all_filtered") == "1":
        query, _ = _filtered_query(request.form)
        certs = query.all()
    else:
        ids = [int(x) for x in request.form.getlist("ids") if x.isdigit()]
        if not ids:
            flash("Nenhum certificado selecionado.", "warning")
            return redirect(url_for("certificates.list_certificates", **keep_filters))
        certs = Certificate.query.filter(
            Certificate.id.in_(ids), Certificate.is_active.is_(True)
        ).all()

    n = 0
    for cert in certs:
        cert.is_active = False
        n += 1
    db.session.commit()
    flash(f"{n} certificado(s) removido(s).", "info")
    return redirect(url_for("certificates.list_certificates", **keep_filters))


# ---------------------------------------------------------------------------
# Importação (JSON do crt.sh ou planilha Excel)
# ---------------------------------------------------------------------------
def _flash_summary(summary):
    flash(
        f"Importação concluída: {summary['created']} novo(s), "
        f"{summary['updated']} atualizado(s), {summary['domains']} domínio(s); "
        f"{summary['skipped']} ignorado(s) de {summary['total']} entrada(s).",
        "success",
    )


@certificates_bp.route("/importar", methods=["GET", "POST"])
@module_required("certificados", manage=True)
def import_certificates_view():
    if request.method == "POST":
        # 1) Excel (.xlsx) -> vai para a tela de REVISÃO (não grava ainda).
        xlsx = request.files.get("xlsx_file")
        if xlsx and xlsx.filename:
            if not xlsx.filename.lower().endswith((".xlsx", ".xlsm")):
                flash("Envie um arquivo .xlsx.", "danger")
                return render_template("certificates/import.html")
            from app.utils.cert_import import parse_xlsx
            try:
                rows = parse_xlsx(xlsx)
            except ValueError as e:
                flash(str(e), "danger")
                return render_template("certificates/import.html")
            if not rows:
                flash("Nenhuma linha encontrada na planilha.", "warning")
                return render_template("certificates/import.html")
            return _render_xlsx_review(rows)

        # 2) JSON (colado ou arquivo).
        text = (request.form.get("json_text") or "").strip()
        file = request.files.get("json_file")
        if file and file.filename:
            try:
                text = file.read().decode("utf-8")
            except Exception:  # noqa: BLE001
                flash("Não consegui ler o arquivo (esperado UTF-8).", "danger")
                return render_template("certificates/import.html")
        if not text:
            flash("Cole o JSON, ou selecione um arquivo JSON/Excel.", "danger")
            return render_template("certificates/import.html")
        try:
            summary = import_from_json_text(text)
        except ValueError as e:
            flash(str(e), "danger")
            return render_template("certificates/import.html")
        _flash_summary(summary)
        return redirect(url_for("certificates.list_certificates"))
    return render_template("certificates/import.html")


@certificates_bp.route("/importar/modelo")
@module_required("certificados", manage=True)
def import_template_xlsx():
    """Baixa a planilha-modelo (.xlsx) com as colunas esperadas."""
    import io

    from flask import send_file

    from app.utils.cert_import import build_template_workbook

    bio = io.BytesIO()
    build_template_workbook().save(bio)
    bio.seek(0)
    return send_file(
        bio, as_attachment=True, download_name="modelo_certificados.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


def _render_xlsx_review(rows):
    """Monta a tela de revisão/comparação do Excel (novo × existente +
    inconsistências), sem gravar nada."""
    import json
    from datetime import date

    from app.models.certificate import Certificate

    today = date.today()
    view_rows, payload = [], []
    n_new = n_update = n_problem = n_nodate = 0

    for i, r in enumerate(rows):
        existing = Certificate.query.filter_by(
            serial_number=r["serial_number"]).first()
        na = r["not_after"]
        days = (na.date() - today).days if na else None
        if days is None:
            status = "unknown"
        elif days < 0:
            status = "expired"
        elif days <= 7:
            status = "critical"
        elif days <= 30:
            status = "warning"
        else:
            status = "valid"
        changed = bool(existing and existing.not_after and na
                       and existing.not_after.date() != na.date())
        importable = not r["problems"]
        if na is None and importable:
            n_nodate += 1
        if not importable:
            n_problem += 1
        elif existing:
            n_update += 1
        else:
            n_new += 1

        view_rows.append({
            "index": i,
            "serial": r["serial_number"],
            "synthetic": r["synthetic"],
            "common_name": r["common_name"],
            "domains": r["domains"],
            "not_after": na,
            "not_after_raw": r["not_after_raw"],
            "days": days,
            "status": status,
            "problems": r["problems"],
            "warnings": r["warnings"],
            "action": "update" if existing else "new",
            "old_after": existing.not_after if existing else None,
            "changed": changed,
            "importable": importable,
        })
        payload.append({
            "index": i,
            "serial_number": r["serial_number"],
            "common_name": r["common_name"],
            "name_value": r["name_value"],
            "not_before": r["not_before"].isoformat() if r["not_before"] else None,
            "not_after": na.isoformat() if na else None,
            "issuer_name": r["issuer_name"],
            "notes": r["notes"],
            "importable": importable,
        })

    return render_template(
        "certificates/import_review.html",
        rows=view_rows,
        payload_json=json.dumps(payload),
        counts={"total": len(rows), "new": n_new, "update": n_update,
                "problem": n_problem, "nodate": n_nodate},
    )


@certificates_bp.route("/importar/confirmar", methods=["POST"])
@module_required("certificados", manage=True)
def import_confirm():
    """Grava apenas as linhas selecionadas na tela de revisão."""
    import json

    from app.utils.cert_import import import_selected_rows

    try:
        payload = json.loads(request.form.get("payload") or "[]")
    except ValueError:
        flash("Dados de revisão inválidos. Reenvie a planilha.", "danger")
        return redirect(url_for("certificates.import_certificates_view"))

    selected = set(request.form.getlist("rows"))
    chosen = [p for p in payload
              if str(p.get("index")) in selected and p.get("importable")]
    if not chosen:
        flash("Nenhuma linha selecionada para importar.", "warning")
        return redirect(url_for("certificates.import_certificates_view"))

    summary = import_selected_rows(chosen)
    _flash_summary(summary)
    return redirect(url_for("certificates.list_certificates"))


# ---------------------------------------------------------------------------
# Envio manual de alertas — tela de revisão (alcance + destinatários) e envio
# ---------------------------------------------------------------------------
def _parse_scope(source):
    """Lê o alcance (vencidos + janela de dias) de request.args/form."""
    include_expired = source.get("expired", "1") in ("1", "true", "on")
    days_raw = source.get("days", "30")
    within_days = None
    if days_raw not in ("", "none", "0"):
        try:
            within_days = int(days_raw)
        except ValueError:
            within_days = 30
    return include_expired, within_days


@certificates_bp.route("/alertas")
@module_required("certificados", manage=True)
def alerts_review():
    from app.utils.cert_alerts import recipient_choices, select_certificates

    include_expired, within_days = _parse_scope(request.args)
    certs = select_certificates(include_expired=include_expired, within_days=within_days)
    recipients = recipient_choices()
    return render_template(
        "certificates/alerts.html",
        certs=certs,
        recipients=recipients,
        scope={"expired": include_expired, "days": within_days},
        day_options=[1, 7, 15, 30],
    )


@certificates_bp.route("/alertas/enviar", methods=["POST"])
@module_required("certificados", manage=True)
def send_alerts():
    from app.utils.cert_alerts import select_certificates, send_manual

    include_expired, within_days = _parse_scope(request.form)
    certs = select_certificates(include_expired=include_expired, within_days=within_days)
    # Somente os destinatários que o admin deixou marcados.
    chosen = [e.strip().lower() for e in request.form.getlist("recipients") if e.strip()]

    if not certs:
        flash("Nenhum certificado no alcance selecionado.", "warning")
        return redirect(url_for("certificates.alerts_review",
                                expired="1" if include_expired else "0",
                                days=within_days if within_days is not None else "none"))
    if not chosen:
        flash("Selecione ao menos um destinatário.", "warning")
        return redirect(url_for("certificates.alerts_review",
                                expired="1" if include_expired else "0",
                                days=within_days if within_days is not None else "none"))

    ok, err = send_manual(certs, chosen)
    if ok:
        flash(f"Alerta enviado: {len(certs)} certificado(s) para "
              f"{len(chosen)} destinatário(s).", "success")
    else:
        flash(f"Falha ao enviar: {err}", "danger")
    return redirect(url_for("certificates.list_certificates"))
