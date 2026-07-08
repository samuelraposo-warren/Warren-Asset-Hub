"""Camada de acessos do Centralizador Warren.

Estrutura:
  Sub-setor de TI (Acessos, Service Desk, Infra, Cyber)
    └─ Módulo (centralizador) — ex.: Inventário de Máquinas, Certificados…
         └─ Acesso por usuário (Ver / Gerenciar)

O "Gestor de TI" (User.role == ADMIN) tem acesso total e administra tudo;
para os demais usuários, o acesso é concedido por módulo (UserModuleAccess).
"""
from datetime import datetime

from app.extensions import db
from app.models.enums import ModuleAccessLevel
from app.utils.audit_listener import audit_model


@audit_model
class ITSubsector(db.Model):
    """Sub-setor dentro de TI (ex.: Acessos, Service Desk, Infra, Cyber)."""
    __tablename__ = "it_subsectors"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    slug = db.Column(db.String(80), nullable=False, unique=True, index=True)
    description = db.Column(db.String(255), nullable=True)
    icon = db.Column(db.String(40), nullable=True)          # ex.: "bi-shield-lock"

    is_active = db.Column(db.Boolean, nullable=False, default=True)

    modules = db.relationship("Module", back_populates="subsector")

    def __repr__(self):
        return f"<ITSubsector {self.slug}>"


@audit_model
class Module(db.Model):
    """Módulo/centralizador — uma funcionalidade vinculada a um sub-setor."""
    __tablename__ = "it_modules"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    slug = db.Column(db.String(80), nullable=False, unique=True, index=True)
    description = db.Column(db.String(255), nullable=True)
    icon = db.Column(db.String(40), nullable=True)          # ex.: "bi-hdd-stack"
    # Endpoint do Flask que abre o módulo (ex.: "assets.list_assets").
    # Nulo = módulo ainda "em breve" (aparece, mas sem link).
    endpoint = db.Column(db.String(120), nullable=True)

    subsector_id = db.Column(
        db.Integer, db.ForeignKey("it_subsectors.id"), nullable=True
    )
    subsector = db.relationship("ITSubsector", back_populates="modules")

    sort_order = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    def __repr__(self):
        return f"<Module {self.slug}>"


@audit_model
class UserModuleAccess(db.Model):
    """Acesso de um usuário a um módulo, com nível (Ver / Gerenciar)."""
    __tablename__ = "user_module_access"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    module_id = db.Column(db.Integer, db.ForeignKey("it_modules.id"), nullable=False, index=True)
    level = db.Column(
        db.Enum(ModuleAccessLevel), nullable=False, default=ModuleAccessLevel.VIEW
    )
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship("User", backref=db.backref("module_access", cascade="all, delete-orphan"))
    module = db.relationship("Module")

    __table_args__ = (
        db.UniqueConstraint("user_id", "module_id", name="uq_user_module"),
    )

    def __repr__(self):
        return f"<UserModuleAccess u={self.user_id} m={self.module_id} {self.level.value}>"
