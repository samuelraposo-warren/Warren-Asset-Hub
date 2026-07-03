"""Model de usuário do sistema (autenticação e autorização)."""
from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.models.enums import UserRole


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    role = db.Column(
        db.Enum(UserRole), nullable=False, default=UserRole.VIEWER
    )

    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)

    # IP do último acesso (suporta IPv6, por isso 45 caracteres).
    ip_address = db.Column(db.String(45), nullable=True)

    # Preferências pessoais em JSON: layout do dashboard, aparência, etc.
    # (não é auditado — ver observação abaixo).
    preferences = db.Column(db.JSON, nullable=True)

    # Força a troca de senha no próximo login (senha temporária / redefinida).
    must_change_password = db.Column(db.Boolean, nullable=False, default=False)

    # --- Senha -------------------------------------------------------
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # --- Conveniências de papel -------------------------------------
    @property
    def is_admin(self):
        return self.role == UserRole.ADMIN

    def has_role(self, *roles):
        return self.role in roles

    # --- Preferências (JSON) ----------------------------------------
    def get_pref(self, key, default=None):
        prefs = self.preferences or {}
        return prefs.get(key, default)

    def set_pref(self, key, value):
        # Reatribui o dict inteiro para o SQLAlchemy detectar a mudança
        # (colunas JSON não rastreiam mutação in-place por padrão).
        prefs = dict(self.preferences or {})
        prefs[key] = value
        self.preferences = prefs

    def __repr__(self):
        return f"<User {self.email} ({self.role.value})>"
