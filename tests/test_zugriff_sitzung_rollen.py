"""Beweist: Gemeinsame Prüfungen für Anzeige, Hilfe, Abgabe und Modellaufrufe (Punkt 4); Sitzungsdauer
120 Minuten ab Anmeldung (Punkt 7); deaktivierte Konten und Organisationen verlieren den Zugang auch mit
bestehender Sitzung; genau eine Modulrolle je Konto und Modul (Punkt 7)."""
import re
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.models import Konto, Lernorganisation, Modulzuweisung, Nachweis
from app.sitzung import sitzung_abgelaufen


class Zaehler:
    """Modelladapter-Spion: zählt Aufrufe und hält die Eingaben fest."""
    herkunft = "SIMULIERT"
    modellname = "spion"

    def __init__(self):
        self.aufrufe = []

    def aufrufen(self, aufruf):
        self.aufrufe.append(aufruf)
        return {"form": "erklaerung", "text": "Erklärung aus dem Abschnitt.",
                "quellen": [{"abschnitt_id": aufruf.auftrag["abschnitte"][0]["id"], "aussage": "x"}]
                if aufruf.auftrag["abschnitte"] else [],
                "luecke": None, "sicherheitsgrad": "wahrscheinlich", "annahmen": []}


def _versuch(seeded, login="student-a"):
    stu = seeded["login"](login, "org-a")
    st, ue = stu.post(f"/module/{seeded['modul']}/uebungen", {"lektion_ids": [seeded["lektion"]]})
    st, v = stu.post(f"/uebungen/{ue['id']}/versuche", {"aufgabe_id": seeded["aufgabe1"], "gegeben": ["a"]})
    assert st == 201, v
    return stu, ue, v


def _spion(seeded):
    spion = Zaehler()
    seeded["app"].config["MODELL"] = spion
    return spion


# ---------- Punkt 4: Freigabe und aktuelle Verfügbarkeit ----------

def test_aenderung_wirkt_auf_bestehende_uebung_und_hilfe(seeded):
    """Beweist: Nach Unterlagenänderung ist eine bereits geöffnete Übung für neue Abgaben und Hilfen gesperrt (Punkt 4)."""
    stu, ue, _ = _versuch(seeded)
    seeded["login"]("dozent-a", "org-a").post(f"/unterlagen/{seeded['unterlage']}/aenderung",
                                             {"inhalt": "Neuer Inhalt ohne Bezug. " * 40})
    st, sicht = stu.get(f"/uebungen/{ue['id']}")
    assert st == 200
    assert all(a["verfuegbar"] is False for a in sicht["aufgaben"] if a["id"] == seeded["aufgabe1"])
    st, d = stu.post(f"/uebungen/{ue['id']}/hilfe", {"aufgabe_id": seeded["aufgabe1"], "art": "hinweis"})
    assert st == 409 and d["fehler"]["code"] == "aufgabe_nicht_verfuegbar"
    st, d = stu.post(f"/uebungen/{ue['id']}/versuche", {"aufgabe_id": seeded["aufgabe1"], "gegeben": ["b"]})
    assert st == 409


def test_historischer_versuch_bleibt_lesbar_mit_altem_stand(seeded):
    """Beweist: Der gespeicherte Versuch zeigt weiterhin Antwort, Rückmeldung und den zitierten Stand (Punkt 4, 5)."""
    stu, _, v = _versuch(seeded)
    seeded["login"]("dozent-a", "org-a").post(f"/unterlagen/{seeded['unterlage']}/aenderung",
                                             {"inhalt": "Neuer Inhalt. " * 40})
    st, sicht = stu.get(f"/versuche/{v['versuch_id']}")
    assert st == 200
    assert sicht["antwort"]["gegeben"] == ["a"]
    assert sicht["gespraech_moeglich"] is False
    quelle = sicht["quellen"][0]
    assert quelle["version_zitiert"] == 1 and quelle["version_aktuell"] == 2
    assert quelle["neu_verwendbar"] is False and quelle["text"]


def test_neue_erklaerung_wird_bei_gesperrter_quelle_nicht_erzeugt(seeded):
    """Beweist: Ohne aktuell verwendbare Quelle erfolgt kein Modellaufruf; der Verlauf bleibt erhalten (Punkt 4)."""
    stu, _, v = _versuch(seeded)
    spion = _spion(seeded)
    seeded["login"]("dozent-a", "org-a").post(f"/unterlagen/{seeded['unterlage']}/aenderung",
                                             {"inhalt": "Neuer Inhalt. " * 40})
    st, d = stu.post(f"/versuche/{v['versuch_id']}/gespraech", {"frage": "Warum?", "form": "rueckfrage"},
                     "frage-gesperrt-1")
    assert st == 201
    assert spion.aufrufe == []
    assert "keine neue Erklärung" in d["antwort"]["text"]
    assert d["frage"] == "Warum?"


def test_neue_erklaerung_bei_neuer_quellenfassung_wird_abgelehnt_historie_bleibt(seeded):
    """Beweist: Nach neuer Freigabe mit anderer Fassung ist für einen frühen Versuch keine neue Erklärung
    zulässig (der zitierte Stand ist nicht mehr aktuell); der Versuch und seine Quelle bleiben lesbar (Punkt 4, 5)."""
    stu, _, v = _versuch(seeded)
    doz = seeded["login"]("dozent-a", "org-a")
    doz.post(f"/unterlagen/{seeded['unterlage']}/aenderung", {"inhalt": "Neuer Inhalt zur Freigabe. " * 40})
    doz.post(f"/unterlagen/{seeded['unterlage']}/freigabe", {"form": "freigegeben"})
    spion = _spion(seeded)
    st, d = stu.post(f"/versuche/{v['versuch_id']}/gespraech", {"frage": "Was gilt?", "form": "erklaerung"},
                     "frage-neue-fassung")
    assert st == 201 and spion.aufrufe == []
    assert "neuere Fassung" in d["antwort"]["text"] or "keine neue Erklärung" in d["antwort"]["text"]
    sicht = stu.get(f"/versuche/{v['versuch_id']}")[1]
    assert sicht["quellen"][0]["version_zitiert"] == 1
    assert sicht["quellen"][0]["version_aktuell"] == 2


def test_abschnitt_zeigt_historischen_stand_und_aktuellen_status(seeded):
    """Beweist: Der zitierte Abschnitt ist lesbar und nennt Zitierstand, aktuellen Stand und Verwendbarkeit (Punkt 5)."""
    stu, _, v = _versuch(seeded)
    abschnitt_id = v["quellen"][0]["abschnitt_id"]
    st, a = stu.get(f"/abschnitte/{abschnitt_id}")
    assert st == 200 and a["neu_verwendbar"] is True and a["version_zitiert"] == a["version_aktuell"]
    seeded["login"]("dozent-a", "org-a").post(f"/unterlagen/{seeded['unterlage']}/aenderung",
                                             {"inhalt": "Anderer Text. " * 40})
    st, a = stu.get(f"/abschnitte/{abschnitt_id}")
    assert st == 200 and a["neu_verwendbar"] is False and a["status_aktuell"] == "in_pruefung"
    assert a["volltext_version"]


def test_entzogene_modulrolle_sperrt_begonnene_uebung(seeded, sitzung):
    """Beweist: Wird die Modulzuweisung entfernt, verliert die Person Übung, Hilfe und Abgabe, auch wenn sie angemeldet bleibt (Punkt 4)."""
    stu, ue, v = _versuch(seeded)
    zuweisung = sitzung.scalars(select(Modulzuweisung).where(
        Modulzuweisung.modul_id == seeded["modul"], Modulzuweisung.konto_id == seeded["konto"]["student-a"])).first()
    sitzung.delete(zuweisung)
    sitzung.commit()
    assert stu.get(f"/uebungen/{ue['id']}")[0] == 404
    assert stu.get(f"/versuche/{v['versuch_id']}")[0] == 404
    assert stu.post(f"/uebungen/{ue['id']}/hilfe", {"aufgabe_id": seeded["aufgabe1"], "art": "hinweis"})[0] == 404
    assert stu.post(f"/uebungen/{ue['id']}/versuche", {"aufgabe_id": seeded["aufgabe2"], "gegeben": ["a"]},
                    "abgabe-nach-entzug")[0] == 404


def test_deaktiviertes_konto_verliert_bestehende_sitzung(seeded, sitzung):
    """Beweist: Ein deaktiviertes Konto kann mit bestehender Sitzung keine geschützten Aktionen mehr ausführen (Punkt 4)."""
    stu, ue, v = _versuch(seeded)
    konto = sitzung.get(Konto, seeded["konto"]["student-a"])
    konto.status = "deaktiviert"
    sitzung.commit()
    assert stu.get(f"/module")[0] == 401
    assert stu.get(f"/versuche/{v['versuch_id']}")[0] == 401
    assert stu.post(f"/uebungen/{ue['id']}/versuche", {"aufgabe_id": seeded["aufgabe2"], "gegeben": ["a"]},
                    "abgabe-deaktiviert")[0] == 401


def test_deaktivierte_organisation_verliert_bestehende_sitzung(seeded, sitzung):
    """Beweist: Eine deaktivierte Lernorganisation sperrt alle Sitzungen ihrer Mitglieder (Punkt 4)."""
    stu, _, _ = _versuch(seeded)
    org = sitzung.get(Lernorganisation, seeded["org"])
    org.status = "deaktiviert"
    sitzung.commit()
    assert stu.get("/module")[0] == 401
    assert stu.get(f"/module/{seeded['modul']}/lernprofil")[0] == 401


def test_deaktivierter_superadmin_verliert_zugang(seeded, sitzung):
    """Beweist: Ein deaktivierter Super-Admin kann mit bestehender Sitzung das Register nicht mehr lesen (Punkt 4)."""
    sa = seeded["app"].test_client()
    sa.post("/api/v1/auth/anmelden", json={"benutzername": "plattform-test", "passwort": "Superadmin-Test-2026"})
    assert sa.get("/api/v1/superadmin/lernorganisationen").status_code == 200
    konto = sitzung.scalars(select(Konto).where(Konto.benutzername == "plattform-test")).first()
    konto.status = "deaktiviert"
    sitzung.commit()
    assert sa.get("/api/v1/superadmin/lernorganisationen").status_code == 401


# ---------- Punkt 7: Sitzungsdauer und Mehrfachrollen ----------

def test_sitzungsgrenze_ist_120_minuten_ab_anmeldung():
    """Beweist: Die Sitzung endet genau nach 120 Minuten ab Anmeldung, nicht ab letzter Aktivität (Punkt 7)."""
    start = datetime(2026, 11, 10, 12, 0, tzinfo=timezone.utc)
    assert sitzung_abgelaufen(start.isoformat(), 120, now=start + timedelta(minutes=119, seconds=59)) is False
    assert sitzung_abgelaufen(start.isoformat(), 120, now=start + timedelta(minutes=120)) is True
    assert sitzung_abgelaufen(None, 120) is True


def test_sitzung_laeuft_nach_ablauf_im_api_ab(seeded):
    """Beweist: Eine Sitzung mit überschrittener Dauer wird verworfen (401 sitzung_abgelaufen) (Punkt 7)."""
    c = seeded["app"].test_client()
    c.post("/api/v1/auth/anmelden", json={"kurzname": "org-a", "benutzername": "student-a",
                                          "passwort": "Testpasswort-2026"})
    with c.session_transaction() as s:
        s["angemeldet_am"] = (datetime.now(timezone.utc) - timedelta(minutes=121)).isoformat()
    antwort = c.get("/api/v1/module")
    assert antwort.status_code == 401 and antwort.get_json()["fehler"]["code"] == "sitzung_abgelaufen"


def test_sitzung_im_browser_laeuft_ab(seeded):
    """Beweist: Die Browser-Sitzung wird nach Ablauf verworfen und leitet zur Anmeldung (Punkt 7)."""
    c = seeded["app"].test_client()
    c.post("/anmelden", data={"kurzname": "org-a", "benutzername": "student-a", "passwort": "Testpasswort-2026"})
    with c.session_transaction() as s:
        s["angemeldet_am"] = (datetime.now(timezone.utc) - timedelta(minutes=121)).isoformat()
    antwort = c.get("/module")
    assert antwort.status_code == 302 and "anmelden" in antwort.headers["Location"]


def test_genau_eine_modulrolle_je_konto_und_modul(seeded, sitzung):
    """Beweist: Eine neue Modulzuweisung ersetzt die bisherige; es gibt nie zwei Rollen im selben Modul (Punkt 7)."""
    adm = seeded["login"]("admin-a", "org-a")
    st, _ = adm.post(f"/module/{seeded['modul']}/zuweisungen", {
        "konto_id": seeded["konto"]["student-a2"], "rolle": "studierende"})
    assert st == 201
    st, d = adm.post(f"/module/{seeded['modul']}/zuweisungen", {
        "konto_id": seeded["konto"]["student-a2"], "rolle": "dozierende"})
    assert st == 201 and d["rolle"] == "dozierende"
    zeilen = sitzung.scalars(select(Modulzuweisung).where(
        Modulzuweisung.modul_id == seeded["modul"], Modulzuweisung.konto_id == seeded["konto"]["student-a2"])).all()
    assert len(zeilen) == 1 and zeilen[0].rolle == "dozierende"
    nachweis = sitzung.scalars(select(Nachweis).where(Nachweis.art == "zuweisung",
                                                      Nachweis.objekt_id == seeded["modul"])).all()
    assert any((n.inhalt or {}).get("vorher") == {"rolle": "studierende", "freigabe_delegiert": False}
               for n in nachweis)


def test_mehrfachrolle_verliert_keine_bisherigen_rechte(seeded):
    """Beweist: Nach dem Rollenwechsel gilt die neue Rolle durchgängig; die alte Zuweisung blockiert nicht mehr (Punkt 7)."""
    adm = seeded["login"]("admin-a", "org-a")
    adm.post(f"/module/{seeded['modul']}/zuweisungen", {"konto_id": seeded["konto"]["student-a2"], "rolle": "studierende"})
    stu2 = seeded["login"]("student-a2", "org-a")
    assert stu2.get(f"/module/{seeded['modul']}/lektionen")[0] == 200
    adm.post(f"/module/{seeded['modul']}/zuweisungen", {"konto_id": seeded["konto"]["student-a2"], "rolle": "assistenz"})
    assert stu2.get(f"/module/{seeded['modul']}/lektionen")[0] == 200  # Assistenz darf lesen
    st, _ = stu2.post(f"/unterlagen/{seeded['unterlage']}/freigabe", {"form": "freigegeben"})
    assert st == 403  # Assistenz ohne Delegation
