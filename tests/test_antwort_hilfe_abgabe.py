"""Beweist: Einheitliches Antwortformat (Punkt 1), wirksame und sichtbare Hilfen (Punkt 2) und sichere
Abgabe mit Anfrage-Schlüssel gegen Doppelklicks, Netzwerk-Wiederholungen und parallele Anfragen
(Punkt 3; LE-11, PR-04, PR-06, LE-12, Spez. §5.5, §8)."""
import secrets
import threading

from sqlalchemy import select

from app.models import Hilfeereignis, Versuch, Wiederholungszustand


def _neue_uebung(seeded, login="student-a"):
    stu = seeded["login"](login, "org-a")
    st, ue = stu.post(f"/module/{seeded['modul']}/uebungen", {"lektion_ids": [seeded["lektion"]]})
    assert st == 201, ue
    return stu, ue


def _aufgabe_mit_mehrstelliger_id(seeded):
    """Single Choice mit Option-IDs wie «antwort_b» (Regressionsfall aus dem Prüfbericht)."""
    doz = seeded["login"]("dozent-a", "org-a")
    st, a = doz.post(f"/module/{seeded['modul']}/aufgaben", {
        "lernziel_id": seeded["ziel1"], "fragetyp": "single_choice",
        "aufgabe_text": "Welche Antwort ist richtig: zwei oder drei?",
        "optionen": [{"id": "antwort_a", "text": "eins"}, {"id": "antwort_b", "text": "zwei"},
                     {"id": "antwort_c", "text": "drei"}],
        "loesung": ["antwort_b"], "max_punkte": 1, "erklaerung": "Zwei ist die richtige Antwort.",
        "hinweis": "Zähle nach.", "abschnitt_ids": [seeded["abschnitte"][0]]})
    assert st == 201, a
    return a["id"]


# ---------- Punkt 1: Antwortformat ----------

def test_einzelauswahl_mit_mehrstelliger_id_wird_richtig_bewertet(seeded):
    """Beweist: «antwort_b» als Liste wird als eine Option bewertet, nicht als Zeichen (Regression Punkt 1)."""
    aid = _aufgabe_mit_mehrstelliger_id(seeded)
    stu, ue = _neue_uebung(seeded)
    st, v = stu.post(f"/uebungen/{ue['id']}/versuche", {"aufgabe_id": aid, "gegeben": ["antwort_b"]})
    assert st == 201 and v["richtig"] is True and v["punkte"] == 1.0


def test_einzelauswahl_als_text_wird_abgewiesen(seeded):
    """Beweist: Eine einzelne Option als Text statt Liste ergibt einen verständlichen Fehler (Punkt 1)."""
    aid = _aufgabe_mit_mehrstelliger_id(seeded)
    stu, ue = _neue_uebung(seeded)
    st, d = stu.post(f"/uebungen/{ue['id']}/versuche", {"aufgabe_id": aid, "gegeben": "antwort_b"})
    assert st == 422 and d["fehler"]["code"] == "antwort_ungueltig"
    assert "Liste" in d["fehler"]["nachricht"]


def test_unbekannte_option_wird_mit_namen_gemeldet(seeded):
    """Beweist: Unbekannte Option-IDs führen zu einem Validierungsfehler mit der betroffenen ID (Punkt 1)."""
    aid = _aufgabe_mit_mehrstelliger_id(seeded)
    stu, ue = _neue_uebung(seeded)
    st, d = stu.post(f"/uebungen/{ue['id']}/versuche", {"aufgabe_id": aid, "gegeben": ["antwort_z"]})
    assert st == 422 and "antwort_z" in d["fehler"]["nachricht"]


def test_einzelauswahl_mit_zwei_optionen_und_leere_auswahl_werden_abgewiesen(seeded):
    """Beweist: Bei Einzelauswahl genau eine Option; eine leere Auswahl ist unzulässig (Punkt 1)."""
    aid = _aufgabe_mit_mehrstelliger_id(seeded)
    stu, ue = _neue_uebung(seeded)
    st, d = stu.post(f"/uebungen/{ue['id']}/versuche", {"aufgabe_id": aid, "gegeben": ["antwort_a", "antwort_b"]})
    assert st == 422 and "genau eine" in d["fehler"]["nachricht"]
    st, d = stu.post(f"/uebungen/{ue['id']}/versuche", {"aufgabe_id": aid, "gegeben": []})
    assert st == 422


def test_ungueltige_datentypen_werden_abgewiesen(seeded):
    """Beweist: Zahlen, Objekte und doppelte Optionen sind keine gültigen Antworten (Punkt 1)."""
    aid = _aufgabe_mit_mehrstelliger_id(seeded)
    stu, ue = _neue_uebung(seeded)
    for ungueltig in (7, {"id": "antwort_a"}, ["antwort_a", "antwort_a"], [1]):
        st, d = stu.post(f"/uebungen/{ue['id']}/versuche", {"aufgabe_id": aid, "gegeben": ungueltig})
        assert st == 422 and d["fehler"]["code"] == "antwort_ungueltig", ungueltig


def test_luecke_nimmt_nur_text(seeded, sitzung):
    """Beweist: Lückentext akzeptiert Text bis 200 Zeichen, Listen und leere Eingaben werden abgewiesen (Punkt 1)."""
    doz = seeded["login"]("dozent-a", "org-a")
    st, a = doz.post(f"/module/{seeded['modul']}/aufgaben", {
        "lernziel_id": seeded["ziel1"], "fragetyp": "luecke", "aufgabe_text": "Wie heisst die Menge aller Ausgänge?",
        "loesung": ["Ergebnisraum"], "max_punkte": 1, "erklaerung": "Der Ergebnisraum.",
        "abschnitt_ids": [seeded["abschnitte"][0]]})
    assert st == 201, a
    stu, ue = _neue_uebung(seeded)
    st, v = stu.post(f"/uebungen/{ue['id']}/versuche", {"aufgabe_id": a["id"], "gegeben": "  ergebnisraum "})
    assert st == 201 and v["richtig"] is True
    st, d = stu.post(f"/uebungen/{ue['id']}/versuche", {"aufgabe_id": a["id"], "gegeben": ["Ergebnisraum"]})
    assert st == 422
    st, d = stu.post(f"/uebungen/{ue['id']}/versuche", {"aufgabe_id": a["id"], "gegeben": "   "})
    assert st == 422


def test_web_einzelauswahl_mit_mehrstelliger_id(seeded):
    """Beweist: Der Browserablauf sendet eine Einzelauswahl als Liste und wertet «antwort_b» richtig aus (Punkt 1)."""
    import re
    aid = _aufgabe_mit_mehrstelliger_id(seeded)
    c = seeded["app"].test_client()
    c.post("/anmelden", data={"kurzname": "org-a", "benutzername": "student-a", "passwort": "Testpasswort-2026"})
    html = c.get(f"/module/{seeded['modul']}").get_data(as_text=True)
    ue = c.post(f"/module/{seeded['modul']}/uebung", data={"lektion_ids": [seeded["lektion"]],
                                                           "csrf": re.search(r'name="csrf" value="([^"]+)"', html).group(1)})
    seite = c.get(ue.headers["Location"]).get_data(as_text=True)
    csrf = re.search(r'name="csrf" value="([^"]+)"', seite).group(1)
    # Formular der gewünschten Aufgabe: Radiobutton «antwort_b» mit Schlüssel
    abschnitt = seite.split(f'id="aufgabe-{aid}"')[1]
    schluessel = re.search(r'name="schluessel" value="([0-9a-f]+)"', abschnitt).group(1)
    antwort = c.post(f"/uebungen/{ue.headers['Location'].split('/')[-1]}/versuch",
                     data={"aufgabe_id": aid, "gegeben": "antwort_b", "csrf": csrf, "schluessel": schluessel})
    assert antwort.status_code == 302
    ergebnis = c.get(antwort.headers["Location"]).get_data(as_text=True)
    assert "Richtig" in ergebnis and "Punkte 1" in ergebnis


# ---------- Punkt 2: Hilfen ----------

def test_hinweis_wird_angezeigt_und_bleibt_nach_neuladen(seeded):
    """Beweist: Der gespeicherte Hinweis erscheint bei der Aufgabe und nach erneutem Laden (Punkt 2)."""
    aid = _aufgabe_mit_mehrstelliger_id(seeded)
    stu, ue = _neue_uebung(seeded)
    st, h = stu.post(f"/uebungen/{ue['id']}/hilfe", {"aufgabe_id": aid, "art": "hinweis"})
    assert st == 200 and h["text"] == "Zähle nach."
    st, sicht = stu.get(f"/uebungen/{ue['id']}")
    aufgabe = next(a for a in sicht["aufgaben"] if a["id"] == aid)
    assert aufgabe["offene_hilfe"]["text"] == "Zähle nach."


def test_hinweis_erscheint_im_browser_und_ist_als_hilfe_vermerkt(seeded, sitzung):
    """Beweist: Der Browser zeigt den Hinweis; die spätere Abgabe vermerkt die Hilfe (Punkt 2, PR-04)."""
    import re
    aid = _aufgabe_mit_mehrstelliger_id(seeded)
    c = seeded["app"].test_client()
    c.post("/anmelden", data={"kurzname": "org-a", "benutzername": "student-a", "passwort": "Testpasswort-2026"})
    html = c.get(f"/module/{seeded['modul']}").get_data(as_text=True)
    ue = c.post(f"/module/{seeded['modul']}/uebung", data={"lektion_ids": [seeded["lektion"]],
                                                           "csrf": re.search(r'name="csrf" value="([^"]+)"', html).group(1)})
    uid = ue.headers["Location"].split("/")[-1]
    seite = c.get(f"/uebungen/{uid}").get_data(as_text=True)
    csrf = re.search(r'name="csrf" value="([^"]+)"', seite).group(1)
    c.post(f"/uebungen/{uid}/hilfe", data={"aufgabe_id": aid, "art": "hinweis", "csrf": csrf})
    seite = c.get(f"/uebungen/{uid}").get_data(as_text=True)
    assert "Zähle nach." in seite and "wird als Hilfe vermerkt" in seite
    csrf = re.search(r'name="csrf" value="([^"]+)"', seite).group(1)
    schluessel = re.search(r'name="schluessel" value="([0-9a-f]+)"', seite.split(f'id="aufgabe-{aid}"')[1]).group(1)
    c.post(f"/uebungen/{uid}/versuch", data={"aufgabe_id": aid, "gegeben": "antwort_b", "csrf": csrf,
                                             "schluessel": schluessel})
    versuch = sitzung.scalars(select(Versuch).where(Versuch.aufgabe_id == aid)).first()
    sitzung.refresh(versuch)
    assert versuch.hilfen and versuch.hilfen[0]["art"] == "hinweis"


def test_fehlende_hilfe_wird_ehrlich_gemeldet_ohne_eintrag(seeded, sitzung):
    """Beweist: Ist keine Hilfe hinterlegt, sagt das System dies und vermerkt keine Hilfe (Punkt 2)."""
    stu, ue = _neue_uebung(seeded)
    st, h = stu.post(f"/uebungen/{ue['id']}/hilfe", {"aufgabe_id": seeded["aufgabe2"], "art": "hinweis"})
    assert st == 200 and h["text"] is None and "keine Hilfe" in h["hinweis"]
    assert sitzung.scalars(select(Hilfeereignis).where(Hilfeereignis.aufgabe_id == seeded["aufgabe2"])).all() == []


# ---------- Punkt 3: Doppelabgaben und bewusste Wiederholung ----------

def test_gleicher_schluessel_erzeugt_keinen_zweiten_versuch(seeded, sitzung):
    """Beweist: Dieselbe Anfrage zweimal ergibt genau einen Versuch und unveränderte Fortschreibung (Punkt 3)."""
    aid = _aufgabe_mit_mehrstelliger_id(seeded)
    stu, ue = _neue_uebung(seeded)
    schluessel = secrets.token_hex(12)
    st1, v1 = stu.post(f"/uebungen/{ue['id']}/versuche", {"aufgabe_id": aid, "gegeben": ["antwort_a"]}, schluessel)
    wdh = sitzung.scalars(select(Wiederholungszustand).where(Wiederholungszustand.aufgabe_id == aid)).first()
    sitzung.refresh(wdh)
    stand = (float(wdh.ease), wdh.intervall_tage, wdh.wiederholungen)
    st2, v2 = stu.post(f"/uebungen/{ue['id']}/versuche", {"aufgabe_id": aid, "gegeben": ["antwort_a"]}, schluessel)
    assert st1 == 201 and st2 == 200
    assert v2["wiederholt"] is True and v2["versuch_id"] == v1["versuch_id"]
    assert v2["hinweis_wiederholung"]
    assert len(sitzung.scalars(select(Versuch).where(Versuch.aufgabe_id == aid)).all()) == 1
    sitzung.expire_all()
    wdh = sitzung.scalars(select(Wiederholungszustand).where(Wiederholungszustand.aufgabe_id == aid)).first()
    assert (float(wdh.ease), wdh.intervall_tage, wdh.wiederholungen) == stand


def test_wiederholung_nach_hilfe_bleibt_nicht_selbststaendig(seeded, sitzung):
    """Beweist: Eine Wiederholung derselben Anfrage nach Hilfe macht die Leistung nicht selbstständig (Punkt 3)."""
    aid = _aufgabe_mit_mehrstelliger_id(seeded)
    stu, ue = _neue_uebung(seeded)
    stu.post(f"/uebungen/{ue['id']}/hilfe", {"aufgabe_id": aid, "art": "hinweis"})
    schluessel = secrets.token_hex(12)
    _, v1 = stu.post(f"/uebungen/{ue['id']}/versuche", {"aufgabe_id": aid, "gegeben": ["antwort_b"]}, schluessel)
    _, v2 = stu.post(f"/uebungen/{ue['id']}/versuche", {"aufgabe_id": aid, "gegeben": ["antwort_b"]}, schluessel)
    assert v1["selbststaendig"] is False and v2["selbststaendig"] is False
    assert v2["versuch_id"] == v1["versuch_id"]


def test_neue_bearbeitung_nach_frueherer_loesung_ist_nicht_selbststaendig(seeded, sitzung):
    """Beweist: Nach einer angezeigten Lösung zählt eine erneute Abgabe nicht als selbstständige Leistung (Punkt 3)."""
    aid = _aufgabe_mit_mehrstelliger_id(seeded)
    stu, ue = _neue_uebung(seeded)
    _, erst = stu.post(f"/uebungen/{ue['id']}/versuche", {"aufgabe_id": aid, "gegeben": ["antwort_a"]})
    st, zweit = stu.post(f"/uebungen/{ue['id']}/versuche", {"aufgabe_id": aid, "gegeben": ["antwort_b"]})
    assert st == 201 and zweit["versuchsnummer"] == 2 and zweit["versuch_id"] != erst["versuch_id"]
    assert zweit["richtig"] is True and zweit["selbststaendig"] is False
    sicht = stu.get(f"/uebungen/{ue['id']}")[1]
    aufgabe = next(a for a in sicht["aufgaben"] if a["id"] == aid)
    assert aufgabe["naechste_versuchsnummer"] == 3


def test_schluessel_fuer_andere_aufgabe_wird_abgewiesen(seeded):
    """Beweist: Ein Schlüssel kann nicht für eine andere Abgabe wiederverwendet werden (Punkt 3)."""
    aid = _aufgabe_mit_mehrstelliger_id(seeded)
    stu, ue = _neue_uebung(seeded)
    schluessel = secrets.token_hex(12)
    stu.post(f"/uebungen/{ue['id']}/versuche", {"aufgabe_id": aid, "gegeben": ["antwort_a"]}, schluessel)
    st, d = stu.post(f"/uebungen/{ue['id']}/versuche", {"aufgabe_id": seeded["aufgabe2"], "gegeben": ["a", "b"]},
                     schluessel)
    assert st == 409 and d["fehler"]["code"] == "schluessel_wiederverwendet"


def test_fehlender_oder_ungueltiger_schluessel_wird_abgewiesen(seeded):
    """Beweist: Abgaben ohne gültigen Anfrage-Schlüssel werden nicht angenommen (Punkt 3)."""
    aid = _aufgabe_mit_mehrstelliger_id(seeded)
    stu, ue = _neue_uebung(seeded)
    st, d = stu.post(f"/uebungen/{ue['id']}/versuche", {"aufgabe_id": aid, "gegeben": ["antwort_a"]}, "kurz")
    assert st == 422 and d["fehler"]["code"] == "schluessel_ungueltig"


def test_gleichzeitige_doppelabgaben_erzeugen_genau_einen_versuch(app, seeded, sitzung):
    """Beweist: Nahezu gleichzeitige Anfragen mit demselben Schlüssel erzeugen genau einen Versuch (Punkt 3)."""
    from app.models import Konto
    aid = _aufgabe_mit_mehrstelliger_id(seeded)
    stu, ue = _neue_uebung(seeded)
    schluessel = secrets.token_hex(12)
    ergebnisse = []
    barriere = threading.Barrier(3)

    def sende():
        barriere.wait()
        c = app.test_client()
        anmeldung = c.post("/api/v1/auth/anmelden", json={"kurzname": "org-a", "benutzername": "student-a",
                                                          "passwort": "Testpasswort-2026"}).get_json()
        a = c.post(f"/api/v1/uebungen/{ue['id']}/versuche", json={"aufgabe_id": aid, "gegeben": ["antwort_b"]},
                   headers={"X-CSRF-Token": anmeldung["csrf"], "Idempotency-Key": schluessel})
        ergebnisse.append(a.status_code)

    threads = [threading.Thread(target=sende) for _ in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=60)
    sitzung.expire_all()
    anzahl = len(sitzung.scalars(select(Versuch).where(Versuch.aufgabe_id == aid,
                                                       Versuch.idempotenz_schluessel == schluessel)).all())
    assert anzahl == 1
    assert all(code in (200, 201) for code in ergebnisse), ergebnisse
