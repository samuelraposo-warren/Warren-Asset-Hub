"""Blueprint de autenticação: login e logout."""
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


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    # Já autenticado -> vai direto para o painel.
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        remember = bool(request.form.get("remember"))

        user = User.query.filter_by(email=email).first()

        # Mesma mensagem para e-mail inexistente ou senha errada
        # (não revela quais e-mails existem).
        if user is None or not user.check_password(password):
            flash("E-mail ou senha inválidos.", "danger")
            return render_template("auth/login.html", email=email), 401

        if not user.is_active:
            flash("Usuário inativo. Contate o administrador.", "warning")
            return render_template("auth/login.html", email=email), 403

        login_user(user, remember=remember)

        # Registra último acesso e IP (User não é auditado, então isso
        # não gera ruído no audit_log).
        user.last_login = datetime.utcnow()
        user.ip_address = request.remote_addr
        db.session.commit()

        # Redireciona para o "next" apenas se for um caminho interno
        # (evita open redirect).
        next_page = request.args.get("next")
        if not next_page or not next_page.startswith("/"):
            next_page = url_for("main.dashboard")
        return redirect(next_page)

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Sessão encerrada com sucesso.", "info")
    return redirect(url_for("auth.login"))
