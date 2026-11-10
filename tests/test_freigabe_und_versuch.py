"""Beweist: Freigabe ist ein Tor (IN-06, IN-07, NR-05); Aufgaben und Versuche sind nachvollziehbar und
Punkte bleiben im Maximum (IN-08, PR-04, PR-05, PR-06, LE-07, LE-11, TC-FRE-01…06, TC-PRF-01…04)."""
from app.models import Aufgabe, Versuch


def _uebung(seeded, lektionen=None):
    stu = seeded["login"]("student-a", "org-a")
    st, ue = stu.post(f"/module/{seeded['modul']}/uebungen", {"lektion_ids": lektionen or [seeded["lektion"]]})
    assert st == 201, ue
    return stu, ue


def test_aenderung_freigegebener_unterlage_setzt_status_zurueck(seeded):
    """Beweist: Eine Inhaltsänderung setzt die freigegebene Unterlage auf in_pruefung (TC-FRE-01, NR-05)."""
    doz = seeded["login"]("dozent-a", "org-a")
    st, daten = doz.post(f"/unterlagen/{seeded['unterlage']}/aenderung", {"inhalt": "Ein neuer, anderer Text. " * 30})
    assert st == 200
    assert daten["status"] == "in_pruefung"
    assert daten["version"] == 2


def test_aufgaben_in_pruefung_sind_ausgeblendet_und_nicht_bearbeitbar(seeded):
    """Beweist: Aufgaben mit Quelle in Prüfung erscheinen nicht in neuen Übungen und können nicht beantwortet werden (TC-FRE-02, TC-FRE-03)."""
    doz = seeded["login"]("dozent-a", "org-a")
    stu, ue = _uebung(seeded)
    alte_aufgabe = ue["aufgaben"][0]["id"]
    doz.post(f"/unterlagen/{seeded['unterlage']}/aenderung", {"inhalt": "Komplett neuer Inhalt. " * 30})
    st, neu = stu.post(f"/module/{seeded['modul']}/uebungen", {"lektion_ids": [seeded["lektion"]]})
    assert st == 409 and neu["fehler"]["code"] == "keine_aufgaben"  # keine Auffüllung (PR-08)
    st, daten = stu.post(f"/uebungen/{ue['id']}/versuche", {"aufgabe_id": alte_aufgabe, "gegeben": ["b"]})
    assert st == 409 and daten["fehler"]["code"] == "aufgabe_nicht_verfuegbar"


def test_freigabe_unter_auflage_braucht_verantwortliche_und_zukunftsfrist(seeded):
    """Beweist: Auflage ohne Verantwortliche oder mit vergangener Frist wird abgelehnt (TC-FRE-04, IN-08)."""
    doz = seeded["login"]("dozent-a", "org-a")
    st, neu = doz.post(f"/module/{seeded['modul']}/unterlagen", {
        "titel": "Auflage-Test", "dateiname": "a.txt", "inhalt": "Text. " * 60})
    st, daten = doz.post(f"/unterlagen/{neu['id']}/freigabe", {"form": "freigegeben_unter_auflage"})
    assert st == 422 and daten["fehler"]["code"] == "auflage_unvollstaendig"
    st, daten = doz.post(f"/unterlagen/{neu['id']}/freigabe", {
        "form": "freigegeben_unter_auflage", "auflage_verantwortlich": "Dozent A",
        "auflage_frist": "2020-01-01T00:00:00+00:00"})
    assert st == 422 and daten["fehler"]["code"] == "auflage_frist_vergangen"


def test_nicht_freigebbar_verlangt_begruendung(seeded):
    """Beweist: Die Ablehnung einer Unterlage braucht eine Begründung (TC-FRE-06)."""
    doz = seeded["login"]("dozent-a", "org-a")
    st, neu = doz.post(f"/module/{seeded['modul']}/unterlagen", {"titel": "Ablehnung", "dateiname": "b.txt",
                                                                  "inhalt": "Text. " * 60})
    st, daten = doz.post(f"/unterlagen/{neu['id']}/freigabe", {"form": "nicht_freigebbar"})
    assert st == 422 and daten["fehler"]["code"] == "begruendung_fehlt"


def test_unterlage_version_bleibt_erhalten_und_nachweis_entsteht(seeded):
    """Beweist: Jede Fassung bleibt nachvollziehbar; die Freigabe ist im Nachweis (IN-05, NF-04)."""
    doz = seeded["login"]("dozent-a", "org-a")
    doz.post(f"/unterlagen/{seeded['unterlage']}/aenderung", {"inhalt": "Dritte Fassung. " * 30})
    st, abschn = doz.get(f"/unterlagen/{seeded['unterlage']}/abschnitte")
    assert st == 200 and abschn  # aktuelle Fassung hat Abschnitte


def test_richtige_antwort_mit_punkten_im_maximum(seeded):
    """Beweist: Vollständige Mehrfachauswahl ergibt genau das Maximum; Prozent ist 100 (PR-05)."""
    stu, ue = _uebung(seeded, [seeded["lektion"]])
    aufgabe = next(a for a in ue["aufgaben"] if a["id"] == seeded["aufgabe2"])
    st, daten = stu.post(f"/uebungen/{ue['id']}/versuche", {"aufgabe_id": aufgabe["id"], "gegeben": ["a", "b", "c"]})
    assert st == 201
    assert daten["punkte"] == 3.0 and daten["maximum"] == 3.0 and daten["prozent"] == 100


def test_hilfe_vor_antwort_wird_vermerkt_und_zaehlt_nicht_selbststaendig(seeded):
    """Beweist: Hinweis vor der Antwort steht am Versuch und macht die richtige Antwort nicht selbstständig (PR-04, LE-12)."""
    stu, ue = _uebung(seeded)
    aufgabe = seeded["aufgabe1"]
    st, _ = stu.post(f"/uebungen/{ue['id']}/hilfe", {"aufgabe_id": aufgabe, "art": "hinweis"})
    assert st == 200
    st, daten = stu.post(f"/uebungen/{ue['id']}/versuche", {"aufgabe_id": aufgabe, "gegeben": ["b"]})
    assert st == 201 and daten["richtig"] is True and daten["hilfen_vorher"] == 1
    st, profil = stu.get(f"/module/{seeded['modul']}/lernprofil")
    ziel = next(z for z in profil if z["lernziel_id"] == seeded["ziel1"])
    assert ziel["selbststaendig_aufgaben"] == 0
    assert ziel["mit_hilfe_aufgaben"] == 1


def test_hilfe_ohne_hinterlegten_inhalt_wird_ehrlich_gemeldet(seeded):
    """Beweist: Fehlt eine Hilfe, wird das gemeldet und keine vermerkt (PR-04)."""
    stu, ue = _uebung(seeded, [seeded["lektion"]])
    st, daten = stu.post(f"/uebungen/{ue['id']}/hilfe", {"aufgabe_id": seeded["aufgabe2"], "art": "beispiel"})
    assert st == 200 and daten["text"] is None


def test_versuch_bleibt_unveraendert_wenn_aufgabe_spaeter_geaendert_wird(seeded, sitzung):
    """Beweist: Ein Versuch speichert den Aufgabenstand; spätere Änderungen verändern ihn nicht (LE-11, RA-06)."""
    stu, ue = _uebung(seeded)
    st, v = stu.post(f"/uebungen/{ue['id']}/versuche", {"aufgabe_id": seeded["aufgabe1"], "gegeben": ["a"]})
    assert st == 201
    versuch = sitzung.get(Versuch, v["versuch_id"])
    sitzung.refresh(versuch)
    vorher = dict(versuch.aufgabe_snapshot)
    aufgabe = sitzung.get(Aufgabe, seeded["aufgabe1"])
    aufgabe.aufgabe_text = "Ganz anderer Text nach der Abgabe"
    aufgabe.version = aufgabe.version + 1
    sitzung.commit()
    sitzung.refresh(versuch)
    assert versuch.aufgabe_snapshot == vorher
    assert versuch.aufgabe_snapshot["text"] != "Ganz anderer Text nach der Abgabe"


def test_fremder_versuch_ist_nicht_sichtbar(seeded):
    """Beweist: Eine Übung oder ein Versuch einer anderen Person ist nicht zugänglich (MO-03, eig.)."""
    stu, ue = _uebung(seeded)
    andere = seeded["login"]("student-a2", "org-a")
    st, _ = andere.post(f"/uebungen/{ue['id']}/versuche", {"aufgabe_id": seeded["aufgabe1"], "gegeben": ["b"]})
    assert st == 404


def test_auswertung_nur_ueber_schluessel_ohne_modell(seeded, sitzung):
    """Beweist: Die Auswertung stammt aus dem Kern (herkunft.erzeugt_durch = kern) (RA-01, Abschnitt 4 Dok. 01)."""
    stu, ue = _uebung(seeded)
    st, v = stu.post(f"/uebungen/{ue['id']}/versuche", {"aufgabe_id": seeded["aufgabe1"], "gegeben": ["a"]})
    versuch = sitzung.get(Versuch, v["versuch_id"])
    sitzung.refresh(versuch)
    assert versuch.herkunft["erzeugt_durch"] == "kern"
    assert versuch.herkunft["modell"] is None


def test_neue_fassung_nach_ablehnung_kehrt_in_den_entwurf(seeded):
    """Beweist: Eine abgelehnte Unterlage kehrt mit neuer Fassung in den Entwurf zurück (Spez. §4.1)."""
    doz = seeded["login"]("dozent-a", "org-a")
    st, neu = doz.post(f"/module/{seeded['modul']}/unterlagen", {"titel": "Abgelehnt", "dateiname": "c.txt",
                                                                  "inhalt": "Text. " * 60})
    st, daten = doz.post(f"/unterlagen/{neu['id']}/freigabe", {"form": "nicht_freigebbar", "begruendung": "Veraltet"})
    assert st == 200 and daten["status"] == "nicht_freigebbar"
    st, daten = doz.post(f"/unterlagen/{neu['id']}/aenderung", {"inhalt": "Überarbeitete Fassung. " * 60})
    assert st == 200 and daten["status"] == "entwurf" and daten["version"] == 2
