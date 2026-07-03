"""Parâmetros do sistema (armazenamento key/value).

Guarda configurações globais editáveis pelo ADMIN (nome da empresa, janela
de garantia, símbolo de moeda, etc.). Uma linha por parâmetro. Os valores
são sempre string; a interpretação (int, etc.) fica na camada de leitura.
"""
from app.extensions import db


class Setting(db.Model):
    __tablename__ = "settings"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(80), nullable=False, unique=True, index=True)
    value = db.Column(db.String(500), nullable=True)

    def __repr__(self):
        return f"<Setting {self.key}={self.value!r}>"
