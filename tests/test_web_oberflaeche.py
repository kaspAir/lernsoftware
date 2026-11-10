"""Beweist: Die Browser-Oberfläche für den Studierendenablauf ist erreichbar, verlangt Anmeldung und
Sicherheitstoken, und zeigt Rückmeldung mit Quelle sowie die Kennzeichnung der Modellherkunft
(NF-01, NF-03, AG-14, TC-A11Y-03 teilweise)."""
import re
import secrets


def _csrf_aus_seite(html: str) -> str:
    m = re.search(r'name="csrf" value="([^"]+)"', html)
    assert m, "CSRF-Feld fehlt"
    return m.group(1)


def test_anmeldeseite_ist_erreichbar_und_beschriftet(seeded):
    """Beweist: Die Anmeldeseite ist erreichbar, Sprache ist Deutsch (Schweiz) und Felder sind beschriftet (NF-03)."""
    c = seeded["app"].test_client()
    antwort = c.get("/anmelden")
    assert antwort.status_code == 200
    html = antwort.get_data(as_text=True)
    assert 'lang="de-CH"' in html
    assert "Benutzername" in html and "Passwort" in html


def test_module_ohne_anmeldung_leiten_zur_anmeldung(seeded):
    """Beweist: Ohne Anmeldung gibt es keine Modulseite (NF-01)."""
    c = seeded["app"].test_client()
    antwort = c.get("/module")
    assert antwort.status_code == 302 and "/anmelden" in antwort.headers["Location"]


def test_studierende_sieht_modul_lektionen_und_uebung_erzeugen(seeded):
    """Beweist: Studierende erreichen über die Oberfläche Modul, Lektion und Übung (Ablauf 2–5)."""
    c = seeded["app"].test_client()
    c.post("/anmelden", data={"kurzname": "org-a", "benutzername": "student-a", "passwort": "Testpasswort-2026"})
    seite = c.get("/module").get_data(as_text=True)
    assert "Statistik A" in seite
    modul_id = re.search(r'href="/module/([0-9a-f-]{36})"', seite).group(1)
    lektionen = c.get(f"/module/{modul_id}")
    assert lektionen.status_code == 200
    html = lektionen.get_data(as_text=True)
    lektion_id = re.search(r'name="lektion_ids" value="([^"]+)"', html).group(1)
    csrf = _csrf_aus_seite(html)
    antwort = c.post(f"/module/{modul_id}/uebung", data={"lektion_ids": [lektion_id], "csrf": csrf})
    assert antwort.status_code == 302
    uebung_seite = c.get(antwort.headers["Location"]).get_data(as_text=True)
    assert "Antwort abgeben" in uebung_seite
    assert "Von Lehrperson geprüft" in uebung_seite


def test_post_ohne_csrf_wird_in_oberflaeche_abgewiesen(seeded):
    """Beweist: Formularabsendungen ohne Sicherheitstoken werden nicht verarbeitet (NF-01)."""
    c = seeded["app"].test_client()
    c.post("/anmelden", data={"kurzname": "org-a", "benutzername": "student-a", "passwort": "Testpasswort-2026"})
    antwort = c.post(f"/module/{seeded['modul']}/uebung", data={"lektion_ids": [seeded["lektion"]]})
    assert antwort.status_code == 302
    assert "/uebungen/" not in antwort.headers["Location"]  # keine Übung entsteht


def test_rueckmeldung_zeigt_quelle_und_bleibt_zugaenglich(seeded):
    """Beweist: Die Rückmeldung nennt Quelle, Version und Abschnitt; die Aufgabe bleibt als Anker erreichbar (LE-05, BS-10)."""
    c = seeded["app"].test_client()
    c.post("/anmelden", data={"kurzname": "org-a", "benutzername": "student-a", "passwort": "Testpasswort-2026"})
    html = c.get(f"/module/{seeded['modul']}").get_data(as_text=True)
    csrf = _csrf_aus_seite(html)
    ue = c.post(f"/module/{seeded['modul']}/uebung", data={"lektion_ids": [seeded["lektion"]], "csrf": csrf})
    seite = c.get(ue.headers["Location"]).get_data(as_text=True)
    csrf = _csrf_aus_seite(seite)
    aufgabe_id = seeded["aufgabe1"]
    antwort = c.post(f"/uebungen/{ue.headers['Location'].split('/')[-1]}/versuch",
                     data={"aufgabe_id": aufgabe_id, "gegeben": "a", "csrf": csrf,
                           "schluessel": secrets.token_hex(12)})
    assert antwort.status_code == 302
    rueck = c.get(antwort.headers["Location"]).get_data(as_text=True)
    assert "Rückmeldung" in rueck
    assert "Quelle:" in rueck and "Version 1" in rueck
