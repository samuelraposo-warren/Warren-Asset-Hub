"""Acesso aos parâmetros do sistema (tabela settings) com defaults.

Uso típico:
    from app.utils.settings import current_settings, set_setting
    cfg = current_settings()      # dict com todos os parâmetros (defaults + banco)
    cfg["company_name"]

Os valores são cacheados em ``flask.g`` durante a requisição para evitar
múltiplas idas ao banco (o filtro brl, o dashboard e o layout usam isso).
"""
from flask import g

# Parâmetros conhecidos e seus valores padrão (sempre string).
SYSTEM_DEFAULTS = {
    "company_name": "Inventário de TI",
    "warranty_window_days": "30",
    "currency_symbol": "R$",
}


def _load_from_db():
    """Lê a tabela settings e mescla sobre os defaults. Tolerante a falhas
    (ex.: tabela ainda não criada) — nesse caso retorna só os defaults."""
    values = dict(SYSTEM_DEFAULTS)
    try:
        from app.models.setting import Setting
        for row in Setting.query.all():
            if row.value is not None:
                values[row.key] = row.value
    except Exception:  # noqa: BLE001 — nunca deve quebrar a página
        pass
    return values


def current_settings():
    """Retorna o dict de parâmetros, cacheado na requisição atual."""
    cached = getattr(g, "_system_settings", None)
    if cached is None:
        cached = _load_from_db()
        try:
            g._system_settings = cached
        except Exception:  # noqa: BLE001 — fora de contexto de request
            pass
    return cached


def get_setting(key, default=None):
    return current_settings().get(key, default if default is not None
                                  else SYSTEM_DEFAULTS.get(key))


def warranty_window_days():
    try:
        return int(current_settings().get("warranty_window_days", 30))
    except (TypeError, ValueError):
        return 30


def set_setting(key, value):
    """Cria/atualiza um parâmetro e invalida o cache da requisição."""
    from app.extensions import db
    from app.models.setting import Setting

    row = Setting.query.filter_by(key=key).first()
    if row is None:
        row = Setting(key=key)
        db.session.add(row)
    row.value = "" if value is None else str(value)
    db.session.commit()
    # Invalida cache para refletir imediatamente na mesma requisição.
    if hasattr(g, "_system_settings"):
        del g._system_settings
