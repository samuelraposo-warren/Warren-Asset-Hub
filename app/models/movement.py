"""Histórico de movimentações de ativos (troca de responsável/local)."""
from datetime import datetime

from app.extensions import db
from app.utils.audit_listener import audit_model


@audit_model
class AssetMovement(db.Model):
    __tablename__ = "asset_movements"

    id = db.Column(db.Integer, primary_key=True)

    asset_id = db.Column(
        db.Integer, db.ForeignKey("assets.id"), nullable=False, index=True
    )
    asset = db.relationship("Asset", back_populates="movements")

    from_employee_id = db.Column(
        db.Integer, db.ForeignKey("employees.id"), nullable=True
    )
    to_employee_id = db.Column(
        db.Integer, db.ForeignKey("employees.id"), nullable=True
    )
    from_employee = db.relationship("Employee", foreign_keys=[from_employee_id])
    to_employee = db.relationship("Employee", foreign_keys=[to_employee_id])

    from_location_id = db.Column(
        db.Integer, db.ForeignKey("locations.id"), nullable=True
    )
    to_location_id = db.Column(
        db.Integer, db.ForeignKey("locations.id"), nullable=True
    )
    from_location = db.relationship("Location", foreign_keys=[from_location_id])
    to_location = db.relationship("Location", foreign_keys=[to_location_id])

    moved_by_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=True
    )
    moved_by = db.relationship("User", foreign_keys=[moved_by_id])

    moved_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    reason = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<AssetMovement asset={self.asset_id} at={self.moved_at}>"
