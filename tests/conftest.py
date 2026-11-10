"""Gemeinsame Testfixtures und Testprotokoll (RA-13: Protokoll als Nachweis).

Alle Testdaten sind synthetisch. Passwörter der Tests sind feste Testwerte, die nur in der
Testdatenbank existieren (keine Zugangsdaten für reale Systeme).
"""
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app import create_app
from app.db import Basis
from app.demo import UNTERLAGE, bootstrap_superadmin
from app.models import Abschnitt, Aufgabe, Konto, Lektion, Lernziel, Modul, Unterlage
from app.modell.testadapter import SimulationsAdapter
from app.sicherheit import lade_basis_konfig

PROJEKT = Path(__file__).resolve().parent.parent
PROTOKOLL_ORDNER = PROJEKT / "docs" / "nachweise"

TESTPW = "Testpasswort-2026"
SA_PW = "Superadmin-Test-2026"


# ---------- Testprotokoll ----------

_ergebnisse: list[dict] = []


def pytest_runtest_logreport(report):
    if report.when != "call" and not (report.when == "setup" and report.skipped):
        return
    doc = (report.nodeid.split("::")[-1])
    _ergebnisse.append({
        "test": report.nodeid,
        "ergebnis": {"passed": "bestanden", "failed": "nicht_bestanden", "skipped": "nicht_geprueft"}[report.outcome],
        "grund": str(report.longrepr)[:300] if report.outcome == "skipped" else None,
        "kennung": doc,
    })


def pytest_sessionfinish(session, exitstatus):
    # Protokoll nur auf ausdrückliche Anweisung schreiben (LERNSOFTWARE_PROTOKOLL=1), damit
    # Entwicklungsläufe keine Nachweise erzeugen.
    if not _ergebnisse or os.environ.get("LERNSOFTWARE_PROTOKOLL") != "1":
        return
    PROTOKOLL_ORDNER.mkdir(parents=True, exist_ok=True)
    jetzt = datetime.now(timezone.utc)
    zaehler = {k: sum(1 for e in _ergebnisse if e["ergebnis"] == k)
               for k in ("bestanden", "nicht_bestanden", "nicht_geprueft")}
    protokoll = {
        "protokoll": {
            "erzeugt_am": jetzt.isoformat(),
            "umgebung": "develop",
            "version_norm": "RA v0.4 · NR-01…NR-10",
            "version_testset": "TS-1 (synthetisch)",
            "modell_herkunft": "SIMULIERT (Testadapter) — echte Modellläufe nur, wo unten als echt ausgewiesen",
            "zusammenfassung": zaehler,
            "exitstatus": int(exitstatus),
            "faelle": _ergebnisse,
            "herkunft": "Test-Runner (pytest)",
        }
    }
    datei = PROTOKOLL_ORDNER / f"testprotokoll-{jetzt.strftime('%Y%m%dT%H%M%SZ')}.json"
    datei.write_text(json.dumps(protokoll, ensure_ascii=False, indent=2), encoding="utf-8")


# ---------- Grundfixtures ----------

@pytest.fixture
def cfg():
    return lade_basis_konfig()


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("LERNSOFTWARE_SECRET", "test-geheimnis-nur-fuer-tests")
    url = f"sqlite:///{tmp_path / 'test.sqlite3'}"
    # Testparameter für Argon2: schwächer, nur für Testlaufzeit. Produktwerte stehen in config/basis.yaml.
    testsicherheit = lade_basis_konfig()["sicherheit"]
    testsicherheit["argon2"] = {"zeit_kosten": 1, "speicher_kib": 8192, "parallelitaet": 1}
    a = create_app({"DATABASE_URL": url, "MODELL_MODUS": "testadapter", "sicherheit": testsicherheit})
    a.config["TESTING"] = True
    return a


@pytest.fixture
def modell(app):
    return app.config["MODELL"]


@pytest.fixture
def sitzung(app):
    s = app.config["SITZUNG"]()
    try:
        yield s
    finally:
        s.close()


def _login(client, benutzername, passwort, kurzname=None):
    body = {"benutzername": benutzername, "passwort": passwort}
    if kurzname:
        body["kurzname"] = kurzname
    antwort = client.post("/api/v1/auth/anmelden", json=body)
    assert antwort.status_code == 200, antwort.get_json()
    return antwort.get_json()["csrf"]


class Klient:
    def __init__(self, client, csrf=None):
        self.c = client
        self.csrf = csrf

    def post(self, pfad, daten=None):
        a = self.c.post(f"/api/v1{pfad}", json=daten or {}, headers={"X-CSRF-Token": self.csrf or ""})
        return a.status_code, a.get_json()

    def get(self, pfad):
        a = self.c.get(f"/api/v1{pfad}")
        return a.status_code, a.get_json()


def login_als(app, benutzername, kurzname):
    """Eigener Testklient je Person (eigene Sitzung)."""
    c = app.test_client()
    return Klient(c, _login(c, benutzername, TESTPW, kurzname))


@pytest.fixture
def seeded(app, sitzung, cfg):
    """Zwei Lernorganisationen. Organisation A hat Modul mit freigegebener Unterlage und zwei Aufgaben."""
    bootstrap_superadmin(sitzung, cfg, "plattform-test", SA_PW)
    sitzung.commit()
    c = app.test_client()
    sa_csrf = _login(c, "plattform-test", SA_PW)
    sa = Klient(c, sa_csrf)
    orgs = {}
    for kurz, admin in (("org-a", "admin-a"), ("org-b", "admin-b")):
        status, org = sa.post("/superadmin/lernorganisationen", {
            "name": f"Organisation {kurz}", "kurzname": kurz,
            "admin_benutzername": admin, "admin_anzeigename": f"Admin {kurz}", "admin_passwort": TESTPW})
        assert status == 201, org
        orgs[kurz] = org
    c.post("/api/v1/auth/abmelden", headers={"X-CSRF-Token": sa_csrf})

    daten = {}
    for kurz, admin in (("org-a", "admin-a"), ("org-b", "admin-b")):
        ac = app.test_client()
        k = Klient(ac, _login(ac, admin, TESTPW, kurzname=kurz))
        daten[kurz] = {"client": ac, "klient": k, "org": orgs[kurz]["id"]}
    adm = daten["org-a"]["klient"]
    for name in ("dozent-a", "assistenz-a", "student-a", "student-a2"):
        adm.post("/konten", {"benutzername": name, "anzeigename": name, "passwort": TESTPW, "rolle": "mitglied"})
    st, modul = adm.post("/module", {"bezeichnung": "Statistik A"})
    ids = {"modul": modul["id"], "org": orgs["org-a"]["id"]}
    konto_ids = {}
    for name, rolle, delegiert in (("dozent-a", "dozierende", False), ("assistenz-a", "assistenz", False),
                                   ("student-a", "studierende", False), ("student-a2", "studierende", False)):
        st, konto = adm.post("/konten", {"benutzername": name, "anzeigename": name, "passwort": TESTPW, "rolle": "mitglied"})
        konto_ids[name] = konto["id"]
        adm.post(f"/module/{modul['id']}/zuweisungen", {"konto_id": konto["id"], "rolle": rolle,
                                                         "freigabe_delegiert": delegiert})
    ids["konto"] = konto_ids

    doz = login_als(app, "dozent-a", "org-a")
    st, lek = doz.post(f"/module/{modul['id']}/lektionen", {"titel": "Lektion 1"})
    st, z1 = doz.post(f"/lektionen/{lek['id']}/lernziele", {"text": "Ereignisse benennen", "handlungsstufe": "wiedergeben"})
    st, z2 = doz.post(f"/lektionen/{lek['id']}/lernziele", {"text": "Unvereinbare Ereignisse rechnen", "handlungsstufe": "anwenden"})
    st, u = doz.post(f"/module/{modul['id']}/unterlagen", {"titel": "Grundlagen (synthetisch)", "dateiname": "g.md",
                                                           "lektion_id": lek["id"], "inhalt": UNTERLAGE.read_text(encoding="utf-8")})
    assert st == 201, u
    st, _ = doz.post(f"/unterlagen/{u['id']}/freigabe", {"form": "freigegeben"})
    assert st == 200
    st, abschn = doz.get(f"/unterlagen/{u['id']}/abschnitte")
    st, a1 = doz.post(f"/module/{modul['id']}/aufgaben", {
        "lernziel_id": z1["id"], "fragetyp": "single_choice",
        "aufgabe_text": "Wie viele Ausgänge hat der Ergebnisraum eines Würfels?",
        "optionen": [{"id": "a", "text": "fünf"}, {"id": "b", "text": "sechs"}],
        "loesung": ["b"], "max_punkte": 1, "erklaerung": "Die Augenzahlen 1 bis 6 ergeben sechs Ausgänge.",
        "hinweis": "Zähle die Augenzahlen.", "abschnitt_ids": [abschn[0]["id"]]})
    assert st == 201, a1
    st, a2 = doz.post(f"/module/{modul['id']}/aufgaben", {
        "lernziel_id": z2["id"], "fragetyp": "multiple_choice",
        "aufgabe_text": "Welche Ereignisse sind bei einem Würfelwurf unvereinbar?",
        "optionen": [{"id": "a", "text": "eins und sechs"}, {"id": "b", "text": "gerade und ungerade"},
                     {"id": "c", "text": "eins und zwei"}],
        "loesung": ["a", "b"], "max_punkte": 2,
        "erklaerung": "Eins und sechs sowie gerade und ungerade schliessen sich aus.",
        "abschnitt_ids": [abschn[-1]["id"]]})
    assert st == 201, a2
    ids.update({"lektion": lek["id"], "ziel1": z1["id"], "ziel2": z2["id"], "unterlage": u["id"],
                "aufgabe1": a1["id"], "aufgabe2": a2["id"], "abschnitte": [a["id"] for a in abschn]})
    ids["org_b"] = orgs["org-b"]["id"]
    ids["login"] = lambda name, kurz: login_als(app, name, kurz)
    ids["app"] = app
    return ids
