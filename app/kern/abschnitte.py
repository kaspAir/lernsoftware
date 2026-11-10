"""Abschnittsbildung aus Textunterlagen (IN-04, IN-10; Spez. §11).

Beweist: Abschnitte sind lückenlos und in Reihenfolge; kein Abschnitt überschreitet die
Höchstlänge, außer ein einzelner Satz ist länger (dann wird am Wortende geteilt).
"""
import re


def segmentiere(text: str, min_zeichen: int = 300, max_zeichen: int = 1200) -> list[str]:
    absaetze = [a.strip() for a in re.split(r"\n\s*\n", text) if a.strip()]
    # Markdown-Überschriften beginnen immer einen neuen Absatz
    neu: list[str] = []
    for absatz in absaetze:
        zeilen = absatz.split("\n")
        block: list[str] = []
        for zeile in zeilen:
            if zeile.lstrip().startswith("#") and block:
                neu.append("\n".join(block).strip())
                block = []
            block.append(zeile)
        if block:
            neu.append("\n".join(block).strip())

    # Zusammenfassen kurzer Absätze bis Mindestlänge
    zusammen: list[str] = []
    puffer = ""
    for absatz in neu:
        puffer = f"{puffer}\n\n{absatz}".strip() if puffer else absatz
        if len(puffer) >= min_zeichen:
            zusammen.append(puffer)
            puffer = ""
    if puffer:
        if zusammen and len(zusammen[-1]) + len(puffer) + 2 <= max_zeichen:
            zusammen[-1] = f"{zusammen[-1]}\n\n{puffer}"
        else:
            zusammen.append(puffer)

    # Zu lange Abschnitte am Wortende teilen
    ergebnis: list[str] = []
    for abschnitt in zusammen:
        while len(abschnitt) > max_zeichen:
            schnitt = abschnitt.rfind(" ", 0, max_zeichen)
            if schnitt <= 0:
                schnitt = max_zeichen
            ergebnis.append(abschnitt[:schnitt].strip())
            abschnitt = abschnitt[schnitt:].strip()
        if abschnitt:
            ergebnis.append(abschnitt)
    return ergebnis
