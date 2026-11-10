"""Lokaler Start: `python run.py` (Entwicklung). Produktiver Betrieb über gunicorn (Betriebsmodul)."""
from app import create_app

app = create_app()

if __name__ == "__main__":
    # Nur 127.0.0.1: kein Zugriff aus dem Netz, bis Betrieb und TLS festgelegt sind (D-11).
    app.run(host="127.0.0.1", port=5050, debug=False)
