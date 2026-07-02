"""Models centrais: Asset (ativo) e AssetType (categoria)."""
from datetime import datetime

from app.extensions import db
from app.models.enums import AssetCondition, AssetStatus
from app.utils.audit_listener import audit_model


@audit_model
class AssetType(db.Model):
    __tablename__ = "asset_types"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False, unique=True)
    slug = db.Column(db.String(80), nullable=False, unique=True, index=True)
    description = db.Column(db.String(255), nullable=True)

    assets = db.relationship("Asset", back_populates="asset_type")

    def __repr__(self):
        return f"<AssetType {self.slug}>"


@audit_model
class Asset(db.Model):
    __tablename__ = "assets"

    id = db.Column(db.Integer, primary_key=True)

    # Patrimônio / etiqueta (ex.: TI-2024-001).
    asset_tag = db.Column(db.String(60), unique=True, nullable=False, index=True)
    serial_number = db.Column(db.String(120), nullable=True, index=True)

    asset_type_id = db.Column(
        db.Integer, db.ForeignKey("asset_types.id"), nullable=False
    )
    asset_type = db.relationship("AssetType", back_populates="assets")

    brand = db.Column(db.String(80), nullable=True)
    model = db.Column(db.String(120), nullable=True)

    status = db.Column(
        db.Enum(AssetStatus), nullable=False, default=AssetStatus.ACTIVE, index=True
    )
    condition = db.Column(
        db.Enum(AssetCondition), nullable=False, default=AssetCondition.GOOD
    )

    purchase_date = db.Column(db.Date, nullable=True)
    warranty_expiry_date = db.Column(db.Date, nullable=True)
    purchase_price = db.Column(db.Numeric(12, 2), nullable=True)

    supplier_id = db.Column(
        db.Integer, db.ForeignKey("suppliers.id"), nullable=True
    )
    supplier = db.relationship("Supplier", back_populates="assets")
    invoice_number = db.Column(db.String(80), nullable=True)  # nota fiscal

    location_id = db.Column(
        db.Integer, db.ForeignKey("locations.id"), nullable=True
    )
    location = db.relationship("Location", back_populates="assets")

    assigned_to_id = db.Column(
        db.Integer, db.ForeignKey("employees.id"), nullable=True
    )
    assigned_to = db.relationship("Employee", back_populates="assets")

    notes = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
    created_by_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=True
    )
    created_by = db.relationship("User", foreign_keys=[created_by_id])

    # Soft delete: registros nunca são removidos fisicamente.
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)

    # --- Specs (uma delas será preenchida conforme o tipo) ----------
    notebook_spec = db.relationship(
        "NotebookSpec", back_populates="asset", uselist=False,
        cascade="all, delete-orphan",
    )
    desktop_spec = db.relationship(
        "DesktopSpec", back_populates="asset", uselist=False,
        cascade="all, delete-orphan",
    )
    monitor_spec = db.relationship(
        "MonitorSpec", back_populates="asset", uselist=False,
        cascade="all, delete-orphan",
    )
    printer_spec = db.relationship(
        "PrinterSpec", back_populates="asset", uselist=False,
        cascade="all, delete-orphan",
    )
    server_spec = db.relationship(
        "ServerSpec", back_populates="asset", uselist=False,
        cascade="all, delete-orphan",
    )
    network_spec = db.relationship(
        "NetworkSpec", back_populates="asset", uselist=False,
        cascade="all, delete-orphan",
    )
    peripheral_spec = db.relationship(
        "PeripheralSpec", back_populates="asset", uselist=False,
        cascade="all, delete-orphan",
    )

    # --- Históricos --------------------------------------------------
    movements = db.relationship(
        "AssetMovement", back_populates="asset", cascade="all, delete-orphan"
    )
    maintenance_records = db.relationship(
        "MaintenanceRecord", back_populates="asset", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Asset {self.asset_tag} ({self.status.value})>"
