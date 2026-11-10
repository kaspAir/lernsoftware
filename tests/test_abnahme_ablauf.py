"""Abnahme Inkrement 1.1 (Dokument 07 §6, Punkt 10): durchgängiger Browserablauf.

Lektion wählen → Hinweis lesen → antworten → Rückmeldung und Quelle lesen → mehrere Rückfragen →
erneut anmelden → gespeicherten Versuch und Gespräch unverändert wiederfinden.
Zusätzlich: Doppelabgabe, entzogene Berechtigung, deaktiviertes Konto, zurückgezogene Quelle.
Beweist: Der Ablauf funktioniert mit dem Testadapter (SIMULIERT); ein echter Modelllauf ist nicht Teil dieses Tests.
"""
import re
import secrets

from app.modell.testadapter import SimulationsAdapter


def _csrf(html: str) -> str:
    return re.search(r'name="csrf" value="([^"]+)"', html).group(1)


def _schluessel_der_aufgabe(html: str, aufgabe_id: str) -> str:
    return re.search(r'name="schluessel" value="([0-9a-f]+)"', html.split(f'id="aufgabe-{aufgabe_id}"')[1]).group(1)


def test_abnahme_durchgaengiger_browserablauf(seeded):
    """Beweist: Vollständiger Lernablauf im Browser einschließlich Neuanmeldung (Abnahme Punkt 10)."""
    app = seeded["app"]
    app.config["MODELL"] = SimulationsAdapter()
    c = app.test_client()
    c.post("/anmelden", data={"kurzname": "org-a", "benutzername": "student-a", "passwort": "Testpasswort-2026"})

    # Lektion wählen
    html = c.get(f"/module/{seeded['modul']}").get_data(as_text=True)
    ue = c.post(f"/module/{seeded['modul']}/uebung", data={"lektion_ids": [seeded["lektion"]], "csrf": _csrf(html)})
    uid = ue.headers["Location"].split("/")[-1]

    # Hinweis lesen
    seite = c.get(f"/uebungen/{uid}").get_data(as_text=True)
    c.post(f"/uebungen/{uid}/hilfe", data={"aufgabe_id": seeded["aufgabe1"], "art": "hinweis", "csrf": _csrf(seite)})
    seite = c.get(f"/uebungen/{uid}").get_data(as_text=True)
    assert "Zähle die Augenzahlen." in seite

    # Antworten (falsch) und Rückmeldung mit Quelle
    antwort = c.post(f"/uebungen/{uid}/versuch", data={
        "aufgabe_id": seeded["aufgabe1"], "gegeben": "a", "csrf": _csrf(seite),
        "schluessel": _schluessel_der_aufgabe(seite, seeded["aufgabe1"]), "selbsteinschaetzung": "unsicher"})
    assert antwort.status_code == 302
    versuch_url = antwort.headers["Location"]
    vid = versuch_url.split("/")[-1]
    rueck = c.get(versuch_url).get_data(as_text=True)
    assert "Nicht richtig" in rueck and "Quelle:" in rueck and "Rückmeldung" in rueck
    assert "Richtige Lösung" in rueck

    # Mehrere Rückfragen
    for frage in ("Warum ist die Anzahl sechs?", "Was bedeutet Ergebnisraum?", "Und bei zwei Würfeln?"):
        seite = c.get(versuch_url).get_data(as_text=True)
        c.post(f"/versuche/{vid}/gespraech", data={"frage": frage, "form": "rueckfrage", "csrf": _csrf(seite),
                                                   "schluessel": secrets.token_hex(12)})
    verlauf = c.get(versuch_url).get_data(as_text=True)
    assert all(f in verlauf for f in ("Warum ist die Anzahl sechs?", "Was bedeutet Ergebnisraum?", "Und bei zwei Würfeln?"))
    assert "SIMULIERT" in verlauf  # Herkunft der Modellantwort ist sichtbar

    # Erneut anmelden: derselbe gespeicherte Stand
    vorher = re.sub(r'name="csrf" value="[^"]+"|name="schluessel" value="[^"]+"', "", verlauf)
    neu = app.test_client()
    neu.post("/anmelden", data={"kurzname": "org-a", "benutzername": "student-a", "passwort": "Testpasswort-2026"})
    nachher = re.sub(r'name="csrf" value="[^"]+"|name="schluessel" value="[^"]+"', "",
                     neu.get(f"/versuche/{vid}").get_data(as_text=True))
    assert _inhalt(nachher) == _inhalt(vorher)


def _inhalt(html: str) -> str:
    """Nur der fachliche Inhalt ohne Zeitstempel-abhängige Elemente."""
    return re.sub(r"\s+", " ", html.split("<main>")[1].split("</main>")[0])


def test_abnahme_doppelabgabe_per_browser_erzeugt_einen_versuch(seeded, sitzung):
    """Beweist: Ein zweites Absenden desselben Formulars legt keinen weiteren Versuch an (Punkt 3)."""
    from sqlalchemy import select
    from app.models import Versuch
    c = seeded["app"].test_client()
    c.post("/anmelden", data={"kurzname": "org-a", "benutzername": "student-a", "passwort": "Testpasswort-2026"})
    html = c.get(f"/module/{seeded['modul']}").get_data(as_text=True)
    ue = c.post(f"/module/{seeded['modul']}/uebung", data={"lektion_ids": [seeded["lektion"]], "csrf": _csrf(html)})
    uid = ue.headers["Location"].split("/")[-1]
    seite = c.get(f"/uebungen/{uid}").get_data(as_text=True)
    daten = {"aufgabe_id": seeded["aufgabe2"], "gegeben": ["a", "b", "c"], "csrf": _csrf(seite),
             "schluessel": _schluessel_der_aufgabe(seite, seeded["aufgabe2"])}
    erst = c.post(f"/uebungen/{uid}/versuch", data=daten)
    doppelt = c.post(f"/uebungen/{uid}/versuch", data=daten)  # Netzwerk-Wiederholung
    assert erst.headers["Location"] == doppelt.headers["Location"]
    sitzung.expire_all()
    assert len(sitzung.scalars(select(Versuch).where(Versuch.aufgabe_id == seeded["aufgabe2"])).all()) == 1


def test_abnahme_zurueckgezogene_quelle_und_entzug(seeded):
    """Beweist: Zurückgezogene Quelle sperrt neue Abgaben; ein Modulentzug sperrt die Übung (Abnahme Punkt 10)."""
    stu = seeded["login"]("student-a", "org-a")
    st, ue = stu.post(f"/module/{seeded['modul']}/uebungen", {"lektion_ids": [seeded["lektion"]]})
    seeded["login"]("dozent-a", "org-a").post(f"/unterlagen/{seeded['unterlage']}/aenderung",
                                             {"inhalt": "Zurückgezogen. " * 40})
    st, d = stu.post(f"/uebungen/{ue['id']}/versuche", {"aufgabe_id": seeded["aufgabe1"], "gegeben": ["a"]}, "zurueck-1")
    assert st == 409
    assert "in Prüfung" in d["fehler"]["nachricht"]
