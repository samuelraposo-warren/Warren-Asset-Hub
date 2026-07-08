"""Motor de alertas de vencimento de certificados.

Regras (definidas com o time):
  - Antecedências: 30, 15, 7 e 1 dia antes; no dia do vencimento; e aviso
    DIÁRIO enquanto estiver vencido (e ainda ativo).
  - Destinatários: todos os usuários com acesso ao módulo "Certificados"
    (Gestores/ADMIN + quem tem UserModuleAccess), mais o MAIL_ALERT_EXTRA.
  - Anti-spam: cada estágio pré-vencimento é enviado uma única vez
    (guardado em last_alert_stage). O estágio "vencido" reenvia no máximo
    uma vez por dia (guardado em last_alert_sent_on).

O disparo é feito pelo comando ``flask send-cert-alerts`` (agendável no
Windows Task Scheduler via Enviar_Alertas_Certificados.bat).
"""
from datetime import date

from app.extensions import db
from app.models.certificate import Certificate
from app.utils.mailer import send_email

# Estágios pré-vencimento (dias -> chave). Ordem do mais próximo ao mais longe.
STAGE_THRESHOLDS = [(1, "1d"), (7, "7d"), (15, "15d"), (30, "30d")]

STAGE_LABELS = {
    "30d": "vence em 30 dias",
    "15d": "vence em 15 dias",
    "7d": "vence em 7 dias",
    "1d": "vence amanhã",
    "expiry": "vence hoje",
    "expired": "VENCIDO",
}


def stage_for(days):
    """Retorna o estágio de alerta para 'dias até vencer' (ou None)."""
    if days is None:
        return None
    if days < 0:
        return "expired"
    if days == 0:
        return "expiry"
    for limit, key in STAGE_THRESHOLDS:  # 1d, 7d, 15d, 30d
        if days <= limit:
            return key
    return None


def _collect_recipients():
    """{email: nome} de quem tem acesso ao módulo 'Certificados' (+ extra).

    = todos os ADMIN (Gestores de TI) + usuários com UserModuleAccess ao
    módulo de slug 'certificados'. Sempre ativos e com e-mail preenchido.
    """
    from app.models.access import Module, UserModuleAccess
    from app.models.enums import UserRole
    from app.models.user import User

    emails = {}

    # Gestores (ADMIN) — acesso total ao Centralizador.
    for u in User.query.filter_by(role=UserRole.ADMIN, is_active=True).all():
        if u.email:
            emails[u.email.lower()] = u.name

    module = Module.query.filter_by(slug="certificados").first()
    if module is not None:
        rows = (
            db.session.query(User)
            .join(UserModuleAccess, UserModuleAccess.user_id == User.id)
            .filter(UserModuleAccess.module_id == module.id, User.is_active.is_(True))
            .all()
        )
        for u in rows:
            if u.email:
                emails[u.email.lower()] = u.name

    # Cópia fixa opcional (lista do time etc.) — banco com fallback ao .env.
    from app.utils.settings import mail_settings
    extra = mail_settings().get("alert_extra")
    if extra:
        for addr in str(extra).replace(";", ",").split(","):
            addr = addr.strip()
            if addr:
                emails.setdefault(addr.lower(), addr)

    return emails


def alert_recipients():
    """Lista de e-mails (para o disparo automático)."""
    return list(_collect_recipients().keys())


def recipient_choices():
    """Lista [{'email','name'}] para a tela de revisão de envio manual."""
    return [{"email": e, "name": n} for e, n in sorted(_collect_recipients().items())]


def select_certificates(include_expired=True, within_days=30):
    """Certificados ativos que se encaixam no alcance escolhido.

    :param include_expired: inclui os já vencidos.
    :param within_days: inclui os que vencem em até N dias (None = nenhum).
    Ordenados do mais urgente ao menos urgente.
    """
    certs = (
        Certificate.query.filter(
            Certificate.is_active.is_(True),
            Certificate.not_after.isnot(None),
        )
        .order_by(Certificate.not_after.asc())
        .all()
    )
    out = []
    for c in certs:
        d = c.days_to_expiry
        if d is None:
            continue
        if d < 0:
            if include_expired:
                out.append(c)
        elif within_days is not None and d <= within_days:
            out.append(c)
    return out


def build_digest_email(certs):
    """Monta (assunto, html, texto) com um resumo de vários certificados."""
    total = len(certs)
    subject = f"[Certificados] {total} certificado(s) requer(em) atenção"

    def _row_html(c):
        badge = {"expired": "#c0392b", "critical": "#e67e22",
                 "warning": "#d4a017"}.get(c.status_key, "#888")
        d = c.days_to_expiry
        quando = (f"vencido há {abs(d)} d" if d is not None and d < 0
                  else "vence hoje" if d == 0 else f"em {d} d")
        cn = c.common_name or (c.domain_list[0] if c.domain_list else "—")
        return (
            f"<tr>"
            f"<td style='padding:6px 8px;border-bottom:1px solid #eee'>{cn}</td>"
            f"<td style='padding:6px 8px;border-bottom:1px solid #eee'>"
            f"{_fmt_date(c.not_after)}</td>"
            f"<td style='padding:6px 8px;border-bottom:1px solid #eee;"
            f"color:{badge};font-weight:600'>{quando}</td>"
            f"</tr>"
        )

    rows = "".join(_row_html(c) for c in certs) or (
        "<tr><td colspan='3' style='padding:8px'>Nenhum.</td></tr>")

    html = f"""\
<div style="font-family:Inter,Arial,sans-serif;max-width:680px;margin:auto">
  <h2 style="margin:0 0 4px">{_company_name()} · Certificados</h2>
  <p style="color:#666;margin:0 0 14px">{total} certificado(s) requer(em) atenção:</p>
  <table style="width:100%;border-collapse:collapse;font-size:14px">
    <thead><tr>
      <th style="text-align:left;padding:6px 8px;border-bottom:2px solid #ccc">Certificado</th>
      <th style="text-align:left;padding:6px 8px;border-bottom:2px solid #ccc">Vence em</th>
      <th style="text-align:left;padding:6px 8px;border-bottom:2px solid #ccc">Situação</th>
    </tr></thead>
    <tbody>{rows}</tbody>
  </table>
  <p style="margin-top:16px;font-size:12px;color:#999">
    Enviado manualmente pelo Warren IT Hub.</p>
</div>"""

    lines = []
    for c in certs:
        d = c.days_to_expiry
        quando = (f"vencido há {abs(d)}d" if d is not None and d < 0
                  else "vence hoje" if d == 0 else f"em {d}d")
        cn = c.common_name or (c.domain_list[0] if c.domain_list else "—")
        lines.append(f"  - {cn} | {_fmt_date(c.not_after)} | {quando}")
    text = f"{total} certificado(s) requer(em) atenção:\n" + "\n".join(lines)
    return subject, html, text


def send_manual(certs, recipients):
    """Envia um resumo (digest) dos certificados aos destinatários escolhidos.

    Não altera o controle de anti-spam da automação (last_alert_*): é um
    envio ad-hoc, complementar ao disparo agendado. Retorna (ok, erro).
    """
    if not certs:
        return False, "Nenhum certificado no alcance selecionado."
    if not recipients:
        return False, "Selecione ao menos um destinatário."
    subject, html, text = build_digest_email(certs)
    return send_email(subject, recipients, html, text)


def _company_name():
    try:
        from app.utils.settings import get_setting
        return get_setting("company_name", "Centralizador de TI")
    except Exception:  # noqa: BLE001
        return "Centralizador de TI"


def _fmt_date(dt):
    return dt.strftime("%d/%m/%Y") if dt else "—"


def build_email(cert, stage):
    """Monta (assunto, html, texto) para um certificado num dado estágio."""
    label = STAGE_LABELS.get(stage, stage)
    cn = cert.common_name or (cert.domain_list[0] if cert.domain_list else "certificado")
    days = cert.days_to_expiry

    if stage == "expired":
        headline = f"Certificado VENCIDO há {abs(days)} dia(s)"
        color = "#c0392b"
    elif stage == "expiry":
        headline = "Certificado vence HOJE"
        color = "#c0392b"
    else:
        headline = f"Certificado {label} (em {days} dia(s))"
        color = "#e67e22" if days is not None and days <= 7 else "#d4a017"

    subject = f"[Certificados] {cn} — {label} (vence {_fmt_date(cert.not_after)})"

    domains = cert.domain_list
    domains_html = "".join(f"<li>{d}</li>" for d in domains) or "<li>—</li>"
    domains_txt = "\n".join(f"  - {d}" for d in domains) or "  -"

    html = f"""\
<div style="font-family:Inter,Arial,sans-serif;max-width:640px;margin:auto;
     border:1px solid #eee;border-radius:10px;overflow:hidden">
  <div style="background:{color};color:#fff;padding:16px 20px">
    <div style="font-size:13px;opacity:.85;text-transform:uppercase;letter-spacing:.05em">
      {_company_name()} · Certificados</div>
    <div style="font-size:20px;font-weight:600;margin-top:2px">{headline}</div>
  </div>
  <div style="padding:20px">
    <table style="width:100%;border-collapse:collapse;font-size:14px">
      <tr><td style="padding:6px 0;color:#666;width:160px">Nome comum (CN)</td>
          <td style="padding:6px 0;font-weight:600">{cn}</td></tr>
      <tr><td style="padding:6px 0;color:#666">Emissor</td>
          <td style="padding:6px 0">{cert.issuer_name or "—"}</td></tr>
      <tr><td style="padding:6px 0;color:#666">Válido de</td>
          <td style="padding:6px 0">{_fmt_date(cert.not_before)}</td></tr>
      <tr><td style="padding:6px 0;color:#666">Vence em</td>
          <td style="padding:6px 0;font-weight:600;color:{color}">
            {_fmt_date(cert.not_after)}</td></tr>
      <tr><td style="padding:6px 0;color:#666">Serial</td>
          <td style="padding:6px 0;font-family:monospace;font-size:12px">
            {cert.serial_number}</td></tr>
    </table>
    <div style="margin-top:14px;color:#666;font-size:13px">Domínios cobertos
      ({len(domains)}):</div>
    <ul style="margin:6px 0 0;padding-left:20px;font-size:13px;columns:2">
      {domains_html}
    </ul>
    <p style="margin-top:18px;font-size:12px;color:#999">
      Você recebeu este alerta por ter acesso ao módulo de Certificados no
      Centralizador de TI.</p>
  </div>
</div>"""

    text = (
        f"{headline}\n\n"
        f"CN: {cn}\n"
        f"Emissor: {cert.issuer_name or '—'}\n"
        f"Válido de: {_fmt_date(cert.not_before)}\n"
        f"Vence em: {_fmt_date(cert.not_after)}\n"
        f"Serial: {cert.serial_number}\n\n"
        f"Domínios ({len(domains)}):\n{domains_txt}\n"
    )
    return subject, html, text


def run_alerts(dry_run=False):
    """Verifica todos os certificados ativos e envia os alertas devidos.

    :returns: resumo {'checked', 'due', 'sent', 'failed', 'skipped',
              'no_recipients', 'details': [...]}
    """
    today = date.today()
    result = {"checked": 0, "due": 0, "sent": 0, "failed": 0,
              "skipped_recent": 0, "details": []}

    recipients = alert_recipients()
    result["recipients"] = recipients

    certs = Certificate.query.filter(
        Certificate.is_active.is_(True),
        Certificate.not_after.isnot(None),
    ).all()

    for cert in certs:
        result["checked"] += 1
        stage = stage_for(cert.days_to_expiry)
        if stage is None:
            continue  # ainda longe do vencimento (> 30 dias)
        result["due"] += 1

        # Anti-spam:
        if stage == "expired":
            # Reenvia no máximo uma vez por dia.
            if cert.last_alert_sent_on == today and cert.last_alert_stage == "expired":
                result["skipped_recent"] += 1
                continue
        else:
            # Estágio pré-vencimento: envia uma única vez.
            if cert.last_alert_stage == stage:
                result["skipped_recent"] += 1
                continue

        subject, html, text = build_email(cert, stage)
        entry = {"cert": cert.common_name, "serial": cert.serial_number,
                 "stage": stage, "days": cert.days_to_expiry}

        if dry_run:
            entry["result"] = "dry-run (não enviado)"
            result["details"].append(entry)
            continue

        if not recipients:
            entry["result"] = "sem destinatários"
            result["details"].append(entry)
            continue

        ok, err = send_email(subject, recipients, html, text)
        if ok:
            cert.last_alert_stage = stage
            cert.last_alert_sent_on = today
            result["sent"] += 1
            entry["result"] = "enviado"
        else:
            result["failed"] += 1
            entry["result"] = f"falha: {err}"
        result["details"].append(entry)

    if not dry_run:
        db.session.commit()
    return result
