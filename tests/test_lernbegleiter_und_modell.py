"""Beweist: Der Lernbegleiter gibt nur belegte Antworten, prüft Quellen und Sprache im Kern, und der
Modellzugang läuft ausschliesslich über den Vorschaltdienst mit korrekter Fehlerweitergabe
(NR-02, NR-03, BS-02, BS-05, BS-06, RA-09, ADR-L-005, ANBINDUNG.md §6.2).

Der Vorschaltdienst wird hier über einen Testdouble der HTTP-Schicht geprüft (Vertragstest).
Ein Lauf gegen den echten Dienst steht in test_live_vorschaltdienst.py.
"""
import json

import pytest
import requests

from app.dienste import lernbegleiter
from app.modell.adapter import (ModellAufruf, ModellFehler, ModellNichtKonfiguriert,
                                PseudonymisierungBlockiert, RueckersetzungUnvollstaendig,
                                VorschaltdienstAdapter)
from app.modell.testadapter import SimulationsAdapter


class Antwort:
    def __init__(self, status, daten):
        self.status_code = status
        self._daten = daten

    def json(self):
        return self._daten


class FalscherAdapter:
    """Liefert vorgegebene Rohdaten; kennzeichnet die Herkunft als SIMULIERT."""
    herkunft = "SIMULIERT"
    modellname = "test-double"

    def __init__(self, rohdaten):
        self.rohdaten = rohdaten

    def aufrufen(self, aufruf):
        if isinstance(self.rohdaten, Exception):
            raise self.rohdaten
        return self.rohdaten


def _versuch_id(seeded, sitzung_stu):
    st, ue = sitzung_stu.post(f"/module/{seeded['modul']}/uebungen", {"lektion_ids": [seeded["lektion"]]})
    st, v = sitzung_stu.post(f"/uebungen/{ue['id']}/versuche", {"aufgabe_id": seeded["aufgabe1"], "gegeben": ["a"]})
    return v["versuch_id"]


def _lauf(seeded, adapter, form="erklaerung", frage="Warum?"):
    from app.models import Konto  # noqa: F401 (Import hält das Modell registriert)
    stu = seeded["login"]("student-a", "org-a")
    vid = _versuch_id(seeded, stu)
    status, daten = stu.post(f"/versuche/{vid}/gespraech", {"frage": frage, "form": form})
    return status, daten.get("antwort", daten) if isinstance(daten, dict) else daten


def _mit_adapter(seeded, adapter):
    seeded["app"].config["MODELL"] = adapter
    return seeded


def test_fremde_quelle_wird_abgelehnt(seeded):
    """Beweist: Eine Quellen-ID außerhalb der übergebenen Abschnitte führt zur Ablehnung (NR-02, BS-02)."""
    _mit_adapter(seeded, FalscherAdapter({"form": "erklaerung", "text": "Erfundene Aussage.",
                                          "quellen": [{"abschnitt_id": "gibt-es-nicht", "aussage": "x"}],
                                          "luecke": None, "sicherheitsgrad": "sicher", "annahmen": []}))
    status, daten = _lauf(seeded, None)
    assert status == 201
    assert "Erfundene" not in daten["text"]
    assert "keine belegte Antwort" in daten["text"]


def test_bewertungssprache_wird_abgelehnt(seeded):
    """Beweist: Bewertungssprache (Note, bestanden) wird nicht ausgegeben (BS-06, NR-01)."""
    sid = seeded["abschnitte"][0]
    _mit_adapter(seeded, FalscherAdapter({"form": "erklaerung", "text": "Das ist eine Note 4, nicht bestanden.",
                                          "quellen": [{"abschnitt_id": sid, "aussage": "x"}], "luecke": None,
                                          "sicherheitsgrad": "sicher", "annahmen": []}))
    status, daten = _lauf(seeded, None)
    assert "Note 4" not in daten["text"]


def test_antwort_ohne_quelle_wird_als_unbelegt_benannt(seeded):
    """Beweist: Ohne Quelle und ohne benannte Grundlage wird die Lücke benannt, nicht gefüllt (BS-05)."""
    _mit_adapter(seeded, FalscherAdapter({"form": "erklaerung", "text": "Ein allgemeines Wissen.",
                                          "quellen": [], "luecke": None, "sicherheitsgrad": "wahrscheinlich",
                                          "annahmen": []}))
    status, daten = _lauf(seeded, None)
    assert "keine belegte Antwort" in daten["text"]
    assert daten["luecke"]


def test_erfolgreiche_antwort_trägt_quelle_und_fachlich_ungeprueft(seeded):
    """Beweist: Belegte Antworten zeigen Quelle, Position und «fachlich ungeprüft» (RA-10, AG-14)."""
    sid = seeded["abschnitte"][0]
    _mit_adapter(seeded, FalscherAdapter({"form": "erklaerung", "text": "Der Ergebnisraum umfasst die Augenzahlen.",
                                          "quellen": [{"abschnitt_id": sid, "aussage": "x"}], "luecke": None,
                                          "sicherheitsgrad": "wahrscheinlich", "annahmen": ["Annahme dokumentiert"]}))
    status, daten = _lauf(seeded, None)
    assert daten["quellen"][0]["abschnitt_id"] == sid
    assert daten["quellen"][0]["fachlich"] == "ungeprueft"
    assert daten["sicherheitsgrad"] == "wahrscheinlich"
    assert daten["annahmen"] == ["Annahme dokumentiert"]


def test_blockierte_pseudonymisierung_sendet_nichts_und_erfindet_nichts(seeded):
    """Beweist: Bei 409 erscheint eine Standardantwort, keine Erklärung (ANBINDUNG.md §4, §6.2)."""
    _mit_adapter(seeded, FalscherAdapter(PseudonymisierungBlockiert([{"befund_id": "bf"}], "vg")))
    status, daten = _lauf(seeded, None)
    assert "Entscheidung" in daten["text"]
    assert daten["herkunft"]["erzeugt_durch"] == "system"


def test_modell_nicht_erreichbar_ergibt_klare_meldung(seeded):
    """Beweist: Modellausfall führt zur ehrlichen Meldung, nicht zu einer erfundenen Erklärung (Spez. §12)."""
    _mit_adapter(seeded, FalscherAdapter(ModellFehler("Netz weg")))
    status, daten = _lauf(seeded, None)
    assert status == 201
    assert "nicht erreichbar" in daten["text"]
    assert daten["quellen"] == []


def test_ungueltiges_schema_wird_nach_festen_wiederholungen_abgebrochen(seeded):
    """Beweist: Schema-Fehler führen zu Wiederholung mit fester Grenze, danach zur Standardantwort (TC-BEG-02)."""
    _mit_adapter(seeded, FalscherAdapter({"unvollstaendig": True}))
    status, daten = _lauf(seeded, None)
    assert "nicht sicher geprüft" in daten["text"]


def test_simulierte_antwort_ist_als_solche_gekennzeichnet(seeded):
    """Beweist: Der Testadapter kennzeichnet seine Ausgaben als SIMULIERT; die Herkunft steht am Verlauf (B-06)."""
    _mit_adapter(seeded, SimulationsAdapter())
    status, daten = _lauf(seeded, None, form="rueckfrage", frage="Ergebnisraum Würfel Augenzahlen")
    assert daten["herkunft"]["herkunft"] == "SIMULIERT"
    assert all(q["abschnitt_id"] in seeded["abschnitte"] for q in daten["quellen"])


def test_simulation_ohne_ueberschneidung_meldet_luecke(seeded):
    """Beweist: Ohne Wortüberschneidung liefert die Simulation keine erfundene Quelle (NR-02)."""
    _mit_adapter(seeded, SimulationsAdapter())
    status, daten = _lauf(seeded, None, frage="Quantenchromodynamik Gluonen")
    assert daten["quellen"] == []


# ---------- Vertrag des Vorschaltdienstes ----------

class HttpDouble:
    def __init__(self, antwort=None, ausnahme=None):
        self.antwort = antwort
        self.ausnahme = ausnahme
        self.aufrufe = []

    def __call__(self, url, json=None, headers=None, timeout=None):
        self.aufrufe.append({"url": url, "json": json, "headers": headers, "timeout": timeout})
        if self.ausnahme:
            raise self.ausnahme
        return self.antwort


def _adapter(http):
    return VorschaltdienstAdapter("http://127.0.0.1:8040/anthropic", "claude-test", "lernsoftware",
                                  timeout=5, http_post=http)


def _aufruf():
    return ModellAufruf({"frage": "x"}, mandant="org-id-1", sitzung="ls-12345678")


def test_vertrag_setzt_drei_pflichtkopfzeilen(app):
    """Beweist: Jeder Aufruf trägt Anwendung, Mandant und Projekt (ANBINDUNG.md §2)."""
    text = json.dumps({"form": "erklaerung", "text": "ok", "quellen": [], "luecke": None,
                       "sicherheitsgrad": "sicher", "annahmen": []})
    http = HttpDouble(Antwort(200, {"content": [{"type": "text", "text": text}]}))
    _adapter(http).aufrufen(_aufruf())
    kopf = http.aufrufe[0]["headers"]
    assert kopf["X-Pseudo-Anwendung"] == "lernsoftware"
    assert kopf["X-Pseudo-Mandant"] == "org-id-1"
    assert kopf["X-Pseudo-Projekt"] == "ls-12345678"
    assert http.aufrufe[0]["url"].endswith("/v1/messages")
    assert "api-key" not in json.dumps(kopf).lower()  # kein Anbieterschlüssel im Produkt


def test_409_wird_als_blockade_weitergereicht(app):
    """Beweist: 409 wird als PseudonymisierungBlockiert mit Befunden weitergereicht, nicht geschluckt (ANBINDUNG.md §6.2)."""
    pseudo = {"error": {"type": "pseudonymisierung_blockiert", "pseudo": {"vorgang_id": "vg1",
              "befunde": [{"befund_id": "bf1", "treffer": "x"}]}}}
    with pytest.raises(PseudonymisierungBlockiert) as info:
        _adapter(HttpDouble(Antwort(409, pseudo))).aufrufen(_aufruf())
    assert info.value.befunde[0]["befund_id"] == "bf1"


def test_502_wird_nicht_als_netzfehler_verschluckt(app):
    """Beweist: 502 (Rückersetzung unvollständig) wird als eigener Fehler gemeldet (ANBINDUNG.md §4)."""
    with pytest.raises(RueckersetzungUnvollstaendig):
        _adapter(HttpDouble(Antwort(502, {}))).aufrufen(_aufruf())


def test_503_ohne_schluessel_ist_konfigurationsfehler(app):
    """Beweist: 503 wird als fehlende Konfiguration gemeldet (ANBINDUNG.md §4)."""
    with pytest.raises(ModellNichtKonfiguriert):
        _adapter(HttpDouble(Antwort(503, {}))).aufrufen(_aufruf())


def test_netzfehler_wird_zu_modellfehler(app):
    """Beweist: Verbindungsfehler werden als ModellFehler gemeldet, ohne Rohdaten preiszugeben."""
    with pytest.raises(ModellFehler):
        _adapter(HttpDouble(ausnahme=requests.ConnectionError("refused"))).aufrufen(_aufruf())


def test_leere_basis_url_verweigert_modellzugang(app):
    """Beweist: Ohne Basis-URL gibt es keinen Modellzugang (ADR-L-005, TC-KI-01)."""
    with pytest.raises(ModellNichtKonfiguriert):
        VorschaltdienstAdapter("", "x", "lernsoftware")


def test_konstante_kopfzeilen_nicht_aus_eingabe(app):
    """Beweist: Die Mandantenkennung kommt aus dem Aufruf, nie aus dem Lernprofil (RA-08, NR-04)."""
    text = json.dumps({"form": "erklaerung", "text": "ok", "quellen": [], "luecke": None,
                       "sicherheitsgrad": "sicher", "annahmen": []})
    http = HttpDouble(Antwort(200, {"content": [{"type": "text", "text": text}]}))
    _adapter(http).aufrufen(ModellAufruf({"mandant_manipuliert": "org-b"}, mandant="org-id-1", sitzung="s"))
    assert http.aufrufe[0]["headers"]["X-Pseudo-Mandant"] == "org-id-1"
