"""Models do módulo Infraestrutura (cabeamento estruturado / mapa de rede).

Documenta o espelho de patch panels de um andar: salas técnicas (racks),
patch panels, e os pontos de rede (tomadas) com sua ocupação. É um módulo
IRMÃO do inventário — desacoplado: o que está "plugado" num ponto é apenas
um texto descritivo (planejamento da mudança), sem FK para o inventário.

Hierarquia:
    Rack (R02, R03)
      └─ PatchPanel (PPA…PPP)
            └─ NetworkPoint (número + status + o que está plugado + área)

Tabelas com prefixo ``net_`` para isolar o módulo. Todos auditados
(@audit_model) e com soft-delete (is_active).
"""
from datetime import datetime

from app.extensions import db
from app.models.enums import PortStatus
from app.utils.audit_listener import audit_model


@audit_model
class Rack(db.Model):
    """Sala técnica / rack (ex.: R02, R03)."""
    __tablename__ = "net_racks"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), nullable=False, unique=True, index=True)
    name = db.Column(db.String(120), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    # Ambiente/sala onde o rack fica (ex.: CPD).
    area_id = db.Column(db.Integer, db.ForeignKey("net_areas.id"), nullable=True)
    area = db.relationship("NetworkArea", back_populates="racks")

    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    panels = db.relationship("PatchPanel", back_populates="rack")

    def __repr__(self):
        return f"<Rack {self.code}>"


@audit_model
class PatchPanel(db.Model):
    """Patch panel dentro de um rack (ex.: PPA…PPP)."""
    __tablename__ = "net_patch_panels"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), nullable=False, index=True)
    rack_id = db.Column(db.Integer, db.ForeignKey("net_racks.id"), nullable=False)
    rack = db.relationship("Rack", back_populates="panels")
    notes = db.Column(db.Text, nullable=True)

    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    points = db.relationship("NetworkPoint", back_populates="panel")

    __table_args__ = (
        db.UniqueConstraint("rack_id", "code", name="uq_panel_rack_code"),
    )

    def __repr__(self):
        return f"<PatchPanel {self.code} rack={self.rack_id}>"


# Associações N:N de setores com salas e mesas.
net_area_sectors = db.Table(
    "net_area_sectors",
    db.Column("area_id", db.Integer, db.ForeignKey("net_areas.id"), primary_key=True),
    db.Column("sector_id", db.Integer, db.ForeignKey("net_sectors.id"), primary_key=True),
)
net_desk_sectors = db.Table(
    "net_desk_sectors",
    db.Column("desk_id", db.Integer, db.ForeignKey("net_desks.id"), primary_key=True),
    db.Column("sector_id", db.Integer, db.ForeignKey("net_sectors.id"), primary_key=True),
)


@audit_model
class NetworkSector(db.Model):
    """Setor (etiqueta reutilizável) aplicável a várias salas e mesas."""
    __tablename__ = "net_sectors"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    def __repr__(self):
        return f"<NetworkSector {self.name}>"


@audit_model
class NetworkArea(db.Model):
    """Ambiente / sala do escritório (ex.: CPD, Mesa de Operações, Recepção).

    É o organizador físico do módulo: agrupa os equipamentos que ficam ali e
    os pontos de rede daquela sala.
    """
    __tablename__ = "net_areas"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    # Tipo do ambiente (CPD, Sala técnica, Operações, Escritório, Recepção...).
    kind = db.Column(db.String(40), nullable=True)
    description = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    points = db.relationship("NetworkPoint", back_populates="area")
    equipment = db.relationship(
        "NetworkEquipment", back_populates="area", cascade="all, delete-orphan"
    )
    racks = db.relationship("Rack", back_populates="area")
    desks = db.relationship(
        "NetworkDesk", back_populates="area", cascade="all, delete-orphan"
    )
    sectors = db.relationship("NetworkSector", secondary=net_area_sectors)

    def __repr__(self):
        return f"<NetworkArea {self.name}>"


@audit_model
class NetworkEquipment(db.Model):
    """Equipamento que fica em um ambiente (lista estruturada de planejamento).

    Desacoplado do inventário: é uma descrição do que vai/está na sala —
    ex.: "Servidor Bloomberg" x3, "Switch 48p" x2, "Desktops" x20.
    """
    __tablename__ = "net_equipment"

    id = db.Column(db.Integer, primary_key=True)
    area_id = db.Column(
        db.Integer, db.ForeignKey("net_areas.id"), nullable=False, index=True
    )
    area = db.relationship("NetworkArea", back_populates="equipment")

    name = db.Column(db.String(160), nullable=False)         # ex.: "Servidor Bloomberg"
    kind = db.Column(db.String(40), nullable=True)           # Servidor, Switch, Desktop, Outro
    quantity = db.Column(db.Integer, nullable=False, default=1)
    notes = db.Column(db.String(255), nullable=True)

    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<NetworkEquipment {self.name} x{self.quantity}>"


@audit_model
class NetworkDesk(db.Model):
    """Mesa dentro de uma sala. Contém posições (lugares/pessoas)."""
    __tablename__ = "net_desks"

    id = db.Column(db.Integer, primary_key=True)
    area_id = db.Column(
        db.Integer, db.ForeignKey("net_areas.id"), nullable=False, index=True
    )
    area = db.relationship("NetworkArea", back_populates="desks")

    name = db.Column(db.String(120), nullable=False)
    notes = db.Column(db.Text, nullable=True)

    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    sectors = db.relationship("NetworkSector", secondary=net_desk_sectors)
    seats = db.relationship(
        "NetworkSeat", back_populates="desk", cascade="all, delete-orphan",
        order_by="NetworkSeat.position",
    )

    def __repr__(self):
        return f"<NetworkDesk {self.name}>"


@audit_model
class NetworkSeat(db.Model):
    """Posição (lugar) numa mesa. Guarda a PESSOA; a máquina é derivada do
    inventário (asset cuja responsabilidade é dessa pessoa)."""
    __tablename__ = "net_seats"

    id = db.Column(db.Integer, primary_key=True)
    desk_id = db.Column(
        db.Integer, db.ForeignKey("net_desks.id"), nullable=False, index=True
    )
    desk = db.relationship("NetworkDesk", back_populates="seats")

    position = db.Column(db.Integer, nullable=False, default=1)   # ordem na mesa
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=True)
    employee = db.relationship("Employee")

    label = db.Column(db.String(120), nullable=True)   # rótulo livre quando sem pessoa
    notes = db.Column(db.String(255), nullable=True)

    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<NetworkSeat desk={self.desk_id} pos={self.position}>"


@audit_model
class NetworkPoint(db.Model):
    """Ponto de rede / tomada — a porta do patch panel que espelha uma tomada.

    ``endpoint`` é texto livre: o que está (ou vai estar) plugado ali —
    ex.: "Desktop recepção", "Telefone ramal 4021", "Access Point corredor".
    """
    __tablename__ = "net_points"

    id = db.Column(db.Integer, primary_key=True)

    patch_panel_id = db.Column(
        db.Integer, db.ForeignKey("net_patch_panels.id"), nullable=False, index=True
    )
    panel = db.relationship("PatchPanel", back_populates="points")

    number = db.Column(db.Integer, nullable=False)          # nº da porta/ponto
    label = db.Column(db.String(60), nullable=True)         # rótulo original ("R02 PPN 320")

    status = db.Column(
        db.Enum(PortStatus), nullable=False, default=PortStatus.FREE, index=True
    )
    # O que está plugado: preferencialmente um equipamento do ambiente
    # (equipment_id); 'endpoint' é uma descrição livre opcional (fallback).
    endpoint = db.Column(db.String(200), nullable=True)

    area_id = db.Column(db.Integer, db.ForeignKey("net_areas.id"), nullable=True)
    area = db.relationship("NetworkArea", back_populates="points")

    equipment_id = db.Column(
        db.Integer, db.ForeignKey("net_equipment.id"), nullable=True
    )
    plugged_equipment = db.relationship("NetworkEquipment", foreign_keys=[equipment_id])

    notes = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        db.UniqueConstraint("patch_panel_id", "number", name="uq_point_panel_number"),
    )

    @property
    def plugged_label(self):
        """Texto do que está plugado: nome do equipamento vinculado ou a
        descrição livre, o que existir."""
        if self.plugged_equipment is not None:
            return self.plugged_equipment.name
        return self.endpoint

    def __repr__(self):
        return f"<NetworkPoint {self.label or self.number}>"
