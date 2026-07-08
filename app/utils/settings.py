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
    "company_name": "Warren IT Hub",
    "warranty_window_days": "30",
    "currency_symbol": "R$",
}

# Chaves de configuração de e-mail (SMTP). São guardadas na tabela settings
# como as demais, MAS nunca devem ir para o contexto público de templates
# (a senha é sensível) — ver public_settings().
MAIL_KEYS = (
    "mail_server", "mail_port", "mail_use_tls", "mail_use_ssl",
    "mail_username", "mail_password", "mail_from", "mail_from_name",
    "mail_alert_extra",
)


def _as_bool(value, default=False):
    """Interpreta valores de banco ('true'/'1') e do .env (bool) como bool."""
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    return str(value).strip().lower() in ("1", "true", "yes", "on")


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


def public_settings():
    """Parâmetros seguros para expor no contexto de templates (SETTINGS).

    Remove as chaves de e-mail (mail_*), que contêm dados sensíveis como a
    senha do SMTP e não devem ficar acessíveis nos templates."""
    return {k: v for k, v in current_settings().items() if k not in MAIL_KEYS}


def mail_settings():
    """Configuração de e-mail resolvida: valor do banco tem prioridade;
    se ausente, cai no .env (config.py). Retorna um dict pronto p/ o mailer.
    """
    from flask import current_app
    cfg = current_app.config
    s = current_settings()

    def pick(key, cfg_key, default=None):
        v = s.get(key)
        if v is None or v == "":
            v = cfg.get(cfg_key, default)
        return v

    username = pick("mail_username", "MAIL_USERNAME")
    try:
        port = int(pick("mail_port", "MAIL_PORT", 587) or 587)
    except (TypeError, ValueError):
        port = 587
    return {
        "server": pick("mail_server", "MAIL_SERVER", "smtp.gmail.com"),
        "port": port,
        "use_tls": _as_bool(pick("mail_use_tls", "MAIL_USE_TLS", True), True),
        "use_ssl": _as_bool(pick("mail_use_ssl", "MAIL_USE_SSL", False), False),
        "username": username,
        "password": pick("mail_password", "MAIL_PASSWORD"),
        "from": pick("mail_from", "MAIL_FROM") or username,
        "from_name": pick("mail_from_name", "MAIL_FROM_NAME", "Warren IT Hub"),
        "alert_extra": pick("mail_alert_extra", "MAIL_ALERT_EXTRA"),
    }
