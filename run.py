"""Lokaler Start: `python run.py` (Entwicklung). Produktiver Betrieb über gunicorn (Betriebsmodul).

Datenbank-Reihenfolge: Umgebungsvariable DATABASE_URL, sonst die Datei instance/aktuelle-demo.txt
(vom Demonstrationsskript geschrieben), sonst instance/lernsoftware.sqlite3.
"""
import os
from pathlib import Path

from app import create_app

PROJEKT = Path(__file__).resolve().parent
ZEIGER = PROJEKT / "instance" / "aktuelle-demo.txt"

if not os.environ.get("DATABASE_URL") and ZEIGER.exists():
    os.environ["DATABASE_URL"] = ZEIGER.read_text(encoding="utf-8").strip()

app = create_app()

if __name__ == "__main__":
    # Nur 127.0.0.1: kein Zugriff aus dem Netz, bis Betrieb und TLS festgelegt sind (D-11).
    app.run(host="127.0.0.1", port=5050, debug=False)
