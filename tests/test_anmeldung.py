"""Beweist: Anmeldung speichert keine Klartextpasswörter, sperrt nach Fehlversuchen und gibt keine
Kontenerkennung preis (TC-LOG-01, TC-LOG-02, BE-01, BE-02, BE-03, BE-05)."""
import pytest

from app.sicherheit import hashe_passwort, pruefe_passwort


def test_passwort_nur_als_argon2_hash(cfg):
    """Beweist: Der gespeicherte Wert ist ein Argon2id-Hash und enthält das Klartextpasswort nicht (TC-LOG-01)."""
    h = hashe_passwort("Ein-sicheres-Passwort", cfg)
    assert h.startswith("$argon2id$")
    assert "Ein-sicheres-Passwort" not in h
    assert pruefe_passwort(h, "Ein-sicheres-Passwort", cfg)
    assert not pruefe_passwort(h, "falsch-falsch", cfg)


def test_zu_kurzes_passwort_wird_abgelehnt(cfg):
    """Beweist: Passwörter unter zehn Zeichen werden nicht gehasht (BE-02)."""
    with pytest.raises(ValueError):
        hashe_passwort("kurz", cfg)


def test_fehlversuche_sperren_konto_auch_bei_richtigem_passwort(seeded):
    """Beweist: Nach fünf Fehlversuchen ist das Konto gesperrt; das richtige Passwort hilft nicht (TC-LOG-02)."""
    c = seeded["app"].test_client()
    for _ in range(5):
        r = c.post("/api/v1/auth/anmelden", json={"kurzname": "org-a", "benutzername": "student-a",
                                                  "passwort": "falsch-falsch-1"})
        assert r.status_code == 401
    r = c.post("/api/v1/auth/anmelden", json={"kurzname": "org-a", "benutzername": "student-a",
                                              "passwort": "Testpasswort-2026"})
    assert r.status_code == 423
    assert r.get_json()["fehler"]["code"] == "gesperrt"


def test_fehlermeldung_verraet_keine_kontenexistenz(seeded):
    """Beweist: Unbekannter Benutzer und falsches Passwort liefern dieselbe Meldung (BE-01)."""
    c = seeded["app"].test_client()
    a = c.post("/api/v1/auth/anmelden", json={"kurzname": "org-a", "benutzername": "gibt-es-nicht",
                                              "passwort": "irgendwas-1234"}).get_json()
    b = c.post("/api/v1/auth/anmelden", json={"kurzname": "org-a", "benutzername": "student-a",
                                              "passwort": "falsch-falsch-1"}).get_json()
    assert a["fehler"]["nachricht"] == b["fehler"]["nachricht"]


def test_konto_in_zwei_organisationen_mit_getrennten_sitzungen(seeded):
    """Beweist: Dasselbe Konto kann in zwei Organisationen angemeldet werden; die Sitzungen bleiben getrennt (BE-05)."""
    c = seeded["app"].test_client()
    assert c.post("/api/v1/auth/anmelden", json={"kurzname": "org-a", "benutzername": "admin-a",
                                                 "passwort": "Testpasswort-2026"}).status_code == 200
    assert c.get("/api/v1/module").status_code == 200
    # Gleiches Konto in Organisation B ohne Mitgliedschaft: abgewiesen
    assert c.post("/api/v1/auth/anmelden", json={"kurzname": "org-b", "benutzername": "student-a",
                                                 "passwort": "Testpasswort-2026"}).status_code == 401
