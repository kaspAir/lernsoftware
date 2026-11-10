"""Lernsoftware – Anwendungsfabrik (Inkrement 1).

`create_app()` lädt die Basiskonfiguration, richtet die Datenbank ein und wählt den Modellzugang.
Betriebswarnungen (ADR-L-005, Betriebsmodul) erscheinen im Start-Protokoll.
"""
import logging
import os
from pathlib import Path

from flask import Flask, jsonify

from .db import Basis, erstelle_engine, sitzungsfabrik
from .fehler import FachFehler
from .modell.adapter import VorschaltdienstAdapter
from .modell.testadapter import SimulationsAdapter
from .sicherheit import lade_basis_konfig

PROJEKT = Path(__file__).resolve().parent.parent
log = logging.getLogger("lernsoftware")


def erstelle_modell(cfg: dict, modus: str | None = None):
    m = modus or cfg["modell"]["modus"]
    if m == "vorschaltdienst":
        return VorschaltdienstAdapter(
            basis_url=cfg["modell"]["vorschaltdienst_basis"],
            modellname=cfg["modell"]["modellname"],
            anwendung=cfg["modell"]["anwendung_kennung"],
            timeout=float(cfg["lernbegleiter"]["timeout_sekunden"]),
        )
    return SimulationsAdapter()


def create_app(test_konfig: dict | None = None) -> Flask:
    app = Flask(__name__, template_folder=str(PROJEKT / "app" / "templates"))
    cfg = lade_basis_konfig()
    if test_konfig:
        cfg.update(test_konfig)
    app.config["LERNCFG"] = cfg
    app.config["SECRET_KEY"] = os.environ.get("LERNSOFTWARE_SECRET", "entwicklung-nur-lokal")
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = bool(os.environ.get("LERNSOFTWARE_HTTPS"))

    url = (test_konfig or {}).get("DATABASE_URL") or os.environ.get(
        "DATABASE_URL", f"sqlite:///{PROJEKT / 'instance' / 'lernsoftware.sqlite3'}")
    if url.startswith("sqlite:///") and "instance" in url:
        (PROJEKT / "instance").mkdir(exist_ok=True)
    engine = erstelle_engine(url)
    Basis.metadata.create_all(engine)
    app.config["SITZUNG"] = sitzungsfabrik(engine)
    app.config["MODELL"] = erstelle_modell(cfg, (test_konfig or {}).get("MODELL_MODUS"))

    # Start-Protokoll (Betrieb): unklare Zustände melden sich beim Start
    if app.config["MODELL"].herkunft == "SIMULIERT":
        log.warning("Start: Testadapter aktiv – Modellausgaben sind SIMULIERT, nicht geprüft.")
    if os.environ.get("LERNSOFTWARE_SECRET") is None:
        log.warning("Start: Standard-Geheimnis aktiv – nur für lokale Entwicklung.")

    from .api import blueprint as api_bp
    from .web import blueprint as web_bp
    app.register_blueprint(api_bp, url_prefix="/api/v1")
    app.register_blueprint(web_bp)

    @app.errorhandler(FachFehler)
    def _fachfehler(exc: FachFehler):
        return jsonify(exc.als_dict()), exc.status

    @app.get("/healthz")
    def healthz():
        return jsonify({"status": "bereit", "produkt": cfg["produkt"]["name"],
                        "modell_herkunft": app.config["MODELL"].herkunft})

    return app
