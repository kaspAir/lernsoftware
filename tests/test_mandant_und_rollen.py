"""Beweist: Organisationstrennung, Modulzugriff, Freigabeberechtigung und CSRF-Schutz wirken
serverseitig (TC-MAND-01, TC-MAND-02, TC-MAND-04, TC-MOD-01, TC-MOD-03, TC-MOD-04; NF-06)."""
import pytest

from app.db import mandant_abfrage
from app.models import Aufgabe, Unterlage


def test_fremde_unterlage_ist_nicht_auffindbar(seeded):
    """Beweist: Eine Unterlage der Organisation A ist für Organisation B nicht vorhanden (TC-MAND-01)."""
    b = seeded["login"]("admin-b", "org-b")
    status, daten = b.get(f"/unterlagen/{seeded['unterlage']}/abschnitte")
    assert status == 404
    assert daten["fehler"]["code"] == "nicht_gefunden"


def test_fremdes_modul_nicht_in_liste_und_nicht_lesbar(seeded):
    """Beweist: Modul der Organisation A erscheint bei Organisation B weder in der Liste noch im Detail (TC-MAND-01)."""
    b = seeded["login"]("admin-b", "org-b")
    status, liste = b.get("/module")
    assert status == 200 and liste == []
    status, _ = b.get(f"/module/{seeded['modul']}/lektionen")
    assert status == 404


def test_mandantenlose_abfrage_wird_verweigert():
    """Beweist: Die Abfragefunktion verlangt einen Mandantenkontext; ohne ihn entsteht keine Abfrage (ADR-L-006)."""
    with pytest.raises(ValueError):
        mandant_abfrage(Unterlage, "")
    with pytest.raises(ValueError):
        mandant_abfrage(Aufgabe, None)


def test_mandant_abfrage_liefert_nur_eigene_zeilen(seeded, sitzung):
    """Beweist: Die mandantengebundene Abfrage liefert ausschliesslich Zeilen der angegebenen Organisation (TC-MAND-02)."""
    assert sitzung.scalars(mandant_abfrage(Unterlage, seeded["org_b"])).all() == []
    assert len(sitzung.scalars(mandant_abfrage(Unterlage, seeded["org"])).all()) >= 1


def test_superadmin_sieht_nur_registrierungsdaten(seeded):
    """Beweist: Der Super-Admin erhält Registrierungsfelder, keine Inhalte (TC-MAND-04, PL-02)."""
    sa = seeded["app"].test_client()
    assert sa.post("/api/v1/auth/anmelden", json={"benutzername": "plattform-test",
                                                  "passwort": "Superadmin-Test-2026"}).status_code == 200
    antwort = sa.get("/api/v1/superadmin/lernorganisationen").get_json()
    assert antwort, "Register sollte Organisationen enthalten"
    for zeile in antwort:
        assert set(zeile) <= {"id", "name", "kurzname", "status", "erstellt_am"}


def test_superadmin_hat_keinen_zugriff_auf_inhalte(seeded):
    """Beweist: Ein Super-Admin ohne Organisationssitzung kann keine Inhalte lesen (PL-02)."""
    sa = seeded["app"].test_client()
    sa.post("/api/v1/auth/anmelden", json={"benutzername": "plattform-test", "passwort": "Superadmin-Test-2026"})
    assert sa.get(f"/api/v1/unterlagen/{seeded['unterlage']}/abschnitte").status_code == 401


def test_studierende_sieht_nur_zugewiesene_module(seeded):
    """Beweist: Studierende sehen Module nur mit Zuweisung (TC-MOD-01, MO-03)."""
    adm = seeded["login"]("admin-a", "org-a")
    st, neu = adm.post("/module", {"bezeichnung": "Nicht zugewiesen"})
    assert st == 201
    stu = seeded["login"]("student-a", "org-a")
    status, liste = stu.get("/module")
    ids = [m["id"] for m in liste]
    assert seeded["modul"] in ids
    assert neu["id"] not in ids
    assert stu.get(f"/module/{neu['id']}/lektionen")[0] == 404


def test_assistenz_darf_nicht_freigeben_ohne_delegation(seeded):
    """Beweist: Assistenz ohne Delegation erhält keine Freigabe (TC-MOD-03, D-03)."""
    ass = seeded["login"]("assistenz-a", "org-a")
    status, daten = ass.post(f"/unterlagen/{seeded['unterlage']}/freigabe", {"form": "freigegeben"})
    assert status == 403
    assert daten["fehler"]["code"] == "nicht_berechtigt"


def test_delegierte_assistenz_darf_freigeben(seeded):
    """Beweist: Nach ausdrücklicher Delegation darf die Assistenz fachlich freigeben (D-03)."""
    adm = seeded["login"]("admin-a", "org-a")
    st, _ = adm.post(f"/module/{seeded['modul']}/zuweisungen", {
        "konto_id": seeded["konto"]["assistenz-a"], "rolle": "assistenz", "freigabe_delegiert": True})
    assert st == 201
    ass = seeded["login"]("assistenz-a", "org-a")
    st, neu = ass.post(f"/module/{seeded['modul']}/unterlagen", {
        "titel": "Zweite Unterlage", "dateiname": "zwei.txt", "inhalt": "Ein Text für die Freigabe. " * 20})
    assert st == 201
    st, daten = ass.post(f"/unterlagen/{neu['id']}/freigabe", {"form": "freigegeben"})
    assert st == 200 and daten["status"] == "freigegeben"


def test_admin_gibt_nicht_frei(seeded):
    """Beweist: Die Administration hat keine fachliche Freigabe (Matrix Spez. §2)."""
    adm = seeded["login"]("admin-a", "org-a")
    status, _ = adm.post(f"/unterlagen/{seeded['unterlage']}/freigabe", {"form": "freigegeben"})
    assert status == 403


def test_studierende_pflegen_keine_inhalte(seeded):
    """Beweist: Studierende können keine Lektionen anlegen (Matrix Spez. §2)."""
    stu = seeded["login"]("student-a", "org-a")
    status, _ = stu.post(f"/module/{seeded['modul']}/lektionen", {"titel": "Heimlich"})
    assert status == 403


def test_schreibende_anfrage_ohne_csrf_wird_abgewiesen(seeded):
    """Beweist: Schreibende Anfragen ohne gültiges CSRF-Token werden abgewiesen (NF-01)."""
    stu = seeded["login"]("student-a", "org-a")
    antwort = stu.c.post("/api/v1/module", json={"bezeichnung": "Ohne Token"})
    assert antwort.status_code == 403
    assert antwort.get_json()["fehler"]["code"] == "csrf_fehlt"


def test_sitzungscookie_ist_httponly(seeded):
    """Beweist: Das Sitzungscookie ist HttpOnly und SameSite=Lax gesetzt (NF-01)."""
    app = seeded["app"]
    assert app.config["SESSION_COOKIE_HTTPONLY"] is True
    assert app.config["SESSION_COOKIE_SAMESITE"] == "Lax"
