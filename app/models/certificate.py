"""Models do módulo Certificados (Centralizador Warren).

Guarda os certificados digitais dos sistemas externos, com foco em controle
de validade e alerta de vencimento. Os dados vêm de exportações do
Certificate Transparency (crt.sh), que trazem MUITA duplicata (precert +
leaf, renovações). Por isso a identidade de um certificado é o
``serial_number`` — a importação deduplica por ele (ver utils/cert_import.py).

Hierarquia:
    Certificate (1)  ──<  CertificateDomain (N)   # cada SAN de name_value

Convenções do projeto seguidas: soft-delete (is_active), auditoria automática
(@audit_model) no Certificate. Os domínios NÃO são auditados de propósito:
são reconstruídos a cada reimportação (upsert), o que geraria ruído enorme
de CREATE/DELETE no audit_logs.
"""
from datetime import date, datetime

from app.extensions import db
from app.utils.audit_listener import audit_model


# Janelas (em dias) usadas para classificar visualmente a validade.
CERT_WARNING_DAYS = 30   # "vencendo"
CERT_CRITICAL_DAYS = 7   # "crítico"


@audit_model
class Certificate(db.Model):
    """Um certificado digital (chave de deduplicação: serial_number)."""
    __tablename__ = "certificates"

    id = db.Column(db.Integer, primary_key=True)

    # Identidade real do certificado — chave de deduplicação da importação.
    serial_number = db.Column(db.String(160), nullable=False, unique=True, index=True)

    # Campos do crt.sh (Certificate Transparency).
    crtsh_id = db.Column(db.BigInteger, nullable=True)      # "id" da entrada crt.sh
    issuer_ca_id = db.Column(db.Integer, nullable=True)
    issuer_name = db.Column(db.String(255), nullable=True)
    common_name = db.Column(db.String(255), nullable=True, index=True)

    not_before = db.Column(db.DateTime, nullable=True)
    not_after = db.Column(db.DateTime, nullable=True, index=True)   # vencimento
    entry_timestamp = db.Column(db.DateTime, nullable=True)
    result_count = db.Column(db.Integer, nullable=True)

    notes = db.Column(db.Text, nullable=True)               # anotações manuais

    # Controle de disparo de alerta (evita reenviar o mesmo estágio).
    last_alert_stage = db.Column(db.String(20), nullable=True)
    last_alert_sent_on = db.Column(db.Date, nullable=True)

    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    domains = db.relationship(
        "CertificateDomain",
        back_populates="certificate",
        cascade="all, delete-orphan",
        order_by="CertificateDomain.domain",
    )

    # --- Conveniências de validade (calculadas, não persistidas) --------
    @property
    def days_to_expiry(self):
        """Dias até o vencimento (negativo = já vencido). None se sem data."""
        if not self.not_after:
            return None
        return (self.not_after.date() - date.today()).days

    @property
    def is_expired(self):
        d = self.days_to_expiry
        return d is not None and d < 0

    @property
    def status_key(self):
        """'expired' | 'critical' | 'warning' | 'valid' | 'unknown'."""
        d = self.days_to_expiry
        if d is None:
            return "unknown"
        if d < 0:
            return "expired"
        if d <= CERT_CRITICAL_DAYS:
            return "critical"
        if d <= CERT_WARNING_DAYS:
            return "warning"
        return "valid"

    @property
    def domain_list(self):
        """Lista simples dos domínios (str) para exibição/e-mail."""
        return [d.domain for d in self.domains]

    def __repr__(self):
        return f"<Certificate {self.common_name} …{self.serial_number[-6:]}>"


# Domínios (SANs) NÃO são auditados de propósito (reconstruídos no upsert).
class CertificateDomain(db.Model):
    """Um domínio/SAN coberto por um certificado (linha de name_value)."""
    __tablename__ = "certificate_domains"

    id = db.Column(db.Integer, primary_key=True)
    certificate_id = db.Column(
        db.Integer, db.ForeignKey("certificates.id"), nullable=False, index=True
    )
    certificate = db.relationship("Certificate", back_populates="domains")

    domain = db.Column(db.String(255), nullable=False, index=True)
    is_wildcard = db.Column(db.Boolean, nullable=False, default=False)
    # Ambiente inferido do nome: 'prd' | 'stg' | 'hml' | 'dev' | None.
    environment = db.Column(db.String(20), nullable=True)

    def __repr__(self):
        return f"<CertificateDomain {self.domain}>"
