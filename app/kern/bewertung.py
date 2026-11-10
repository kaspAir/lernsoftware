"""Auswertung geschlossener Aufgaben (Spez. §7.1, §7.4; PR-05).

Beweist: Punkte sind nie negativ und nie größer als `max_punkte`; Prozentwerte sind konsistent.
"""
from decimal import Decimal, ROUND_HALF_UP

CENT = Decimal("0.01")


def _auf_cent(wert: Decimal) -> Decimal:
    return wert.quantize(CENT, rounding=ROUND_HALF_UP)


def normalisiere_text(text: str, konfig: dict) -> str:
    """Normalisierung für Lückentexte (Spez. §7.1). Ändert nie die Bedeutung."""
    t = text.strip()
    if konfig.get("kleinschreibung", True):
        t = t.lower()
    if konfig.get("leerraum_zusammenfassen", True):
        t = " ".join(t.split())
    if konfig.get("umlaute_vergleich", True):
        for quelle, ziel in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
            t = t.replace(quelle, ziel)
    return t


def werte_aus(fragetyp: str, gegeben, loesung, max_punkte: Decimal, normalisierung: dict) -> dict:
    """Wertet eine Antwort aus und liefert Punkte, Maximum, Richtigkeit.

    - single_choice: max_punkte bei korrekter Option, sonst 0.
    - multiple_choice: max_punkte * clamp(richtig_gewählt - falsch_gewählt, 0, n_richtig) / n_richtig.
    - luecke: max_punkte bei Übereinstimmung mit einem zulässigen Text (normalisiert).
    """
    max_punkte = Decimal(str(max_punkte))
    if max_punkte <= 0:
        raise ValueError("max_punkte muss größer als 0 sein")

    if fragetyp == "single_choice":
        richtig_ids = set(loesung)
        gewaehlt = set(gegeben or [])
        punkte = max_punkte if gewaehlt == richtig_ids and len(richtig_ids) == 1 else Decimal(0)
    elif fragetyp == "multiple_choice":
        richtig_ids = set(loesung)
        gewaehlt = set(gegeben or [])
        n = len(richtig_ids)
        if n == 0:
            raise ValueError("multiple_choice ohne richtige Option")
        richtig_gewaehlt = len(gewaehlt & richtig_ids)
        falsch_gewaehlt = len(gewaehlt - richtig_ids)
        netto = max(0, min(n, richtig_gewaehlt - falsch_gewaehlt))
        punkte = _auf_cent(max_punkte * Decimal(netto) / Decimal(n))
    elif fragetyp == "luecke":
        zulaessig = {normalisiere_text(t, normalisierung) for t in loesung}
        antwort = normalisiere_text(str(gegeben or ""), normalisierung)
        punkte = max_punkte if antwort and antwort in zulaessig else Decimal(0)
    else:
        raise ValueError(f"Fragetyp nicht auswertbar: {fragetyp}")

    punkte = min(max(punkte, Decimal(0)), max_punkte)
    return {
        "punkte": _auf_cent(punkte),
        "maximum": _auf_cent(max_punkte),
        "richtig": punkte == max_punkte,
    }


def prozent(punkte: Decimal, maximum: Decimal) -> int | None:
    """Quote in ganzen Prozent; None bei Maximum 0 (PR-05)."""
    if maximum <= 0:
        return None
    return int((Decimal(punkte) / Decimal(maximum) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
