"""Evidenzlage je Lernziel (Spez. §6.1, §6.2; LE-04; D-13).

Trennung: Dies ist die Kompetenzeinschätzung. Sie teilt keine Felder mit der Wiederholungsplanung.
Beweist: Hilfen zählen nie als selbstständige Leistung; mehrere richtige Antworten auf dieselbe
Aufgabe zählen einmal.
"""
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Versuchseingang:
    aufgabe_id: str
    punkte_voll: bool          # volle Punkte erreicht
    hilfe_vorher: bool         # mindestens eine Hilfe vor der Antwort
    zeitpunkt: datetime


def evidenzlage(versuche: list[Versuchseingang], schwelle: int, widerspruch_nach: int) -> dict:
    """Liefert Evidenzlage und Zählwerte für ein Lernziel.

    Reihenfolge: `versuche` ist chronologisch zu übergeben.
    """
    sortiert = sorted(versuche, key=lambda v: v.zeitpunkt)
    selbststaendig = {v.aufgabe_id for v in sortiert if v.punkte_voll and not v.hilfe_vorher}
    mit_hilfe = {v.aufgabe_id for v in sortiert if v.punkte_voll and v.hilfe_vorher}
    anzahl = len(selbststaendig)
    letzte_evidenz = None
    for v in sortiert:
        if v.punkte_voll and not v.hilfe_vorher:
            letzte_evidenz = v.zeitpunkt

    if anzahl == 0:
        lage = "noch_nicht_belegt"
    elif anzahl < schwelle:
        lage = "teilweise_belegt"
    else:
        lage = "ausreichend_belegt"

    # Widerspruch: zuletzt mehrere Fehlversuche nach ausreichender Evidenz (Spez. §6.2)
    letzte = sortiert[-widerspruch_nach:] if widerspruch_nach > 0 else []
    if lage == "ausreichend_belegt" and len(letzte) == widerspruch_nach and all(not v.punkte_voll for v in letzte):
        lage = "widerspruechlich"

    return {
        "evidenzlage": lage,
        "selbststaendig_aufgaben": anzahl,
        "mit_hilfe_aufgaben": len(mit_hilfe - selbststaendig),
        "schwelle": schwelle,
        "letzte_evidenz_am": letzte_evidenz.isoformat() if letzte_evidenz else None,
    }
