"""Wiederholungsplanung nach SM-2-Variante (Spez. §6.3; ADR-L-007). Austauschbar.

Beweist: Bei falscher Antwort beginnt das Intervall neu; das Intervall ist nach oben begrenzt;
der Leichtigkeitsfaktor fällt nie unter das Minimum.
"""
from dataclasses import dataclass, asdict
from datetime import date, timedelta


@dataclass
class Wiederholungszustand:
    ease: float
    intervall_tage: int
    wiederholungen: int

    @classmethod
    def start(cls, start_ease: float) -> "Wiederholungszustand":
        return cls(ease=start_ease, intervall_tage=0, wiederholungen=0)

    def als_dict(self) -> dict:
        return asdict(self)


def qualitaet(richtig: bool, hilfe_vorher: bool, selbsteinschaetzung: str | None) -> int:
    """Qualität q nach Spez. §6.3."""
    if not richtig:
        return 1
    if hilfe_vorher:
        return 3
    if selbsteinschaetzung == "sicher":
        return 5
    if selbsteinschaetzung in ("unsicher", "unklar"):
        return 3
    return 4


def naechster_zustand(z: Wiederholungszustand, q: int, cfg: dict) -> Wiederholungszustand:
    """Berechnet den Folgezustand (Spez. §6.3, Schritte 1–3)."""
    if not 0 <= q <= 5:
        raise ValueError("q muss zwischen 0 und 5 liegen")
    min_ease = cfg["min_ease"]
    max_int = cfg["max_intervall_tage"]
    if q < 3:
        return Wiederholungszustand(ease=z.ease, intervall_tage=1, wiederholungen=0)
    wdh = z.wiederholungen + 1
    if wdh == 1:
        intervall = 1
    elif wdh == 2:
        intervall = 6
    else:
        intervall = round(z.intervall_tage * z.ease)
    intervall = min(max(1, intervall), max_int)
    ease = max(min_ease, z.ease + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02)))
    return Wiederholungszustand(ease=round(ease, 4), intervall_tage=intervall, wiederholungen=wdh)


def faellig_am(letzter_versuch: date, z: Wiederholungszustand) -> date:
    return letzter_versuch + timedelta(days=z.intervall_tage)
