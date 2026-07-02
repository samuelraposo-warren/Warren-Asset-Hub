"""Especificações técnicas por tipo de ativo.

Cada spec tem um vínculo 1:1 com Asset via ``asset_id`` (FK único). Somente
a spec correspondente ao tipo do ativo é preenchida.
"""
from app.extensions import db
from app.models.enums import (
    ConnectionType,
    FormFactor,
    NetworkDeviceType,
    PanelType,
    PrinterType,
    StorageType,
)
from app.utils.audit_listener import audit_model


@audit_model
class NotebookSpec(db.Model):
    __tablename__ = "notebook_specs"

    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(
        db.Integer, db.ForeignKey("assets.id"), unique=True, nullable=False
    )
    asset = db.relationship("Asset", back_populates="notebook_spec")

    cpu = db.Column(db.String(120), nullable=True)
    ram_gb = db.Column(db.Integer, nullable=True)
    storage_gb = db.Column(db.Integer, nullable=True)
    storage_type = db.Column(db.Enum(StorageType), nullable=True)
    screen_size = db.Column(db.String(20), nullable=True)
    os = db.Column(db.String(80), nullable=True)
    os_version = db.Column(db.String(80), nullable=True)
    battery_health = db.Column(db.Integer, nullable=True)  # % de saúde

    def __repr__(self):
        return f"<NotebookSpec asset={self.asset_id}>"


@audit_model
class DesktopSpec(db.Model):
    __tablename__ = "desktop_specs"

    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(
        db.Integer, db.ForeignKey("assets.id"), unique=True, nullable=False
    )
    asset = db.relationship("Asset", back_populates="desktop_spec")

    cpu = db.Column(db.String(120), nullable=True)
    ram_gb = db.Column(db.Integer, nullable=True)
    storage_gb = db.Column(db.Integer, nullable=True)
    storage_type = db.Column(db.Enum(StorageType), nullable=True)
    has_gpu = db.Column(db.Boolean, nullable=False, default=False)
    gpu_model = db.Column(db.String(120), nullable=True)
    form_factor = db.Column(db.Enum(FormFactor), nullable=True)

    def __repr__(self):
        return f"<DesktopSpec asset={self.asset_id}>"


@audit_model
class MonitorSpec(db.Model):
    __tablename__ = "monitor_specs"

    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(
        db.Integer, db.ForeignKey("assets.id"), unique=True, nullable=False
    )
    asset = db.relationship("Asset", back_populates="monitor_spec")

    screen_size = db.Column(db.String(20), nullable=True)
    resolution = db.Column(db.String(40), nullable=True)
    panel_type = db.Column(db.Enum(PanelType), nullable=True)
    refresh_rate_hz = db.Column(db.Integer, nullable=True)
    ports = db.Column(db.String(120), nullable=True)  # ex.: "HDMI, DisplayPort"

    def __repr__(self):
        return f"<MonitorSpec asset={self.asset_id}>"


@audit_model
class PrinterSpec(db.Model):
    __tablename__ = "printer_specs"

    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(
        db.Integer, db.ForeignKey("assets.id"), unique=True, nullable=False
    )
    asset = db.relationship("Asset", back_populates="printer_spec")

    printer_type = db.Column(db.Enum(PrinterType), nullable=True)
    is_colorful = db.Column(db.Boolean, nullable=False, default=False)
    is_network = db.Column(db.Boolean, nullable=False, default=False)
    ip_address = db.Column(db.String(45), nullable=True)

    def __repr__(self):
        return f"<PrinterSpec asset={self.asset_id}>"


@audit_model
class ServerSpec(db.Model):
    __tablename__ = "server_specs"

    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(
        db.Integer, db.ForeignKey("assets.id"), unique=True, nullable=False
    )
    asset = db.relationship("Asset", back_populates="server_spec")

    cpu = db.Column(db.String(120), nullable=True)
    ram_gb = db.Column(db.Integer, nullable=True)
    storage_gb = db.Column(db.Integer, nullable=True)
    storage_type = db.Column(db.Enum(StorageType), nullable=True)
    raid_type = db.Column(db.String(40), nullable=True)
    os = db.Column(db.String(80), nullable=True)
    os_version = db.Column(db.String(80), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    rack_position = db.Column(db.String(40), nullable=True)

    def __repr__(self):
        return f"<ServerSpec asset={self.asset_id}>"


@audit_model
class NetworkSpec(db.Model):
    __tablename__ = "network_specs"

    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(
        db.Integer, db.ForeignKey("assets.id"), unique=True, nullable=False
    )
    asset = db.relationship("Asset", back_populates="network_spec")

    device_type = db.Column(db.Enum(NetworkDeviceType), nullable=True)
    ports_count = db.Column(db.Integer, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    managed = db.Column(db.Boolean, nullable=False, default=False)

    def __repr__(self):
        return f"<NetworkSpec asset={self.asset_id}>"


@audit_model
class PeripheralSpec(db.Model):
    __tablename__ = "peripheral_specs"

    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(
        db.Integer, db.ForeignKey("assets.id"), unique=True, nullable=False
    )
    asset = db.relationship("Asset", back_populates="peripheral_spec")

    peripheral_type = db.Column(db.String(80), nullable=True)  # Teclado, Mouse...
    connection_type = db.Column(db.Enum(ConnectionType), nullable=True)

    def __repr__(self):
        return f"<PeripheralSpec asset={self.asset_id}>"
