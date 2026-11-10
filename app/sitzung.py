"""Sitzungsdauer (Inkrement 1.1, Punkt 7).

Festlegung: Die Sitzung gilt 120 Minuten **ab Anmeldung** (absolut), nicht ab letzter Aktivität.
Begründung: Eine feste Obergrenze begrenzt die Zeit, in der ein offenes Gerät genutzt werden kann,
und ist ohne serverseitige Sitzungsliste eindeutig prüfbar (Abweichung A-13). Nach Ablauf wird die
Sitzung verworfen; die Person meldet sich neu an. Entzug durch Deaktivierung wirkt sofort, weil
der Kontext bei jeder Anfrage neu geladen wird (rechte.lade_kontext).
"""
from datetime import datetime, timedelta, timezone


def sitzung_beginnt(now: datetime | None = None) -> str:
    return (now or datetime.now(timezone.utc)).isoformat()


def sitzung_abgelaufen(angemeldet_am: str | None, dauer_minuten: int, now: datetime | None = None) -> bool:
    if not angemeldet_am:
        return True
    start = datetime.fromisoformat(angemeldet_am)
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    jetzt = now or datetime.now(timezone.utc)
    return jetzt >= start + timedelta(minutes=dauer_minuten)
