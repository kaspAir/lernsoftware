"""Testadapter (SIMULIERT). Deterministisch, ohne Netz, ohne Anbieter.

Er ersetzt den Vorschaltdienst nur für Entwicklung und Tests. Jede Antwort trägt
`herkunft = "SIMULIERT"`, damit keine simulierte Ausgabe als echte Modellprüfung erscheint
(Dokument 07 §0, Testkonzept Protokoll).

Verhalten: Er wählt den Abschnitt mit den meisten gemeinsamen Wörtern zur Frage als Quelle.
Ohne Überschneidung meldet er eine Lücke. Er erfindet keinen Inhalt jenseits der Abschnitte.
"""
import re

from .adapter import ModellAufruf

WORT = re.compile(r"[a-zäöüß]{4,}", re.IGNORECASE)


class SimulationsAdapter:
    herkunft = "SIMULIERT"
    modellname = "simulation-deterministisch"

    def __init__(self, fehler_modus: str | None = None):
        # fehler_modus erlaubt Tests, Ausfälle zu simulieren: "nicht_erreichbar", "schema", "409"
        self.fehler_modus = fehler_modus

    def aufrufen(self, aufruf: ModellAufruf) -> dict:
        from .adapter import ModellFehler, PseudonymisierungBlockiert

        if self.fehler_modus == "nicht_erreichbar":
            raise ModellFehler("Simulation: Modell nicht erreichbar")
        if self.fehler_modus == "409":
            raise PseudonymisierungBlockiert([{"befund_id": "simuliert"}], "vg_simuliert")
        if self.fehler_modus == "schema":
            return {"unvollstaendig": True}

        frage = aufruf.auftrag.get("frage", "")
        abschnitte = aufruf.auftrag.get("abschnitte", [])
        ziel = {w.lower() for w in WORT.findall(frage)}
        bestes, punkte = None, 0
        for abschnitt in abschnitte:
            treffer = len(ziel & {w.lower() for w in WORT.findall(abschnitt["text"])})
            if treffer > punkte:
                bestes, punkte = abschnitt, treffer
        if bestes is None:
            return {
                "form": "rueckfrage",
                "text": "Dazu finde ich in den freigegebenen Abschnitten keine belegte Antwort.",
                "quellen": [],
                "luecke": "Frage ohne Überschneidung mit den Abschnitten",
                "sicherheitsgrad": "unbestaetigt",
                "annahmen": [],
            }
        satz = _bester_satz(bestes["text"], ziel)
        return {
            "form": aufruf.auftrag.get("form", "erklaerung"),
            "text": "Laut dem Abschnitt: " + satz,
            "quellen": [{"abschnitt_id": bestes["id"], "aussage": "Textstelle des Abschnitts"}],
            "luecke": None,
            "sicherheitsgrad": "wahrscheinlich",
            "annahmen": ["Simulierte Auswahl der Quelle nach Wortüberschneidung"],
        }


def _bester_satz(text: str, ziel: set[str]) -> str:
    """Der Satz des Abschnitts mit den meisten Wortüberschneidungen zur Frage."""
    zusammen = " ".join(text.split())
    saetze = [s.lstrip("# ").strip() for s in re.split(r"(?<=[.!?])\s+", zusammen) if s.lstrip("# ").strip()]
    if not saetze:
        return text[:200]
    return max(saetze, key=lambda s: len(ziel & {w.lower() for w in WORT.findall(s)}))
