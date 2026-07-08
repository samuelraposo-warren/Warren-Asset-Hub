"""Central de notificações (avisos calculados em tempo real).

Não há tabela de notificações: os avisos são derivados do estado atual do
inventário (garantias vencendo/vencidas, manutenções em aberto, ativos sem
responsável, furtados). Injetado em todas as páginas via context processor
para alimentar o sino no topo.
"""
from datetime import date, timedelta

from flask import url_for

# Mapa nível -> classe de badge do tema.
_BADGE = {
    "danger": "badge-defective",
    "warning": "badge-maintenance",
    "info": "badge-loaned",
}


def build_notifications():
    """Retorna {'count': N, 'items': [...]} com os avisos ativos.

    Tolerante a falhas: qualquer erro (ex.: banco indisponível) resulta em
    lista vazia, nunca quebra a página.
    """
    items = []
    try:  # noqa: PLR0915
        from app.models.asset import Asset
        from app.models.enums import AssetStatus
        from app.models.maintenance import MaintenanceRecord
        from app.utils.settings import warranty_window_days

        active = Asset.query.filter(Asset.is_active.is_(True))
        today = date.today()
        window = warranty_window_days()
        horizon = today + timedelta(days=window)

        expiring = active.filter(
            Asset.warranty_expiry_date.isnot(None),
            Asset.warranty_expiry_date >= today,
            Asset.warranty_expiry_date <= horizon,
        ).count()
        if expiring:
            items.append({
                "level": "warning",
                "icon": "bi-shield-exclamation",
                "text": f"Garantias vencendo nos próximos {window} dias",
                "count": expiring,
                "url": url_for("main.dashboard"),
            })

        expired = active.filter(
            Asset.warranty_expiry_date.isnot(None),
            Asset.warranty_expiry_date < today,
            Asset.status == AssetStatus.ACTIVE,
        ).count()
        if expired:
            items.append({
                "level": "danger",
                "icon": "bi-shield-x",
                "text": "Ativos com garantia vencida",
                "count": expired,
                "url": url_for("main.dashboard"),
            })

        open_maint = MaintenanceRecord.query.filter(
            MaintenanceRecord.finished_at.is_(None)
        ).count()
        if open_maint:
            items.append({
                "level": "info",
                "icon": "bi-tools",
                "text": "Manutenções em aberto",
                "count": open_maint,
                "url": url_for("maintenance.list_maintenance", status="open"),
            })

        unassigned = active.filter(
            Asset.assigned_to_id.is_(None),
            Asset.status == AssetStatus.ACTIVE,
        ).count()
        if unassigned:
            items.append({
                "level": "warning",
                "icon": "bi-person-dash",
                "text": "Ativos ativos sem responsável",
                "count": unassigned,
                "url": url_for("main.dashboard"),
            })

        stolen = active.filter(Asset.status == AssetStatus.STOLEN).count()
        if stolen:
            items.append({
                "level": "danger",
                "icon": "bi-exclamation-octagon",
                "text": "Ativos marcados como furtados/roubados",
                "count": stolen,
                "url": url_for("assets.list_assets", status="STOLEN"),
            })
    except Exception:  # noqa: BLE001 — avisos nunca devem quebrar a página
        return {"count": 0, "alerts": []}

    # --- Certificados (bloco isolado: tabela pode não existir ainda) -----
    try:
        from datetime import date as _date, timedelta as _td

        from app.models.certificate import Certificate

        _today = _date.today()
        _horizon = _today + _td(days=30)
        cert_active = Certificate.query.filter(Certificate.is_active.is_(True))

        cert_expiring = cert_active.filter(
            Certificate.not_after.isnot(None),
            Certificate.not_after >= _today,
            Certificate.not_after <= _horizon,
        ).count()
        if cert_expiring:
            items.append({
                "level": "warning",
                "icon": "bi-file-earmark-lock",
                "text": "Certificados vencendo nos próximos 30 dias",
                "count": cert_expiring,
                "url": url_for("certificates.list_certificates", status="expiring"),
            })

        cert_expired = cert_active.filter(
            Certificate.not_after.isnot(None),
            Certificate.not_after < _today,
        ).count()
        if cert_expired:
            items.append({
                "level": "danger",
                "icon": "bi-file-earmark-x",
                "text": "Certificados vencidos",
                "count": cert_expired,
                "url": url_for("certificates.list_certificates", status="expired"),
            })
    except Exception:  # noqa: BLE001 — não deve afetar os demais avisos
        pass

    # Anexa a classe de badge a cada item.
    for it in items:
        it["badge"] = _BADGE.get(it["level"], "badge-neutral")

    # Chave "alerts" (não usar "items": colide com o método dict.items no Jinja).
    return {"count": len(items), "alerts": items}
