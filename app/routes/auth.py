"""Blueprint de autenticação: login e logout."""
import time
from datetime import datetime

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user

from app.extensions import db
from app.models.user import User

auth_bp = Blueprint("auth", __name__)

# --- Proteção simples contra força bruta no login (em memória) ---------
# Bloqueia por IP após muitas tentativas falhas numa janela de tempo.
_MAX_FAILS = 5
_WINDOW_SECONDS = 300  # 5 minutos
_FAILED_ATTEMPTS = {}   # ip -> [timestamps]


def _recent_fails(ip):
    now = time.time()
    fails = [t for t in _FAILED_ATTEMPTS.get(ip, []) if now - t < _WINDOW_SECONDS]
    _FAILED_ATTEMPTS[ip] = fails
    return fails


def _is_blocked(ip):
    return len(_recent_fails(ip)) >= _MAX_FAILS


def _register_fail(ip):
    _FAILED_ATTEMPTS.setdefault(ip, []).append(time.time())


def _clear_fails(ip):
    _FAILED_ATTEMPTS.pop(ip, None)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    # Já autenticado -> vai direto para o painel.
    if current_user.is_authenticated:
        return redirect(url_for("main.hub"))

    if request.method == "POST":
        ip = request.remote_addr or "unknown"

        # Bloqueio temporário após muitas tentativas falhas.
        if _is_blocked(ip):
            flash(
                "Muitas tentativas de login. Aguarde alguns minutos e tente novamente.",
                "danger",
            )
            return render_template("auth/login.html", email=request.form.get("email")), 429

        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        remember = bool(request.form.get("remember"))

        user = User.query.filter_by(email=email).first()

        # Mesma mensagem para e-mail inexistente ou senha errada
        # (não revela quais e-mails existem).
        if user is None or not user.check_password(password):
            _register_fail(ip)
            flash("E-mail ou senha inválidos.", "danger")
            return render_template("auth/login.html", email=email), 401

        if not user.is_active:
            flash("Usuário inativo. Contate o administrador.", "warning")
            return render_template("auth/login.html", email=email), 403

        login_user(user, remember=remember)
        _clear_fails(ip)

        # Registra último acesso e IP (User não é auditado, então isso
        # não gera ruído no audit_log).
        user.last_login = datetime.utcnow()
        user.ip_address = request.remote_addr
        db.session.commit()

        # Redireciona para o "next" apenas se for um caminho interno
        # (evita open redirect).
        next_page = request.args.get("next")
        if not next_page or not next_page.startswith("/"):
            next_page = url_for("main.hub")
        return redirect(next_page)

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Sessão encerrada com sucesso.", "info")
    return redirect(url_for("auth.login"))
