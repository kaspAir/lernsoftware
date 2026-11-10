"""Beweist: Der deterministische Kern rechnet Punkte, Evidenz, Wiederholung und Abschnitte korrekt
(Spez. §6, §7; PR-05; LE-04; LE-03; IN-04)."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.kern import abschnitte, bewertung, evidenz, wiederholung

NORM = {"kleinschreibung": True, "leerraum_zusammenfassen": True, "umlaute_vergleich": True}
CFG_WDH = {"min_ease": 1.3, "max_intervall_tage": 365}


def test_single_choice_voll_oder_null():
    """Beweist: Single Choice gibt volle Punkte nur bei der richtigen Option (PR-05)."""
    assert bewertung.werte_aus("single_choice", ["b"], ["b"], Decimal("2"), NORM)["punkte"] == Decimal("2.00")
    assert bewertung.werte_aus("single_choice", ["a"], ["b"], Decimal("2"), NORM)["punkte"] == Decimal("0.00")


@pytest.mark.parametrize("gegeben,erwartet", [
    (["a", "b"], Decimal("2.00")),          # beide richtig
    (["a"], Decimal("1.00")),               # halb
    (["a", "c"], Decimal("0.00")),          # richtig und falsch: 1-1 = 0
    (["c"], Decimal("0.00")),               # nur falsch, nie negativ
    (["a", "b", "c"], Decimal("1.00")),     # 2 richtig - 1 falsch = 1 von 2
])
def test_multiple_choice_teilpunkte_nie_negativ_nie_ueber_maximum(gegeben, erwartet):
    """Beweist: Teilpunkte bleiben im Bereich 0 bis max_punkte (PR-05)."""
    erg = bewertung.werte_aus("multiple_choice", gegeben, ["a", "b"], Decimal("2"), NORM)
    assert erg["punkte"] == erwartet
    assert Decimal("0") <= erg["punkte"] <= Decimal("2")


def test_luecke_normalisiert_ohne_bedeutungsaenderung():
    """Beweist: Lückentext vergleicht normalisiert (Schreibung, Leerraum), ohne Synonyme zu akzeptieren."""
    assert bewertung.werte_aus("luecke", "  Gerade  Zahl ", ["gerade zahl"], Decimal("1"), NORM)["richtig"]
    assert not bewertung.werte_aus("luecke", "ungerade", ["gerade zahl"], Decimal("1"), NORM)["richtig"]


def test_prozent_konsistent_und_null_maximum():
    """Beweist: Prozent wird auf ganze Prozent gerundet; bei Maximum 0 entsteht keine Quote."""
    assert bewertung.prozent(Decimal("1"), Decimal("3")) == 33
    assert bewertung.prozent(Decimal("2"), Decimal("3")) == 67
    assert bewertung.prozent(Decimal("0"), Decimal("0")) is None


def _v(aid, voll, hilfe, tag):
    return evidenz.Versuchseingang(aufgabe_id=aid, punkte_voll=voll, hilfe_vorher=hilfe,
                                   zeitpunkt=datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(days=tag))


def test_hilfe_zaehlt_nicht_als_selbststaendig():
    """Beweist: Richtige Antwort nach Hilfe ist keine selbstständige Leistung (PR-04, LE-04)."""
    lage = evidenz.evidenzlage([_v("a1", True, True, 0)], 3, 2)
    assert lage["evidenzlage"] == "noch_nicht_belegt"
    assert lage["mit_hilfe_aufgaben"] == 1


def test_mehrere_richtige_auf_dieselbe_aufgabe_zaehlen_einmal():
    """Beweist: Evidenz zählt verschiedene Aufgaben, nicht wiederholte Treffer (Spez. §6.1)."""
    lage = evidenz.evidenzlage([_v("a1", True, False, 0), _v("a1", True, False, 1), _v("a1", True, False, 2)], 3, 2)
    assert lage["selbststaendig_aufgaben"] == 1
    assert lage["evidenzlage"] == "teilweise_belegt"


def test_ausreichend_erst_ab_schwelle_und_widerspruch():
    """Beweist: Drei verschiedene selbstständige Aufgaben belegen; zwei Fehler danach widersprechen."""
    basis = [_v(f"a{i}", True, False, i) for i in range(3)]
    assert evidenz.evidenzlage(basis, 3, 2)["evidenzlage"] == "ausreichend_belegt"
    mit_fehlern = basis + [_v("a9", False, False, 5), _v("a8", False, False, 6)]
    assert evidenz.evidenzlage(mit_fehlern, 3, 2)["evidenzlage"] == "widerspruechlich"


def test_sm2_referenzwerte():
    """Beweist: SM-2 folgt der Spezifikation §6.3 (Intervalle 1, 6, dann Faktor; Reset bei q<3)."""
    z = wiederholung.Wiederholungszustand.start(2.5)
    z = wiederholung.naechster_zustand(z, 4, CFG_WDH)
    assert (z.intervall_tage, z.wiederholungen) == (1, 1)
    z = wiederholung.naechster_zustand(z, 4, CFG_WDH)
    assert (z.intervall_tage, z.wiederholungen) == (6, 2)
    z = wiederholung.naechster_zustand(z, 4, CFG_WDH)
    assert z.intervall_tage == 15  # 6 Tage × Faktor 2,5 (q=4 lässt den Faktor unverändert)


def test_sm2_falsch_setzt_zurueck_und_ease_untergrenze():
    """Beweist: Falsche Antwort beginnt das Intervall neu; der Faktor fällt nie unter 1,3."""
    z = wiederholung.Wiederholungszustand(ease=1.4, intervall_tage=30, wiederholungen=5)
    neu = wiederholung.naechster_zustand(z, 1, CFG_WDH)
    assert (neu.intervall_tage, neu.wiederholungen) == (1, 0)
    for _ in range(10):
        neu = wiederholung.naechster_zustand(neu, 0, CFG_WDH)
    assert neu.ease >= 1.3


def test_sm2_intervall_obergrenze():
    """Beweist: Das Intervall überschreitet die Obergrenze nicht."""
    z = wiederholung.Wiederholungszustand(ease=2.5, intervall_tage=300, wiederholungen=5)
    assert wiederholung.naechster_zustand(z, 5, CFG_WDH).intervall_tage == 365


def test_qualitaet_mapping():
    """Beweist: Qualität folgt der Tabelle in Spez. §6.3 (Hilfe, Selbsteinschätzung)."""
    assert wiederholung.qualitaet(False, False, "sicher") == 1
    assert wiederholung.qualitaet(True, True, "sicher") == 3
    assert wiederholung.qualitaet(True, False, "unsicher") == 3
    assert wiederholung.qualitaet(True, False, None) == 4
    assert wiederholung.qualitaet(True, False, "sicher") == 5


def test_abschnitte_lueckenlos_und_begrenzt():
    """Beweist: Abschnitte decken den Text ab und überschreiten die Höchstlänge nicht (IN-04)."""
    text = ("Satz eins ist hier. " * 200).strip()
    teile = abschnitte.segmentiere(text, 300, 1200)
    assert all(len(t) <= 1200 for t in teile)
    assert "".join(teile).replace(" ", "") == text.replace(" ", "")


def test_markdown_ueberschrift_beginnt_neuen_abschnitt():
    """Beweist: Überschriften trennen Abschnitte (Quellen bleiben lokalisierbar)."""
    text = "# A\n\n" + "a " * 200 + "\n\n## B\n\n" + "b " * 200
    teile = abschnitte.segmentiere(text, 100, 1200)
    assert any(t.startswith("## B") for t in teile)
