"""Beweist: Der echte Vorschaltdienst (Pseudonymisierung, 127.0.0.1:8040) ist erreichbar und liefert
seinen Gesundheitsstatus. Dieser Test läuft nur mit VORSCHALT_LIVE=1, damit die Testläufe ohne den
Dienst reproduzierbar bleiben. Ohne Dienst wird er als «nicht geprüft» protokolliert (Testkonzept).

Ein echter Modelllauf (Anthropic über den Dienst) wird hier bewusst NICHT ausgeführt: Er würde
Daten an einen Anbieter im Ausland senden, und der Verarbeitungsort ist nicht geklärt (D-05, D-07).
"""
import os

import pytest
import requests

BASIS = os.environ.get("VORSCHALT_BASIS", "http://127.0.0.1:8040")

live = pytest.mark.live


@live
def test_vorschaltdienst_gesundheit_erreichbar():
    """Beweist: Der Vorschaltdienst meldet «bereit» auf dem Health-Endpunkt (D-05, API.md §3)."""
    if os.environ.get("VORSCHALT_LIVE") != "1":
        pytest.skip("VORSCHALT_LIVE != 1: Live-Test nicht ausgeführt (als nicht geprüft protokolliert)")
    try:
        antwort = requests.get(f"{BASIS}/pseudo/v1/health", timeout=5)
    except requests.RequestException as exc:
        pytest.fail(f"Vorschaltdienst nicht erreichbar: {exc.__class__.__name__}")
    assert antwort.status_code == 200
    daten = antwort.json()
    assert daten["status"] == "bereit"
    assert daten["wortliste_fehlt"] is False
