"""Beweist: Eine frische Installation erzeugt die Demo-Datenbank, der Demo-Login funktioniert, der
Server-Zeiger zeigt auf dieselbe Datenbank und der wirksame Modellmodus ist sichtbar (Punkt 8)."""
from pathlib import Path

from app import create_app, wirksamer_modus
from app.demo import main as demo_main
from app.sicherheit import lade_basis_konfig


def test_demo_erzeugt_datenbank_und_student_kann_sich_anmelden(tmp_path):
    """Beweist: Die Demo legt eine lauffähige Datenbank an; die ausgegebenen Zugangsdaten melden an (Punkt 8)."""
    pw = {}
    rc = demo_main(tmp_path / "demo-test.sqlite3", passwoerter=pw)
    assert rc == 0
    app = create_app({"DATABASE_URL": f"sqlite:///{tmp_path / 'demo-test.sqlite3'}", "MODELL_MODUS": "testadapter"})
    c = app.test_client()
    antwort = c.post("/api/v1/auth/anmelden", json={"kurzname": "beispiel-hs", "benutzername": "student",
                                                    "passwort": pw["student"]})
    assert antwort.status_code == 200
    assert c.get("/api/v1/module").get_json()[0]["rolle"] == "studierende"


def test_modellmodus_ueber_umgebungsvariable(monkeypatch):
    """Beweist: LERNSOFTWARE_MODELL wirkt; ein ungültiger Wert bricht ab statt still zurückzufallen (Punkt 8)."""
    cfg = lade_basis_konfig()
    monkeypatch.setenv("LERNSOFTWARE_MODELL", "vorschaltdienst")
    assert wirksamer_modus(cfg) == ("vorschaltdienst", "Umgebungsvariable LERNSOFTWARE_MODELL")
    monkeypatch.setenv("LERNSOFTWARE_MODELL", "irgendwas")
    try:
        wirksamer_modus(cfg)
        raise AssertionError("ungültiger Modus wurde akzeptiert")
    except ValueError as exc:
        assert "irgendwas" in str(exc)


def test_modellmodus_ohne_umgebungsvariable_kommt_aus_config(monkeypatch):
    """Beweist: Ohne Umgebungsvariable gilt config/basis.yaml, und die Quelle wird angezeigt (Punkt 8)."""
    monkeypatch.delenv("LERNSOFTWARE_MODELL", raising=False)
    modus, quelle = wirksamer_modus(lade_basis_konfig())
    assert modus == "testadapter" and quelle == "config/basis.yaml"


def test_healthz_zeigt_wirksamen_modus(app):
    """Beweist: Der Modellmodus ist über den Gesundheitsendpunkt und in der Oberfläche sichtbar (Punkt 8)."""
    daten = app.test_client().get("/healthz").get_json()
    assert daten["modell"]["modus"] == "testadapter"
    assert "SIMULIERT" in daten["modell"]["text"]
    seite = app.test_client().get("/anmelden").get_data(as_text=True)
    assert "SIMULIERT" in seite


def test_zeiger_fuer_run_py_wird_geschrieben(tmp_path, monkeypatch):
    """Beweist: Die Standard-Demo schreibt den Zeiger, den run.py ohne Umgebungsvariable verwendet (Punkt 8)."""
    import app.demo as demo
    monkeypatch.setattr(demo, "PROJEKT", tmp_path)
    (tmp_path / "instance").mkdir()
    demo.main(None, passwoerter={})
    zeiger = (tmp_path / "instance" / "aktuelle-demo.txt").read_text(encoding="utf-8")
    assert zeiger.startswith("sqlite:///") and zeiger.endswith(".sqlite3")
