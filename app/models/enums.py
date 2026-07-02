"""Enumerações usadas pelos models.

Cada enum tem valores iguais aos nomes (armazenados como string no banco
via ``db.Enum``), o que facilita leitura direta na tabela e migrações.
"""
import enum


class UserRole(enum.Enum):
    ADMIN = "ADMIN"
    TI = "TI"
    VIEWER = "VIEWER"


class AssetStatus(enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    MAINTENANCE = "MAINTENANCE"
    DISPOSED = "DISPOSED"
    STOLEN = "STOLEN"
    LOANED = "LOANED"


class AssetCondition(enum.Enum):
    NEW = "NEW"
    GOOD = "GOOD"
    FAIR = "FAIR"
    POOR = "POOR"
    DEFECTIVE = "DEFECTIVE"


class StorageType(enum.Enum):
    HDD = "HDD"
    SSD = "SSD"
    NVME = "NVME"


class FormFactor(enum.Enum):
    TOWER = "TOWER"
    MINI = "MINI"
    ALL_IN_ONE = "ALL_IN_ONE"


class PanelType(enum.Enum):
    IPS = "IPS"
    TN = "TN"
    VA = "VA"
    OLED = "OLED"


class PrinterType(enum.Enum):
    LASER = "LASER"
    INKJET = "INKJET"
    THERMAL = "THERMAL"


class NetworkDeviceType(enum.Enum):
    SWITCH = "SWITCH"
    ROUTER = "ROUTER"
    ACCESS_POINT = "ACCESS_POINT"
    FIREWALL = "FIREWALL"


class ConnectionType(enum.Enum):
    USB = "USB"
    BLUETOOTH = "BLUETOOTH"
    WIRELESS = "WIRELESS"


class MaintenanceType(enum.Enum):
    PREVENTIVE = "PREVENTIVE"
    CORRECTIVE = "CORRECTIVE"
    UPGRADE = "UPGRADE"


class AuditAction(enum.Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
