"""Demonstrationsablauf des Inkrements 1 über die JSON-Schnittstelle.

Start (Projektordner, mit aktivierter venv):
    python -m app.demo

Es wird eine frische Entwicklungsdatenbank unter instance/demo.sqlite3 angelegt. Passwörter
werden zufällig erzeugt und nur auf der Konsole ausgegeben; sie stehen nicht im Repository (NF-12).
Der Modellzugang ist der Testadapter; alle Modellausgaben sind als SIMULIERT gekennzeichnet.
"""
import json
import secrets
import sys
from pathlib import Path

from . import create_app
from .db import Basis
from .models import Konto
from .sicherheit import hashe_passwort, lade_basis_konfig

PROJEKT = Path(__file__).resolve().parent.parent
UNTERLAGE = PROJEKT / "tests" / "daten" / "grundlagen_wahrscheinlichkeit.md"


def bootstrap_superadmin(session, cfg: dict, benutzername: str, passwort: str) -> Konto:
    """Legt den Super-Admin an (einmalig, außerhalb der Oberfläche)."""
    konto = Konto(benutzername=benutzername, anzeigename="Super-Admin", ist_superadmin=True,
                  passwort_hash=hashe_passwort(passwort, cfg), status="aktiv")
    session.add(konto)
    session.flush()
    return konto


class Klient:
    """Dünner Helfer: hält Sitzung und CSRF-Token, gibt Antworten als Tupel (status, daten) zurück."""

    def __init__(self, client):
        self.c = client
        self.csrf = None

    def anmelden(self, benutzername, passwort, kurzname=None):
        body = {"benutzername": benutzername, "passwort": passwort}
        if kurzname:
            body["kurzname"] = kurzname
        self.c.get("/healthz")
        antwort = self.c.post("/api/v1/auth/anmelden", json=body)
        if antwort.status_code == 200:
            self.csrf = antwort.get_json()["csrf"]
        return antwort.status_code, antwort.get_json()

    def abmelden(self):
        self.c.post("/api/v1/auth/abmelden", headers={"X-CSRF-Token": self.csrf or ""})
        self.csrf = None

    def get(self, pfad):
        a = self.c.get(f"/api/v1{pfad}")
        return a.status_code, a.get_json()

    def post(self, pfad, daten=None):
        a = self.c.post(f"/api/v1{pfad}", json=daten or {}, headers={"X-CSRF-Token": self.csrf or ""})
        return a.status_code, a.get_json()


def _zeige(titel: str, status: int, daten) -> None:
    print(f"\n== {titel}  [HTTP {status}]")
    print(json.dumps(daten, ensure_ascii=False, indent=2, default=str)[:1500])


def main(db_pfad: Path | None = None) -> int:
    # Jeder Lauf bekommt eine eigene Datei: Eine noch geöffnete alte Datenbank (z. B. durch einen
    # laufenden Server unter Windows) blockiert so keinen neuen Lauf.
    if db_pfad is None:
        from datetime import datetime
        db_pfad = PROJEKT / "instance" / f"demo-{datetime.now():%Y%m%d-%H%M%S}.sqlite3"
    db_pfad.parent.mkdir(exist_ok=True)
    app = create_app({"DATABASE_URL": f"sqlite:///{db_pfad}", "MODELL_MODUS": "testadapter"})
    cfg = app.config["LERNCFG"]

    pw = {k: secrets.token_urlsafe(12) for k in ("sa", "admin", "dozent", "assistenz", "student", "admin2", "student2")}
    print("Zufällige Demo-Passwörter (nur für diese Sitzung, nicht gespeichert):")
    for k in ("sa", "admin", "dozent", "assistenz", "student"):
        print(f"  {k:10s} {pw[k]}")

    with app.config["SITZUNG"]() as s:
        bootstrap_superadmin(s, cfg, "plattform-admin", pw["sa"])
        s.commit()

    c = app.test_client()
    sa = Klient(c)
    st, d = sa.anmelden("plattform-admin", pw["sa"])
    _zeige("1 · Super-Admin meldet sich an", st, {"superadmin": d.get("superadmin")})
    st, d = sa.post("/superadmin/lernorganisationen", {
        "name": "Beispiel Hochschule", "kurzname": "beispiel-hs",
        "admin_benutzername": "admin", "admin_anzeigename": "Administration Beispiel",
        "admin_passwort": pw["admin"]})
    _zeige("2 · Super-Admin legt Lernorganisation und Erstadministration an", st, d)
    st, d = sa.post("/superadmin/lernorganisationen", {
        "name": "Andere Schule", "kurzname": "andere-schule",
        "admin_benutzername": "admin2", "admin_anzeigename": "Administration Andere",
        "admin_passwort": pw["admin2"]})
    st, d = sa.get("/superadmin/lernorganisationen")
    _zeige("2b · Super-Admin sieht nur Registrierungsdaten", st, d)
    sa.abmelden()

    adm = Klient(c)
    st, d = adm.anmelden("admin", pw["admin"], kurzname="beispiel-hs")
    _zeige("3 · Administration meldet sich an", st, {"org_rolle": d.get("org_rolle")})
    konten = {}
    for benutzer, anzeige, pwk in (("dozent", "Dozent Beispiel", "dozent"),
                                   ("assistenz", "Assistenz Beispiel", "assistenz"),
                                   ("student", "Studierende Beispiel", "student")):
        st, d = adm.post("/konten", {"benutzername": benutzer, "anzeigename": anzeige,
                                     "passwort": pw[pwk], "rolle": "mitglied"})
        konten[benutzer] = d["id"]
    st, modul = adm.post("/module", {"bezeichnung": "Statistik-Grundlagen (Testkurs)",
                                     "beschreibung": "Synthetischer Testkurs"})
    _zeige("4 · Administration legt Modul an", st, modul)
    for benutzer, rolle in (("dozent", "dozierende"), ("assistenz", "assistenz"), ("student", "studierende")):
        st, d = adm.post(f"/module/{modul['id']}/zuweisungen",
                         {"konto_id": konten[benutzer], "rolle": rolle,
                          "freigabe_delegiert": False})
        _zeige(f"5 · Zuweisung {benutzer} als {rolle}", st, d)
    adm.abmelden()

    doz = Klient(c)
    st, d = doz.anmelden("dozent", pw["dozent"], kurzname="beispiel-hs")
    st, lek = doz.post(f"/module/{modul['id']}/lektionen", {"titel": "Lektion 1: Ereignisse und Wahrscheinlichkeit"})
    _zeige("6 · Dozent legt Lektion an", st, lek)
    st, ziel = doz.post(f"/lektionen/{lek['id']}/lernziele",
                        {"text": "Ereignisse und Gegenereignisse bei Zufallsexperimenten benennen",
                         "handlungsstufe": "wiedergeben"})
    st, ziel2 = doz.post(f"/lektionen/{lek['id']}/lernziele",
                         {"text": "Wahrscheinlichkeiten unvereinbarer Ereignisse berechnen",
                          "handlungsstufe": "anwenden"})
    st, u = doz.post(f"/module/{modul['id']}/unterlagen", {
        "titel": "Grundlagen Wahrscheinlichkeit (synthetisch)", "dateiname": "grundlagen.md",
        "lektion_id": lek["id"], "inhalt": UNTERLAGE.read_text(encoding="utf-8")})
    _zeige("7 · Dozent lädt Unterlage hoch", st, u)
    st, d = doz.post(f"/unterlagen/{u['id']}/freigabe", {"form": "freigegeben"})
    _zeige("8 · Dozent gibt Unterlage fachlich frei (Ebene A)", st, d)
    st, abschn = doz.get(f"/unterlagen/{u['id']}/abschnitte")
    quelle_eins = abschn[0]["id"]
    quelle_zwei = abschn[1]["id"]
    st, a1 = doz.post(f"/module/{modul['id']}/aufgaben", {
        "lernziel_id": ziel["id"], "fragetyp": "single_choice",
        "aufgabe_text": "Wie viele Ausgänge umfasst der Ergebnisraum eines sechsseitigen Würfels?",
        "optionen": [{"id": "a", "text": "fünf"}, {"id": "b", "text": "sechs"}, {"id": "c", "text": "zwölf"}],
        "loesung": ["b"], "max_punkte": 1,
        "erklaerung": "Der Ergebnisraum enthält die Augenzahlen 1 bis 6, also sechs Ausgänge.",
        "hinweis": "Zähle die möglichen Augenzahlen des Würfels.",
        "abschnitt_ids": [quelle_eins], "denkschritte": 1})
    st, a2 = doz.post(f"/module/{modul['id']}/aufgaben", {
        "lernziel_id": ziel2["id"], "fragetyp": "single_choice",
        "aufgabe_text": "Wie gross ist die Wahrscheinlichkeit, mit einem Würfel eine eins oder eine sechs zu würfeln?",
        "optionen": [{"id": "a", "text": "ein Sechstel"}, {"id": "b", "text": "zwei Sechstel"},
                     {"id": "c", "text": "drei Sechstel"}],
        "loesung": ["b"], "max_punkte": 1,
        "erklaerung": "Eins und sechs sind unvereinbar; ihre Wahrscheinlichkeiten addieren sich zu zwei Sechsteln.",
        "beispiel": "Berechne zuerst die Wahrscheinlichkeit für eine eins, dann für eine sechs.",
        "abschnitt_ids": [quelle_zwei], "denkschritte": 2})
    _zeige("9 · Dozent bereitet zwei Lernaufgaben vor (Ebene C: von Lehrperson erstellt und damit geprüft)", st, a2)
    doz.abmelden()

    ass = Klient(c)
    ass.anmelden("assistenz", pw["assistenz"], kurzname="beispiel-hs")
    st, d = ass.post(f"/unterlagen/{u['id']}/freigabe", {"form": "freigegeben"})
    _zeige("10 · Assistenz versucht Freigabe ohne Delegation (erwartet: 403)", st, d)
    ass.abmelden()

    stu = Klient(c)
    st, d = stu.anmelden("student", pw["student"], kurzname="beispiel-hs")
    st, mod_liste = stu.get("/module")
    _zeige("11 · Studierende sieht nur zugewiesene Module", st, mod_liste)
    st, ue = stu.post(f"/module/{modul['id']}/uebungen", {"lektion_ids": [lek["id"]]})
    _zeige("12 · Studierende erzeugt Übung zur Lektion", st, ue)
    aufgabe_1 = ue["aufgaben"][0]
    st, hilfe = stu.post(f"/uebungen/{ue['id']}/hilfe", {"aufgabe_id": aufgabe_1["id"], "art": "hinweis"})
    _zeige("13 · Hilfe vor der Antwort (wird am Versuch vermerkt)", st, hilfe)
    st, v1 = stu.post(f"/uebungen/{ue['id']}/versuche", {
        "aufgabe_id": aufgabe_1["id"], "gegeben": ["a"], "selbsteinschaetzung": "unsicher"})
    _zeige("14 · Antwort abgegeben (falsch) mit Rückmeldung und Quelle", st, v1)
    aufgabe_2 = ue["aufgaben"][1]
    st, v2 = stu.post(f"/uebungen/{ue['id']}/versuche", {
        "aufgabe_id": aufgabe_2["id"], "gegeben": ["b"], "selbsteinschaetzung": "sicher"})
    _zeige("15 · Zweite Antwort (richtig, ohne Hilfe)", st, v2)
    st, gp = stu.post(f"/versuche/{v1['versuch_id']}/gespraech",
                      {"frage": "Warum gehört die Aufgabe zum Ergebnisraum?", "form": "rueckfrage"})
    _zeige("16 · Rückfrage an den Lernbegleiter (Testadapter, SIMULIERT)", st, gp)
    st, lp = stu.get(f"/module/{modul['id']}/lernprofil")
    _zeige("17 · Lernprofil je Lernziel", st, lp)
    st, agg = stu.get(f"/module/{modul['id']}/lernprofil/aggregiert")
    _zeige("18 · Studierende darf keine aggregierte Lehrsicht sehen (erwartet: 403)", st, agg)
    stu.abmelden()

    fremd = Klient(c)
    fremd.anmelden("admin2", pw["admin2"], kurzname="andere-schule")
    st, d = fremd.get(f"/module/{modul['id']}/lektionen")
    _zeige("19 · Admin einer anderen Organisation greift auf fremdes Modul zu (erwartet: 404)", st, d)
    st, d = fremd.get("/module")
    _zeige("19b · Andere Organisation sieht das Modul nicht in der Liste", st, d)
    print(f"\nDatenbank: {db_pfad}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
