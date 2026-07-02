"""Models de colaboradores e departamentos."""
from datetime import datetime

from app.extensions import db
from app.utils.audit_listener import audit_model


@audit_model
class Department(db.Model):
    __tablename__ = "departments"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)

    employees = db.relationship("Employee", back_populates="department")

    def __repr__(self):
        return f"<Department {self.name}>"


@audit_model
class Employee(db.Model):
    __tablename__ = "employees"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=True, index=True)
    # Matrícula do colaborador.
    employee_id = db.Column(db.String(50), unique=True, nullable=False, index=True)

    department_id = db.Column(
        db.Integer, db.ForeignKey("departments.id"), nullable=True
    )
    department = db.relationship("Department", back_populates="employees")

    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Ativos atualmente atribuídos a este colaborador.
    assets = db.relationship("Asset", back_populates="assigned_to")

    def __repr__(self):
        return f"<Employee {self.employee_id} - {self.name}>"
