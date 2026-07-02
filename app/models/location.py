"""Models de filiais e localizações físicas."""
from app.extensions import db
from app.utils.audit_listener import audit_model


@audit_model
class Branch(db.Model):
    __tablename__ = "branches"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    address = db.Column(db.String(255), nullable=True)

    locations = db.relationship("Location", back_populates="branch")

    def __repr__(self):
        return f"<Branch {self.name}>"


@audit_model
class Location(db.Model):
    __tablename__ = "locations"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)

    branch_id = db.Column(
        db.Integer, db.ForeignKey("branches.id"), nullable=True
    )
    branch = db.relationship("Branch", back_populates="locations")

    floor = db.Column(db.String(50), nullable=True)
    room = db.Column(db.String(50), nullable=True)

    assets = db.relationship("Asset", back_populates="location")

    def __repr__(self):
        return f"<Location {self.name}>"
