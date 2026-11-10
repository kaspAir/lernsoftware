"""Nachweise (RA-13, NF-04): unveränderliche Protokolleinträge.

Beweist: Jeder Eintrag wird neu angelegt; es gibt keine Aktualisierungsfunktion.
"""
from ..models import Nachweis


def schreibe_nachweis(session, art: str, lernorganisation_id: str | None, konto_id: str | None,
                      objekt_id: str | None, inhalt: dict, kennung: str | None = None) -> Nachweis:
    eintrag = Nachweis(
        lernorganisation_id=lernorganisation_id,
        art=art,
        konto_id=konto_id,
        objekt_id=objekt_id,
        kennung=kennung,
        inhalt=inhalt,
    )
    session.add(eintrag)
    return eintrag
