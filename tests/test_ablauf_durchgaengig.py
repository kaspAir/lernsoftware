"""Beweist: Der durchgängige Lernablauf des Inkrements 1 funktioniert über die Schnittstelle:
Lernorganisation → Anmeldung → Modul und Zuweisung → Lektion mit Lernziel → Unterlage → Freigabe →
Aufgaben → Übung → Hilfe → Antwort → Rückmeldung mit Quelle → Rückfrage → Lernprofil → Nachweise
(Demonstrationsablauf Dokument 07 §5; Abnahme-Kriterium Inkrement 1).
"""
from sqlalchemy import select

from app.models import Nachweis


def test_durchgaengiger_lernablauf(seeded, sitzung):
    stu = seeded["login"]("student-a", "org-a")

    # Übung zu einer Lektion
    st, ue = stu.post(f"/module/{seeded['modul']}/uebungen", {"lektion_ids": [seeded["lektion"]]})
    assert st == 201
    assert {a["id"] for a in ue["aufgaben"]} == {seeded["aufgabe1"], seeded["aufgabe2"]}
    # Lösungsschlüssel ist den Lernenden nicht zugänglich
    assert all("loesung" not in a and "erklaerung" not in a for a in ue["aufgaben"])

    # Hilfe, dann falsche Antwort mit Rückmeldung und Quelle
    stu.post(f"/uebungen/{ue['id']}/hilfe", {"aufgabe_id": seeded["aufgabe1"], "art": "hinweis"})
    st, falsch = stu.post(f"/uebungen/{ue['id']}/versuche", {"aufgabe_id": seeded["aufgabe1"], "gegeben": "a",
                                                             "selbsteinschaetzung": "unsicher"})
    assert st == 201 and falsch["richtig"] is False and falsch["hilfen_vorher"] == 1
    assert falsch["quellen"] and falsch["quellen"][0]["abschnitt_id"] in seeded["abschnitte"]
    assert falsch["faellig_am"]

    # Richtige Mehrfachauswahl ohne Hilfe
    st, richtig = stu.post(f"/uebungen/{ue['id']}/versuche", {"aufgabe_id": seeded["aufgabe2"],
                                                              "gegeben": ["a", "b"]})
    assert st == 201 and richtig["punkte"] == 2.0 and richtig["prozent"] == 100

    # Rückfrage zum Ergebnis (Testadapter, SIMULIERT)
    st, gespraech = stu.post(f"/versuche/{falsch['versuch_id']}/gespraech",
                             {"frage": "Warum ist die Anzahl sechs?", "form": "rueckfrage"})
    assert st == 200
    assert gespraech["herkunft"]["herkunft"] == "SIMULIERT"
    assert all(q["fachlich"] == "ungeprueft" for q in gespraech["quellen"])

    # Lernprofil: Hilfe zählt nicht als selbstständig, richtige Antwort ohne Hilfe zählt
    st, profil = stu.get(f"/module/{seeded['modul']}/lernprofil")
    assert st == 200
    ziel1 = next(z for z in profil if z["lernziel_id"] == seeded["ziel1"])
    ziel2 = next(z for z in profil if z["lernziel_id"] == seeded["ziel2"])
    assert ziel1["selbststaendig_aufgaben"] == 0 and ziel1["evidenzlage"] == "noch_nicht_belegt"
    assert ziel2["selbststaendig_aufgaben"] == 1 and ziel2["evidenzlage"] == "teilweise_belegt"

    # Nachweise zu Übung, Versuchen und Rückfrage liegen vor (RA-13)
    arten = {n.art for n in sitzung.scalars(select(Nachweis)).all()}
    assert {"uebung_erzeugt", "versuch", "modellaufruf", "unterlage_hochgeladen", "freigabe"} <= arten
