"""Strenge Prüfung jeder Modellausgabe, bevor sie verarbeitet wird (Inkrement 1.1, Spez. §10).

Beweist: Nur vollständige, typgerechte und zulässige Ausgaben werden angenommen. Unbekannte Felder,
falsche Typen, Zahlen als Annahmen, nicht erlaubte Quellen und Bewertungssprache führen zur
Ablehnung mit Grund; die aufrufende Stelle erhält so einen Fehler statt eines Serverabsturzes.
"""
from ..fehler import FachFehler  # noqa: F401  (Einheitlicher Fehlertyp für Aufrufer)

FORMEN = ("hinweis", "rueckfrage", "beispiel", "erklaerung")
SICHERHEIT = ("sicher", "wahrscheinlich", "unbestaetigt")
PFLICHT = ("form", "text", "quellen", "sicherheitsgrad", "annahmen")
ERLAUBT = set(PFLICHT) | {"luecke"}
MAX_QUELLEN = 5
MAX_ANNAHMEN = 5


class AusgabeUngueltig(Exception):
    def __init__(self, grund: str, kennung: str):
        super().__init__(grund)
        self.grund = grund
        self.kennung = kennung


def pruefe_modellausgabe(daten, erlaubte_abschnitte: set[str], verboten: list[str]) -> dict:
    if not isinstance(daten, dict):
        raise AusgabeUngueltig("Ausgabe ist kein Objekt.", "schema")
    unbekannt = set(daten) - ERLAUBT
    if unbekannt:
        raise AusgabeUngueltig(f"Unbekannte Felder: {sorted(unbekannt)}", "schema")
    fehlend = [f for f in PFLICHT if f not in daten]
    if fehlend:
        raise AusgabeUngueltig(f"Pflichtfelder fehlen: {fehlend}", "schema")

    if daten["form"] not in FORMEN:
        raise AusgabeUngueltig("Unzulässige Form.", "schema")
    text = daten["text"]
    if not isinstance(text, str) or not (1 <= len(text.strip()) <= 1500):
        raise AusgabeUngueltig("Text fehlt oder ist zu lang.", "schema")

    quellen = daten["quellen"]
    if not isinstance(quellen, list) or len(quellen) > MAX_QUELLEN:
        raise AusgabeUngueltig("Quellen müssen eine Liste mit höchstens 5 Einträgen sein.", "schema")
    saubere_quellen = []
    for q in quellen:
        if not isinstance(q, dict) or set(q) - {"abschnitt_id", "aussage"}:
            raise AusgabeUngueltig("Quellenobjekt hat ungültige Felder.", "schema")
        aid = q.get("abschnitt_id")
        if not isinstance(aid, str):
            raise AusgabeUngueltig("abschnitt_id fehlt oder ist kein Text.", "schema")
        if aid not in erlaubte_abschnitte:
            raise AusgabeUngueltig("Quelle außerhalb der übergebenen Abschnitte.", "quelle")
        aussage = q.get("aussage", "")
        if not isinstance(aussage, str) or len(aussage) > 300:
            raise AusgabeUngueltig("Aussage zur Quelle ist ungültig.", "schema")
        saubere_quellen.append({"abschnitt_id": aid, "aussage": aussage})

    if daten["sicherheitsgrad"] not in SICHERHEIT:
        raise AusgabeUngueltig("Unzulässiger Sicherheitsgrad.", "schema")

    annahmen = daten["annahmen"]
    if not isinstance(annahmen, list) or len(annahmen) > MAX_ANNAHMEN or \
            not all(isinstance(a, str) and len(a) <= 200 for a in annahmen):
        raise AusgabeUngueltig("Annahmen müssen eine Liste von Texten sein.", "schema")

    luecke = daten.get("luecke")
    if luecke is not None and (not isinstance(luecke, str) or len(luecke) > 300):
        raise AusgabeUngueltig("Lücke muss Text oder null sein.", "schema")

    treffer = [m for m in verboten if m.lower() in text.lower()]
    if treffer:
        raise AusgabeUngueltig("Bewertungssprache in der Ausgabe.", "bewertung")

    return {"form": daten["form"], "text": text.strip(), "quellen": saubere_quellen,
            "sicherheitsgrad": daten["sicherheitsgrad"], "annahmen": list(annahmen), "luecke": luecke}
