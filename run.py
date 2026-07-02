"""Ponto de entrada da aplicação.

Uso em desenvolvimento:
    python run.py

Uso com o CLI do Flask (migrações, shell, etc.):
    flask --app run:app db init
    flask --app run:app db migrate -m "mensagem"
    flask --app run:app db upgrade
"""
import os

from app import create_app

app = create_app(os.environ.get("FLASK_ENV", "development"))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=app.config.get("DEBUG", False))
