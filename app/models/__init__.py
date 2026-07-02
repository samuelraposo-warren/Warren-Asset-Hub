"""Pacote de models.

Importa todos os models para que:
  1. o SQLAlchemy registre as tabelas no metadata (o Flask-Migrate
     precisa disso para autogerar as migrações);
  2. os event listeners de auditoria (@audit_model) sejam ativados no
     momento da importação das classes.

A ordem respeita as dependências de ForeignKey.
"""
from app.models.user import User
from app.models.audit import AuditLog
from app.models.employee import Department, Employee
from app.models.location import Branch, Location
from app.models.supplier import Supplier
from app.models.asset import Asset, AssetType
from app.models.specs import (
    DesktopSpec,
    MonitorSpec,
    NetworkSpec,
    NotebookSpec,
    PeripheralSpec,
    PrinterSpec,
    ServerSpec,
)
from app.models.movement import AssetMovement
from app.models.maintenance import MaintenanceRecord

__all__ = [
    "User",
    "AuditLog",
    "Department",
    "Employee",
    "Branch",
    "Location",
    "Supplier",
    "Asset",
    "AssetType",
    "NotebookSpec",
    "DesktopSpec",
    "MonitorSpec",
    "PrinterSpec",
    "ServerSpec",
    "NetworkSpec",
    "PeripheralSpec",
    "AssetMovement",
    "MaintenanceRecord",
]
