"""Envio de e-mail via SMTP (biblioteca padrão smtplib).

Lê a configuração ``MAIL_*`` do app (config.py <- .env). Projetado para
Google Workspace/Gmail (smtp.gmail.com:587 STARTTLS + senha de app), mas
funciona com qualquer SMTP.

Tolerante a falhas: nunca levanta exceção para o chamador — retorna
``(ok: bool, erro: str|None)`` para que o job de alertas registre o
resultado sem quebrar.
"""
import smtplib
from email.message import EmailMessage
from email.utils import formataddr

from app.utils.settings import mail_settings


def mail_configured():
    """True se há credenciais suficientes para enviar e-mail (banco ou .env)."""
    cfg = mail_settings()
    return bool(cfg["server"] and cfg["username"] and cfg["password"])


def send_email(subject, recipients, html_body, text_body=None):
    """Envia um e-mail para uma lista de destinatários.

    A configuração vem do banco (tela de e-mail) com fallback ao .env.

    :param recipients: lista de e-mails (str). Vazio -> não faz nada.
    :returns: (ok, erro)
    """
    recipients = [r for r in (recipients or []) if r]
    if not recipients:
        return False, "Sem destinatários."

    cfg = mail_settings()
    if not (cfg["server"] and cfg["username"] and cfg["password"]):
        return False, ("E-mail não configurado. Preencha em "
                       "Configurações → E-mail (SMTP).")

    from_addr = cfg["from"] or cfg["username"]

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = formataddr((cfg["from_name"], from_addr))
    msg["To"] = ", ".join(recipients)
    msg.set_content(text_body or "Seu cliente de e-mail não suporta HTML.")
    msg.add_alternative(html_body, subtype="html")

    try:
        if cfg["use_ssl"]:
            with smtplib.SMTP_SSL(cfg["server"], cfg["port"], timeout=30) as smtp:
                smtp.login(cfg["username"], cfg["password"])
                smtp.send_message(msg)
        else:
            with smtplib.SMTP(cfg["server"], cfg["port"], timeout=30) as smtp:
                smtp.ehlo()
                if cfg["use_tls"]:
                    smtp.starttls()
                    smtp.ehlo()
                smtp.login(cfg["username"], cfg["password"])
                smtp.send_message(msg)
    except Exception as e:  # noqa: BLE001 — reporta sem quebrar o chamador
        return False, f"{type(e).__name__}: {e}"
    return True, None
