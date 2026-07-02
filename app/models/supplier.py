"""Model de fornecedor."""
from datetime import datetime

from app.extensions import db
from app.utils.audit_listener import audit_model


@audit_model
class Supplier(db.Model):
    __tablename__ = "suppliers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False, index=True)
    cnpj = db.Column(db.String(20), nullable=True)
    contact_name = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(40), nullable=True)
    email = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    assets = db.relationship("Asset", back_populates="supplier")

    def __repr__(self):
        return f"<Supplier {self.name}>"
