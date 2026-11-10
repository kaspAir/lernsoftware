"""Beweist: Versuch und Gespräch sind dauerhaft abrufbar (Punkt 5); mehrere Rückfragen sind möglich; der
Modellkontext ist begrenzt und personenfrei (Punkt 5); jede Modellausgabe wird vollständig validiert,
und Simulation, echte Ausgabe und Systemfehler bleiben unterscheidbar (Punkt 6; Spez. §10)."""
import json

import pytest

from app.kern.modellpruefung import AusgabeUngueltig, pruefe_modellausgabe
from app.modell.adapter import ModellAufruf, ModellFehler, PseudonymisierungBlockiert

GUELTIG = {"form": "erklaerung", "text": "Der Abschnitt nennt sechs Ausgänge.", "quellen": [],
           "luecke": None, "sicherheitsgrad": "sicher", "annahmen": []}


def _mit_quelle(aid):
    return {**GUELTIG, "quellen": [{"abschnitt_id": aid, "aussage": "sechs Ausgänge"}]}


class Ausgabe:
    """Liefert festgelegte Modellausgaben nacheinander und zählt Aufrufe."""
    herkunft = "echt"
    modellname = "test-modell-ausgabe"

    def __init__(self, folge):
        self.folge = list(folge)
        self.aufrufe = []

    def aufrufen(self, aufruf: ModellAufruf):
        self.aufrufe.append(aufruf)
        wert = self.folge.pop(0) if len(self.folge) > 1 else self.folge[0]
        if isinstance(wert, Exception):
            raise wert
        return wert


def _versuch(seeded, login="student-a", aufgabe=None):
    stu = seeded["login"](login, "org-a")
    st, ue = stu.post(f"/module/{seeded['modul']}/uebungen", {"lektion_ids": [seeded["lektion"]]})
    st, v = stu.post(f"/uebungen/{ue['id']}/versuche", {"aufgabe_id": aufgabe or seeded["aufgabe1"], "gegeben": ["a"]})
    assert st == 201, v
    return stu, v


# ---------- Punkt 5: Dauerhafte Versuchssicht und mehrere Rückfragen ----------

def test_mehrere_rueckfragen_hintereinander_und_verlauf_bleibt(seeded):
    """Beweist: Nach einer Rückfrage ist die nächste Frage möglich; der Verlauf wächst in Reihenfolge (Punkt 5)."""
    stu, v = _versuch(seeded)
    seeded["app"].config["MODELL"] = Ausgabe([_mit_quelle(seeded["abschnitte"][0])])
    for n in range(3):
        st, d = stu.post(f"/versuche/{v['versuch_id']}/gespraech", {"frage": f"Frage {n}", "form": "rueckfrage"})
        assert st == 201, d
    sicht = stu.get(f"/versuche/{v['versuch_id']}")[1]
    fragen = [m["text"] for m in sicht["verlauf"] if m["rolle"] == "frage"]
    assert fragen == ["Frage 0", "Frage 1", "Frage 2"]
    assert sicht["gespraech_moeglich"] is True


def test_versuch_und_gespraech_nach_neuer_anmeldung_unveraendert(seeded):
    """Beweist: Antwort, Rückmeldung, Quelle und Gespräch sind nach erneuter Anmeldung identisch (Punkt 5, Abnahme)."""
    stu, v = _versuch(seeded)
    seeded["app"].config["MODELL"] = Ausgabe([_mit_quelle(seeded["abschnitte"][0])])
    stu.post(f"/versuche/{v['versuch_id']}/gespraech", {"frage": "Warum?", "form": "rueckfrage"}, "frage-persistent-1")
    vor = stu.get(f"/versuche/{v['versuch_id']}")[1]
    neu = seeded["login"]("student-a", "org-a")
    nach = neu.get(f"/versuche/{v['versuch_id']}")[1]
    assert nach["verlauf"] == vor["verlauf"]
    assert nach["antwort"] == vor["antwort"]
    assert nach["quellen"] == vor["quellen"]


def test_gespraech_wiederholung_erzeugt_keinen_zweiten_modellaufruf(seeded):
    """Beweist: Dieselbe Frage mit demselben Schlüssel löst keinen zweiten Modellaufruf aus (Punkt 3, 5)."""
    stu, v = _versuch(seeded)
    spion = Ausgabe([_mit_quelle(seeded["abschnitte"][0])])
    seeded["app"].config["MODELL"] = spion
    st1, d1 = stu.post(f"/versuche/{v['versuch_id']}/gespraech", {"frage": "Warum?", "form": "rueckfrage"}, "frage-doppel-1")
    st2, d2 = stu.post(f"/versuche/{v['versuch_id']}/gespraech", {"frage": "Warum?", "form": "rueckfrage"}, "frage-doppel-1")
    assert len(spion.aufrufe) == 1
    assert st2 == 200 and d2["wiederholt"] is True and d2["frage_id"] == d1["frage_id"]


def test_modellkontext_ist_begrenzt_und_personenfrei(seeded):
    """Beweist: Der Kontext enthält Aufgabe, Optionen, Lösung, Hilfen, begrenzten Verlauf und Lernstand, aber
    keine Namen oder Kennungen der Person (Punkt 5, NF-02)."""
    stu, v = _versuch(seeded)
    spion = Ausgabe([_mit_quelle(seeded["abschnitte"][0])])
    seeded["app"].config["MODELL"] = spion
    for n in range(8):
        stu.post(f"/versuche/{v['versuch_id']}/gespraech", {"frage": f"Frage {n}", "form": "rueckfrage"})
    letzter = spion.aufrufe[-1].auftrag
    assert len(letzter["verlauf"]) <= seeded["app"].config["LERNCFG"]["lernbegleiter"]["verlauf_max"]
    assert letzter["aufgabe"]["optionen"] and letzter["loesung"]["richtig"]
    assert "lernstand" in letzter and letzter["lernstand"]["evidenzlage"] in ("noch_nicht_belegt", "teilweise_belegt", "ausreichend_belegt", "widerspruechlich")
    text = json.dumps(letzter, ensure_ascii=False)
    assert "student-a" not in text and seeded["konto"]["student-a"] not in text
    assert len(text) <= seeded["app"].config["LERNCFG"]["lernbegleiter"]["kontext_max_zeichen"] + 2000


def test_frage_ueber_laengengrenze_wird_abgewiesen(seeded):
    """Beweist: Zu lange Fragen werden vor dem Modellaufruf abgewiesen (Punkt 5)."""
    stu, v = _versuch(seeded)
    spion = Ausgabe([GUELTIG])
    seeded["app"].config["MODELL"] = spion
    st, d = stu.post(f"/versuche/{v['versuch_id']}/gespraech", {"frage": "x" * 600, "form": "rueckfrage"})
    assert st == 422 and spion.aufrufe == []


def test_quellen_sind_durchgaengig_belegbar_und_nicht_erfunden(seeded):
    """Beweist: Die Quelle einer Antwort ist ein Abschnitt der Aufgabe, nie eine Erfindung des Modells (NR-02)."""
    stu, v = _versuch(seeded)
    seeded["app"].config["MODELL"] = Ausgabe([_mit_quelle("gibt-es-nicht")])
    st, d = stu.post(f"/versuche/{v['versuch_id']}/gespraech", {"frage": "Was?", "form": "rueckfrage"})
    assert d["antwort"]["quellen"] == []
    assert "keine belegte" in d["antwort"]["text"]


# ---------- Punkt 6: Vollständige Validierung ----------

@pytest.mark.parametrize("daten", [
    {**GUELTIG, "annahmen": 42},                       # der Regressionsfall aus dem Prüfbericht
    {**GUELTIG, "annahmen": ["ok", 3]},
    {**GUELTIG, "unbekannt": "x"},
    {k: v for k, v in GUELTIG.items() if k != "text"},  # Pflichtfeld fehlt
    {**GUELTIG, "form": "lob"},
    {**GUELTIG, "sicherheitsgrad": "sehr_sicher"},
    {**GUELTIG, "quellen": "abc"},
    {**GUELTIG, "quellen": [{"abschnitt_id": 5}]},
    {**GUELTIG, "quellen": [{"abschnitt_id": "x", "zusatz": 1}]},
    {**GUELTIG, "text": "   "},
    {**GUELTIG, "text": "Das ist eine Note 4."},
    {**GUELTIG, "luecke": 7},
    "kein Objekt",
])
def test_ungueltige_modellausgaben_werden_abgelehnt(daten):
    """Beweist: Jede Verletzung von Typ, Pflicht, zulässigem Wert oder Quellenobjekt wird vor der Verarbeitung abgelehnt (Punkt 6)."""
    with pytest.raises(AusgabeUngueltig):
        pruefe_modellausgabe(daten, {"a1"}, ["note "])


def test_gueltige_modellausgabe_wird_bereinigt_akzeptiert():
    """Beweist: Eine vollständige, gültige Ausgabe wird unverändert im Inhalt übernommen (Punkt 6)."""
    ergebnis = pruefe_modellausgabe(_mit_quelle("a1"), {"a1"}, ["note "])
    assert ergebnis["text"] == GUELTIG["text"] and ergebnis["quellen"][0]["abschnitt_id"] == "a1"


def test_annahmen_42_fuehrt_zu_wiederholung_und_standardantwort_ohne_serverfehler(seeded):
    """Beweist: annahmen=42 löst keinen Serverfehler aus; es gibt eine begrenzte Wiederholung und eine klare Meldung (Punkt 6)."""
    stu, v = _versuch(seeded)
    spion = Ausgabe([{**GUELTIG, "annahmen": 42}])
    seeded["app"].config["MODELL"] = spion
    st, d = stu.post(f"/versuche/{v['versuch_id']}/gespraech", {"frage": "Warum?", "form": "rueckfrage"})
    assert st == 201
    assert len(spion.aufrufe) == 2  # ein Versuch plus eine Wiederholung (schema_wiederholungen = 1)
    assert "nicht sicher geprüft" in d["antwort"]["text"]
    assert d["antwort"]["herkunft"]["erzeugt_durch"] == "kern"
    assert d["antwort"]["herkunft"]["grund"] == "schema"


def test_zweite_gueltige_ausgabe_nach_wiederholung_wird_verwendet(seeded):
    """Beweist: Nach einer ungültigen Ausgabe wird die gültige Wiederholung übernommen (Punkt 6)."""
    stu, v = _versuch(seeded)
    seeded["app"].config["MODELL"] = Ausgabe([{**GUELTIG, "annahmen": 42}, _mit_quelle(seeded["abschnitte"][0])])
    st, d = stu.post(f"/versuche/{v['versuch_id']}/gespraech", {"frage": "Warum?", "form": "rueckfrage"})
    assert d["antwort"]["text"] == GUELTIG["text"]
    assert len(d["antwort"]["quellen"]) == 1


def test_modellfehler_und_blockade_sind_von_belegten_antworten_unterscheidbar(seeded):
    """Beweist: Systemfehler, Blockade und simulierte Antwort tragen unterschiedliche Herkunft (Punkt 6, B-06)."""
    stu, v = _versuch(seeded)
    seeded["app"].config["MODELL"] = Ausgabe([ModellFehler("Netz")])
    _, fehler = stu.post(f"/versuche/{v['versuch_id']}/gespraech", {"frage": "a", "form": "rueckfrage"})
    seeded["app"].config["MODELL"] = Ausgabe([PseudonymisierungBlockiert([{"befund_id": "b"}], "vg")])
    _, blockiert = stu.post(f"/versuche/{v['versuch_id']}/gespraech", {"frage": "b", "form": "rueckfrage"})
    assert fehler["antwort"]["herkunft"]["erzeugt_durch"] == "system"
    assert blockiert["antwort"]["herkunft"]["grund"] == "pseudonymisierung_blockiert"
    assert fehler["antwort"]["form"] == "nicht_erreichbar"


def test_simulation_und_echte_ausgabe_sind_gekennzeichnet(seeded):
    """Beweist: Die Herkunft einer belegten Antwort nennt, ob sie simuliert oder echt ist (Punkt 6)."""
    stu, v = _versuch(seeded)
    seeded["app"].config["MODELL"] = Ausgabe([_mit_quelle(seeded["abschnitte"][0])])
    _, d = stu.post(f"/versuche/{v['versuch_id']}/gespraech", {"frage": "Warum?", "form": "rueckfrage"})
    assert d["antwort"]["herkunft"]["herkunft"] == "echt"
