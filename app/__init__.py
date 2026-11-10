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


MODI = ("testadapter", "vorschaltdienst")


def wirksamer_modus(cfg: dict, ueberschreibung: str | None = None) -> tuple[str, str]:
    """Ermittelt den wirksamen Modellmodus und die Quelle der Entscheidung.

    Reihenfolge: Testparameter, dann Umgebungsvariable LERNSOFTWARE_MODELL, dann config/basis.yaml.
    Ungültige Werte führen zu einem Fehler, nie zu einem stillen Rückfall.
    """
    if ueberschreibung:
        quelle, modus = "Testparameter", ueberschreibung
    elif os.environ.get("LERNSOFTWARE_MODELL"):
        quelle, modus = "Umgebungsvariable LERNSOFTWARE_MODELL", os.environ["LERNSOFTWARE_MODELL"].strip()
    else:
        quelle, modus = "config/basis.yaml", cfg["modell"]["modus"]
    if modus not in MODI:
        raise ValueError(f"Unbekannter Modellmodus «{modus}» (erlaubt: {', '.join(MODI)})")
    return modus, quelle


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
    modus, quelle = wirksamer_modus(cfg, (test_konfig or {}).get("MODELL_MODUS"))
    app.config["MODELL"] = erstelle_modell(cfg, modus)
    app.config["MODELL_ANZEIGE"] = {
        "modus": modus, "quelle": quelle,
        "text": ("Modell: SIMULIERT (Testadapter) – keine echte Modellprüfung"
                 if modus == "testadapter" else "Modell: Vorschaltdienst (echte Modellausgaben)"),
    }

    # Start-Protokoll (Betrieb): wirksamer Modus und Warnungen erscheinen beim Start
    log.warning("Start: Modellmodus = %s (Quelle: %s)", modus, quelle)
    if modus == "testadapter":
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
                        "modell_herkunft": app.config["MODELL"].herkunft,
                        "modell": app.config["MODELL_ANZEIGE"]})

    return app
