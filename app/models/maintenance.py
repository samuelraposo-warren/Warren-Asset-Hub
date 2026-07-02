"""Registros de manutenção de ativos."""
from datetime import datetime

from app.extensions import db
from app.models.enums import MaintenanceType
from app.utils.audit_listener import audit_model


@audit_model
class MaintenanceRecord(db.Model):
    __tablename__ = "maintenance_records"

    id = db.Column(db.Integer, primary_key=True)

    asset_id = db.Column(
        db.Integer, db.ForeignKey("assets.id"), nullable=False, index=True
    )
    asset = db.relationship("Asset", back_populates="maintenance_records")

    type = db.Column(db.Enum(MaintenanceType), nullable=False)
    description = db.Column(db.Text, nullable=True)
    # Nome da empresa/técnico que executou.
    performed_by = db.Column(db.String(160), nullable=True)

    started_at = db.Column(db.DateTime, nullable=True)
    finished_at = db.Column(db.DateTime, nullable=True)
    cost = db.Column(db.Numeric(12, 2), nullable=True)

    created_by_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=True
    )
    created_by = db.relationship("User", foreign_keys=[created_by_id])
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<MaintenanceRecord asset={self.asset_id} {self.type.value}>"
