"""Configurações do sistema e da conta.

Seções:
  * Minha conta      — editar o próprio nome.
  * Trocar senha     — exige a senha atual.
  * Aparência        — preferências pessoais (salvas em users.preferences).
  * Parâmetros       — configurações globais (só ADMIN, tabela settings).
  * Atalhos de admin — links rápidos p/ Usuários e Auditoria (só ADMIN).
"""
from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required

from app.extensions import db
from app.models.enums import UserRole
from app.utils.settings import current_settings, set_setting

settings_bp = Blueprint("settings", __name__, url_prefix="/settings")

# Opções de aparência oferecidas.
ROWS_OPTIONS = [10, 20, 30, 50, 100]
DENSITY_OPTIONS = ["comfortable", "compact"]


def _appearance():
    """Preferências de aparência do usuário atual (com defaults)."""
    ap = current_user.get_pref("appearance", {}) or {}
    return {
        "rows_per_page": int(ap.get("rows_per_page", 30)),
        "density": ap.get("density", "comfortable"),
    }


@settings_bp.route("/")
@login_required
def index():
    return render_template(
        "settings/index.html",
        appearance=_appearance(),
        rows_options=ROWS_OPTIONS,
        density_options=DENSITY_OPTIONS,
        sys=current_settings(),
        is_admin=current_user.is_admin,
    )


@settings_bp.route("/account", methods=["POST"])
@login_required
def update_account():
    name = (request.form.get("name") or "").strip()
    if not name:
        flash("Informe seu nome.", "danger")
    else:
        current_user.name = name
        db.session.commit()
        flash("Dados da conta atualizados.", "success")
    return redirect(url_for("settings.index"))


@settings_bp.route("/password", methods=["POST"])
@login_required
def change_password():
    current = request.form.get("current_password") or ""
    new = request.form.get("new_password") or ""
    confirm = request.form.get("confirm_password") or ""

    if not current_user.check_password(current):
        flash("Senha atual incorreta.", "danger")
    elif len(new) < 6:
        flash("A nova senha deve ter ao menos 6 caracteres.", "danger")
    elif new != confirm:
        flash("A confirmação não confere com a nova senha.", "danger")
    else:
        current_user.set_password(new)
        db.session.commit()
        flash("Senha alterada com sucesso.", "success")
    return redirect(url_for("settings.index"))


@settings_bp.route("/appearance", methods=["POST"])
@login_required
def update_appearance():
    try:
        rows = int(request.form.get("rows_per_page") or 30)
    except ValueError:
        rows = 30
    if rows not in ROWS_OPTIONS:
        rows = 30
    density = request.form.get("density") or "comfortable"
    if density not in DENSITY_OPTIONS:
        density = "comfortable"

    current_user.set_pref("appearance", {"rows_per_page": rows, "density": density})
    db.session.commit()
    flash("Preferências de aparência salvas.", "success")
    return redirect(url_for("settings.index"))


@settings_bp.route("/system", methods=["POST"])
@login_required
def update_system():
    if not current_user.is_admin:
        flash("Apenas administradores podem alterar os parâmetros do sistema.", "danger")
        return redirect(url_for("settings.index"))

    company = (request.form.get("company_name") or "").strip() or "Inventário de TI"
    currency = (request.form.get("currency_symbol") or "").strip() or "R$"
    try:
        window = int(request.form.get("warranty_window_days") or 30)
        if window < 1:
            window = 30
    except ValueError:
        window = 30

    set_setting("company_name", company)
    set_setting("currency_symbol", currency)
    set_setting("warranty_window_days", window)
    flash("Parâmetros do sistema atualizados.", "success")
    return redirect(url_for("settings.index"))
