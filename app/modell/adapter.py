"""Modellzugang: einzige Stelle mit Anbieterkontakt im Projekt (RA-09, NR-03, ADR-L-005).

Der Adapter spricht ausschliesslich den Vorschaltdienst (Pseudonymisierung) über seine
Basis-URL an. Der Vorschaltdienst kennt die Anbieter-API (feldgleich, siehe
C:\\Projekte\\Pseudonymisierung\\docs\\API.md). Fehlerfälle werden nicht geschluckt
(ANBINDUNG.md §6.2): 409 und 502 werden als eigene Ausnahmen weitergereicht.

Beweist: Ein 409 des Vorschaltdienstes führt zu PseudonymisierungBlockiert und nicht zu
einer stillen Ersatzantwort; die drei Pflicht-Kopfzeilen werden bei jedem Aufruf gesetzt.
"""
from __future__ import annotations

import json
from typing import Protocol

import requests


class ModellFehler(Exception):
    """Allgemeiner Modellfehler (nicht erreichbar, Zeitüberschreitung, Schema)."""


class ModellNichtKonfiguriert(ModellFehler):
    """Kein Modellzugang eingerichtet (fehlende Basis-URL, Schlüssel nicht hinterlegt)."""


class PseudonymisierungBlockiert(ModellFehler):
    """409 des Vorschaltdienstes: Eine Fundstelle braucht eine Entscheidung. Nichts wurde gesendet."""

    def __init__(self, befunde: list, vorgang_id: str | None = None):
        super().__init__("Pseudonymisierung blockiert: Entscheidung nötig.")
        self.befunde = befunde
        self.vorgang_id = vorgang_id


class RueckersetzungUnvollstaendig(ModellFehler):
    """502 des Vorschaltdienstes: Antwort wurde nicht ausgeliefert (Leckverdacht)."""


class ModellAufruf:
    """Eingabe eines Lernbegleiter-Aufrufs. Enthält nur pseudonymisierte, abschnittsbezogene Daten."""

    def __init__(self, auftrag: dict, mandant: str, sitzung: str):
        self.auftrag = auftrag
        self.mandant = mandant
        self.sitzung = sitzung


class ModellAdapter(Protocol):
    herkunft: str  # "echt" oder "SIMULIERT"
    modellname: str

    def aufrufen(self, aufruf: ModellAufruf) -> dict: ...


SYSTEM_ANWEISUNG = (
    "Du bist ein formativer Lernbegleiter. Antworte ausschliesslich als JSON-Objekt mit den Feldern "
    "form, text, quellen (Liste mit abschnitt_id und aussage), luecke (Text oder null), "
    "sicherheitsgrad (sicher|wahrscheinlich|unbestaetigt), annahmen (Liste). "
    "Verwende nur die übergebenen Abschnitte als Quelle. Vergib keine Noten. "
    "Wenn die Abschnitte die Frage nicht belegen, setze luecke und quellen leer."
)


class VorschaltdienstAdapter:
    """Spricht den Vorschaltdienst über die Anbieter-kompatible Schnittstelle an."""

    herkunft = "echt"

    def __init__(self, basis_url: str, modellname: str, anwendung: str,
                 timeout: float = 20.0, http_post=requests.post):
        if not basis_url:
            raise ModellNichtKonfiguriert("Keine Basis-URL des Vorschaltdienstes konfiguriert.")
        self.basis_url = basis_url.rstrip("/")
        self.modellname = modellname
        self.anwendung = anwendung
        self.timeout = timeout
        self._post = http_post

    def aufrufen(self, aufruf: ModellAufruf) -> dict:
        rumpf = {
            "model": self.modellname,
            "max_tokens": 800,
            "system": SYSTEM_ANWEISUNG,
            "messages": [{"role": "user", "content": json.dumps(aufruf.auftrag, ensure_ascii=False)}],
        }
        kopf = {
            "content-type": "application/json",
            "X-Pseudo-Anwendung": self.anwendung,
            "X-Pseudo-Mandant": aufruf.mandant,
            "X-Pseudo-Projekt": aufruf.sitzung,
        }
        try:
            antwort = self._post(f"{self.basis_url}/v1/messages", json=rumpf, headers=kopf, timeout=self.timeout)
        except requests.RequestException as exc:
            raise ModellFehler(f"Vorschaltdienst nicht erreichbar: {exc.__class__.__name__}") from exc

        if antwort.status_code == 409:
            daten = _json_sicher(antwort)
            pseudo = (daten.get("error") or {}).get("pseudo") or {}
            raise PseudonymisierungBlockiert(pseudo.get("befunde", []), pseudo.get("vorgang_id"))
        if antwort.status_code == 502:
            raise RueckersetzungUnvollstaendig("Rückersetzung unvollständig; Antwort nicht ausgeliefert.")
        if antwort.status_code == 503:
            raise ModellNichtKonfiguriert("Für diese Anwendung ist kein Anbieterschlüssel hinterlegt.")
        if antwort.status_code != 200:
            raise ModellFehler(f"Vorschaltdienst lieferte Status {antwort.status_code}.")

        daten = _json_sicher(antwort)
        try:
            text = daten["content"][0]["text"]
            return json.loads(text)
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise ModellFehler("Modellantwort ist kein gültiges Schema-JSON.") from exc


def _json_sicher(antwort) -> dict:
    try:
        wert = antwort.json()
        return wert if isinstance(wert, dict) else {}
    except ValueError:
        return {}
