"""Model de log de auditoria.

IMPORTANTE: esta tabela é imutável — registros nunca devem ser atualizados
ou deletados. É preenchida automaticamente pelos event listeners em
``app/utils/audit_listener.py``. Este model NÃO é decorado com @audit_model
(auditar a própria auditoria causaria recursão).
"""
from datetime import datetime

from app.extensions import db
from app.models.enums import AuditAction


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)

    # Identificação do registro alterado.
    table_name = db.Column(db.String(120), nullable=False, index=True)
    record_id = db.Column(db.Integer, nullable=False, index=True)
    action = db.Column(db.Enum(AuditAction), nullable=False)

    # Quem alterou (nullable: alterações fora de request, ex. seeds/CLI).
    changed_by_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=True, index=True
    )
    changed_by = db.relationship("User", foreign_keys=[changed_by_id])
    changed_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, index=True
    )

    # Snapshots antes/depois (apenas colunas alteradas em UPDATE).
    old_values = db.Column(db.JSON, nullable=True)
    new_values = db.Column(db.JSON, nullable=True)

    # Contexto da requisição.
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(400), nullable=True)

    def __repr__(self):
        return (
            f"<AuditLog {self.action.value} {self.table_name}"
            f"#{self.record_id}>"
        )
