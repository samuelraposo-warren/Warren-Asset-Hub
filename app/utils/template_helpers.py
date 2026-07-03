"""Filtros e helpers de template (rótulos PT-BR, badges, formatação)."""
import re

from app.models.enums import AssetCondition, AssetStatus

# Extrai o ID de um arquivo do Google Drive a partir de vários formatos de URL
# (/file/d/<id>/view, open?id=<id>, uc?id=<id>, etc.).
_DRIVE_ID_RE = re.compile(r"(?:/d/|[?&]id=|/file/d/)([A-Za-z0-9_-]{20,})")


def _drive_img(url):
    """Converte um link de compartilhamento do Google Drive em uma URL que
    pode ser usada diretamente em <img>. Se não reconhecer, devolve a URL
    original (permite também links diretos de imagem)."""
    if not url:
        return ""
    m = _DRIVE_ID_RE.search(url)
    if m:
        return f"https://drive.google.com/thumbnail?id={m.group(1)}&sz=w1000"
    return url

# Auditoria
AUDIT_LABELS = {"CREATE": "Criação", "UPDATE": "Atualização", "DELETE": "Exclusão"}
AUDIT_BADGES = {
    "CREATE": "badge-active",
    "UPDATE": "badge-loaned",
    "DELETE": "badge-defective",
}

# Manutenção
MAINTENANCE_LABELS = {
    "PREVENTIVE": "Preventiva",
    "CORRECTIVE": "Corretiva",
    "UPGRADE": "Upgrade",
}
MAINTENANCE_BADGES = {
    "PREVENTIVE": "badge-active",
    "CORRECTIVE": "badge-maintenance",
    "UPGRADE": "badge-loaned",
}

# Rótulos em português (chave = nome do membro do enum).
STATUS_LABELS = {
    "ACTIVE": "Ativo",
    "INACTIVE": "Inativo",
    "MAINTENANCE": "Manutenção",
    "DISPOSED": "Descartado",
    "STOLEN": "Roubado",
    "LOANED": "Emprestado",
}
STATUS_BADGES = {
    "ACTIVE": "badge-active",
    "INACTIVE": "badge-inactive",
    "MAINTENANCE": "badge-maintenance",
    "DISPOSED": "badge-disposed",
    "STOLEN": "badge-stolen",
    "LOANED": "badge-loaned",
}
CONDITION_LABELS = {
    "NEW": "Novo",
    "GOOD": "Bom",
    "FAIR": "Regular",
    "POOR": "Ruim",
    "DEFECTIVE": "Defeituoso",
}
CONDITION_BADGES = {
    "NEW": "badge-active",
    "GOOD": "badge-active",
    "FAIR": "badge-maintenance",
    "POOR": "badge-maintenance",
    "DEFECTIVE": "badge-defective",
}


def _brl(value):
    if value is None:
        return "—"
    # Símbolo de moeda vem dos parâmetros do sistema (default "R$").
    try:
        from app.utils.settings import get_setting
        symbol = get_setting("currency_symbol", "R$")
    except Exception:  # noqa: BLE001
        symbol = "R$"
    # Formata no padrão brasileiro: 1.234,56
    formatted = f"{float(value):,.2f}"
    return f"{symbol} " + formatted.replace(",", "X").replace(".", ",").replace("X", ".")


def _date_br(value):
    return value.strftime("%d/%m/%Y") if value else "—"


def _humanize(value):
    """Enum.value 'ALL_IN_ONE' -> 'All in one'."""
    if value is None:
        return "—"
    return str(value).replace("_", " ").capitalize()


def register_template_helpers(app):
    app.add_template_filter(lambda v: STATUS_LABELS.get(v, v), "status_label")
    app.add_template_filter(lambda v: STATUS_BADGES.get(v, "badge-neutral"), "status_badge")
    app.add_template_filter(lambda v: CONDITION_LABELS.get(v, v), "condition_label")
    app.add_template_filter(lambda v: CONDITION_BADGES.get(v, "badge-neutral"), "condition_badge")
    app.add_template_filter(_brl, "brl")
    app.add_template_filter(_date_br, "date_br")
    app.add_template_filter(_humanize, "humanize")
    app.add_template_filter(_drive_img, "drive_img")
    app.add_template_filter(lambda v: AUDIT_LABELS.get(v, v), "audit_label")
    app.add_template_filter(lambda v: AUDIT_BADGES.get(v, "badge-neutral"), "audit_badge")
    app.add_template_filter(lambda v: MAINTENANCE_LABELS.get(v, v), "maintenance_label")
    app.add_template_filter(lambda v: MAINTENANCE_BADGES.get(v, "badge-neutral"), "maintenance_badge")

    @app.context_processor
    def inject_enums():
        from app.models.enums import AuditAction, MaintenanceType
        from app.utils.registry_config import REGISTRY
        from app.utils.settings import current_settings

        registry_menu = [
            {"slug": slug, "plural": cfg["plural"], "icon": cfg["icon"]}
            for slug, cfg in REGISTRY.items()
        ]
        return {
            "AssetStatus": AssetStatus,
            "AssetCondition": AssetCondition,
            "AuditAction": AuditAction,
            "MaintenanceType": MaintenanceType,
            "STATUS_LABELS": STATUS_LABELS,
            "CONDITION_LABELS": CONDITION_LABELS,
            "REGISTRY_MENU": registry_menu,
            "SETTINGS": current_settings(),
        }

    @app.context_processor
    def inject_notifications():
        from flask_login import current_user
        if not getattr(current_user, "is_authenticated", False):
            return {"NOTIFICATIONS": {"count": 0, "alerts": []}}
        from app.utils.notifications import build_notifications
        return {"NOTIFICATIONS": build_notifications()}
