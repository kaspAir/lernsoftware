"""Einheitliches Antwortformat (Inkrement 1.1, Dokument 03 §5.5).

- single_choice: Liste mit genau einer gültigen Option-ID, z. B. ["antwort_b"].
- multiple_choice: Liste mit mindestens einer gültigen, eindeutigen Option-ID.
- luecke: Text (1 bis 200 Zeichen nach dem Trimmen).

Beweist: Eine einzelne Auswahl wird nie als Zeichenkette zerlegt; unbekannte Option-IDs,
falsche Datentypen und leere Auswahlen führen zu einem verständlichen Validierungsfehler.
"""
from ..fehler import FachFehler


def _fehler(nachricht: str) -> FachFehler:
    return FachFehler("antwort_ungueltig", nachricht, status=422, felder={"gegeben": nachricht})


def normalisiere_antwort(fragetyp: str, optionen: list, gegeben) -> list | str:
    if fragetyp in ("single_choice", "multiple_choice"):
        if not isinstance(gegeben, list):
            raise _fehler("Die Auswahl muss als Liste von Option-IDs übermittelt werden.")
        if not all(isinstance(x, str) for x in gegeben):
            raise _fehler("Option-IDs müssen Text sein.")
        gueltige = {o.get("id") for o in optionen}
        unbekannt = [x for x in gegeben if x not in gueltige]
        if unbekannt:
            raise _fehler(f"Unbekannte Option: {unbekannt[0]}.")
        if len(set(gegeben)) != len(gegeben):
            raise _fehler("Eine Option darf nur einmal gewählt werden.")
        if fragetyp == "single_choice" and len(gegeben) != 1:
            raise _fehler("Bei Einzelauswahl bitte genau eine Option wählen.")
        if fragetyp == "multiple_choice" and len(gegeben) < 1:
            raise _fehler("Bitte mindestens eine Option wählen.")
        return list(gegeben)
    if fragetyp == "luecke":
        if not isinstance(gegeben, str):
            raise _fehler("Die Lücke muss als Text übermittelt werden.")
        text = gegeben.strip()
        if not (1 <= len(text) <= 200):
            raise _fehler("Die Antwort muss zwischen 1 und 200 Zeichen lang sein.")
        return text
    raise _fehler("Dieser Aufgabentyp kann nicht beantwortet werden.")


def antworttext(fragetyp: str, optionen: list, gegeben) -> str:
    """Lesbare Fassung der Antwort für Anzeige und Modellkontext."""
    if isinstance(gegeben, list):
        namen = {o["id"]: o.get("text", o["id"]) for o in optionen}
        return "; ".join(namen.get(x, x) for x in gegeben)
    return str(gegeben or "")
