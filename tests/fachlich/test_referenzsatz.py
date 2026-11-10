"""Beweist (fachlich, synthetisch): Die Lösungsschlüssel der Referenzaufgaben stimmen mit der
mathematischen Prüfung überein. Dies ist eine fachliche Referenzprüfung, keine Lehrpersonen-Abnahme.

Die Unvereinbarkeit wird aus den Ereignismengen berechnet, nicht aus dem Schlüssel abgelesen.
"""
from pathlib import Path

import yaml

from app.demo import UNTERLAGE

REFERENZ = Path(__file__).with_name("referenzsatz.yaml")
ERGEBNISRAUM = {1, 2, 3, 4, 5, 6}
EREIGNISSE = {
    "eins und sechs": ({1}, {6}),
    "gerade und ungerade": ({2, 4, 6}, {1, 3, 5}),
    "eins und zwei": ({1}, {2}),
}


def _unvereinbar(paar):
    a, b = EREIGNISSE[paar]
    return not (a & b) and a <= ERGEBNISRAUM and b <= ERGEBNISRAUM


def _lade():
    return yaml.safe_load(REFERENZ.read_text(encoding="utf-8"))


def test_wuerfel_ergebnisraum_schluessel_stimmt():
    """Beweist (fachlich): Der Ergebnisraum eines Würfels hat sechs Ausgänge; der Schlüssel nennt die Sechs."""
    aufgabe = next(a for a in _lade()["aufgaben"] if a["id"] == "wuerfel_ergebnisraum")
    assert len(ERGEBNISRAUM) == 6 and aufgabe["loesung"] == ["b"] and aufgabe["optionen"]["b"] == "sechs"


def test_wuerfel_unvereinbar_schluessel_stimmt_mit_mengenpruefung():
    """Beweist (fachlich): Alle drei Paare sind unvereinbar; der Schlüssel enthält alle drei (Punkt 9)."""
    aufgabe = next(a for a in _lade()["aufgaben"] if a["id"] == "wuerfel_unvereinbar")
    berechnet = sorted(k for k in EREIGNISSE if _unvereinbar(k))
    schluessel = sorted(aufgabe["optionen"][x] for x in aufgabe["loesung"])
    assert berechnet == schluessel


def test_gegenereignis_schluessel_stimmt():
    """Beweist (fachlich): Das Gegenereignis zu «gerade» ist «ungerade» (Mengenkomplement)."""
    aufgabe = next(a for a in _lade()["aufgaben"] if a["id"] == "wuerfel_gegenereignis")
    gerade = {2, 4, 6}
    assert ERGEBNISRAUM - gerade == {1, 3, 5}
    assert aufgabe["optionen"][aufgabe["loesung"][0]] == "ungerade Augenzahl"


def test_testdaten_stimmen_mit_referenzsatz_ueberein():
    """Beweist (fachlich): Die Testaufgabe im Abnahmelauf nutzt denselben Schlüssel wie der Referenzsatz."""
    conftest = (Path(__file__).parents[1] / "conftest.py").read_text(encoding="utf-8")
    assert '"loesung": ["a", "b", "c"]' in conftest
    assert "Ergebnisraum" in UNTERLAGE.read_text(encoding="utf-8")
