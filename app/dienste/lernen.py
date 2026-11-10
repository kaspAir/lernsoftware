"""Lernen und Üben: Übung, Hilfe, Versuch, Rückmeldung, Lernprofil, Wiederholung.

Ablauf (Dokument 01 §6): Lektion wählen → Übung → Hilfe (optional, vermerkt) → Antwort →
deterministische Auswertung (Kern) → Rückmeldung mit Quelle → Versuch und Lernprofil gespeichert.

Beweist: Hilfen vor der Antwort werden am Versuch vermerkt und verändern die Evidenz
(nicht selbstständig); Auswertung ist Code; Versuche sind nach Abgabe unveränderlich.
"""
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select

from ..db import mandant_abfrage
from ..fehler import FachFehler, nicht_gefunden
from ..kern import bewertung, evidenz, wiederholung
from ..models import (Abschnitt, Aufgabe, Hilfeereignis, Konto, Lektion, Lernziel, Modul, Unterlage,
                      Uebung, Versuch, Wiederholungszustand, jetzt)
from ..rechte import Kontext, modul_im_mandanten, pruefe_studierend
from .nachweis import schreibe_nachweis
from .verwaltung import FREIGEGEBEN

VERFUEGBAR = ("technisch_geprueft", "fachlich_geprueft")
SELBSTEINSCHAETZUNG = ("sicher", "unsicher", "unklar")


def _als_utc(dt: datetime) -> datetime:
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)


def _aufgabe_quellen_gueltig(session, kontext: Kontext, aufgabe: Aufgabe) -> bool:
    """Zur Laufzeit: alle Quellen aktuell und freigegeben (IN-07, D-06). Keine Anzeige bei Änderung."""
    for aid in aufgabe.abschnitt_ids:
        a = session.scalars(mandant_abfrage(Abschnitt, kontext.lernorganisation_id).where(Abschnitt.id == aid)).first()
        if a is None:
            return False
        u = session.get(Unterlage, a.unterlage_id)
        if u is None or u.status not in FREIGEGEBEN or a.unterlage_version != u.version:
            return False
    return True


def _verfuegbare_aufgaben(session, kontext: Kontext, modul_id: str, lektion_ids: list[str]) -> list[Aufgabe]:
    q = (mandant_abfrage(Aufgabe, kontext.lernorganisation_id)
         .where(Aufgabe.modul_id == modul_id, Aufgabe.lektion_id.in_(lektion_ids),
                Aufgabe.pruefstatus.in_(VERFUEGBAR)))
    kandidaten = session.scalars(q).all()
    ergebnis = [a for a in kandidaten if _aufgabe_quellen_gueltig(session, kontext, a)]
    ziele = {z.id: z for z in session.scalars(mandant_abfrage(Lernziel, kontext.lernorganisation_id)).all()}
    ergebnis.sort(key=lambda a: (ziele[a.lernziel_id].reihenfolge if a.lernziel_id in ziele else 0,
                                 a.erstellt_am or datetime.min))
    return ergebnis


def uebung_erzeugen(session, cfg: dict, kontext: Kontext, modul_id: str, lektion_ids: list[str]) -> dict:
    pruefe_studierend(session, kontext, modul_id)
    if not lektion_ids:
        raise FachFehler("lektion_fehlt", "Wähle mindestens eine Lektion.", status=422)
    lektionen = session.scalars(mandant_abfrage(Lektion, kontext.lernorganisation_id)
                                .where(Lektion.id.in_(lektion_ids), Lektion.modul_id == modul_id,
                                       Lektion.status == "aktiv")).all()
    if len(lektionen) != len(set(lektion_ids)):
        raise nicht_gefunden("Lektion")
    aufgaben = _verfuegbare_aufgaben(session, kontext, modul_id, lektion_ids)[: cfg["uebung"]["max_aufgaben"]]
    if not aufgaben:
        # PR-08: nicht auffüllen, sondern ehrlich melden
        raise FachFehler("keine_aufgaben", "Zu den gewählten Lektionen sind noch keine freigegebenen Aufgaben vorhanden.",
                         status=409)
    uebung = Uebung(lernorganisation_id=kontext.lernorganisation_id, konto_id=kontext.konto_id,
                    modul_id=modul_id, lektion_ids=list(lektion_ids),
                    aufgaben=[{"id": a.id, "version": a.version} for a in aufgaben], modus="lernen")
    session.add(uebung)
    session.flush()
    schreibe_nachweis(session, "uebung_erzeugt", kontext.lernorganisation_id, kontext.konto_id, uebung.id,
                      {"anzahl": len(aufgaben), "lektionen": list(lektion_ids)})
    return {"id": uebung.id, "modus": uebung.modus, "aufgaben": [_aufgabe_fuer_lernende(a) for a in aufgaben]}


def _aufgabe_fuer_lernende(a: Aufgabe) -> dict:
    """Sicht ohne Lösung und ohne Erklärung (Lösung erst nach Abgabe)."""
    return {"id": a.id, "version": a.version, "text": a.aufgabe_text, "fragetyp": a.fragetyp,
            "optionen": a.optionen, "max_punkte": float(a.max_punkte),
            "pruefstatus": a.pruefstatus,
            "hinweis_verfuegbar": bool(a.hinweis), "beispiel_verfuegbar": bool(a.beispiel)}


def _uebung_des_kontos(session, kontext: Kontext, uebung_id: str) -> Uebung:
    u = session.scalars(mandant_abfrage(Uebung, kontext.lernorganisation_id).where(Uebung.id == uebung_id)).first()
    if u is None or u.konto_id != kontext.konto_id:
        raise nicht_gefunden("Übung")
    return u


def _aufgabe_in_uebung(session, kontext: Kontext, uebung: Uebung, aufgabe_id: str) -> Aufgabe:
    if aufgabe_id not in [e["id"] for e in uebung.aufgaben]:
        raise nicht_gefunden("Aufgabe")
    a = session.scalars(mandant_abfrage(Aufgabe, kontext.lernorganisation_id).where(Aufgabe.id == aufgabe_id)).first()
    if a is None:
        raise nicht_gefunden("Aufgabe")
    return a


def hilfe_anfordern(session, kontext: Kontext, uebung_id: str, aufgabe_id: str, art: str) -> dict:
    if art not in ("hinweis", "beispiel"):
        raise FachFehler("hilfeart_ungueltig", "Hilfeart: hinweis oder beispiel.", status=422)
    uebung = _uebung_des_kontos(session, kontext, uebung_id)
    aufgabe = _aufgabe_in_uebung(session, kontext, uebung, aufgabe_id)
    text = aufgabe.hinweis if art == "hinweis" else aufgabe.beispiel
    if not text:
        return {"art": art, "text": None, "hinweis": "Für diese Aufgabe ist keine Hilfe dieser Art hinterlegt."}
    session.add(Hilfeereignis(lernorganisation_id=kontext.lernorganisation_id, konto_id=kontext.konto_id,
                              uebung_id=uebung.id, aufgabe_id=aufgabe.id, art=art))
    session.flush()
    return {"art": art, "text": text}


def _quellen_sicht(session, kontext: Kontext, abschnitt_ids: list[str]) -> list[dict]:
    quellen = []
    for aid in abschnitt_ids:
        a = session.scalars(mandant_abfrage(Abschnitt, kontext.lernorganisation_id).where(Abschnitt.id == aid)).first()
        if a is None:
            continue
        u = session.get(Unterlage, a.unterlage_id)
        quellen.append({"abschnitt_id": a.id, "unterlage": u.titel if u else None,
                        "version": a.unterlage_version, "position": a.position, "text": a.text})
    return quellen


def _naechster_schritt(richtig: bool, faellig: date) -> str:
    if richtig:
        return f"Nächste Wiederholung am {faellig.isoformat()}."
    return (f"Nächster Schritt: Abschnitt erneut lesen. Diese Aufgabe erscheint wieder am {faellig.isoformat()}.")


def versuch_abgeben(session, cfg: dict, kontext: Kontext, uebung_id: str, aufgabe_id: str,
                    gegeben, selbsteinschaetzung: str | None = None) -> dict:
    uebung = _uebung_des_kontos(session, kontext, uebung_id)
    aufgabe = _aufgabe_in_uebung(session, kontext, uebung, aufgabe_id)
    if aufgabe.pruefstatus not in VERFUEGBAR or not _aufgabe_quellen_gueltig(session, kontext, aufgabe):
        raise FachFehler("aufgabe_nicht_verfuegbar",
                         "Diese Aufgabe ist derzeit nicht verfügbar (Quelle in Prüfung oder Aufgabe gesperrt).",
                         status=409)
    if selbsteinschaetzung is not None and selbsteinschaetzung not in SELBSTEINSCHAETZUNG:
        raise FachFehler("selbsteinschaetzung_ungueltig", "Selbsteinschätzung: sicher, unsicher oder unklar.", status=422)

    hilfen = session.scalars(select(Hilfeereignis).where(
        Hilfeereignis.konto_id == kontext.konto_id, Hilfeereignis.aufgabe_id == aufgabe.id,
        Hilfeereignis.uebung_id == uebung.id, Hilfeereignis.versuch_id.is_(None))).all()
    hilfen_liste = [{"art": h.art, "zeitpunkt": _als_utc(h.zeitpunkt).isoformat()} for h in hilfen]

    erg = bewertung.werte_aus(aufgabe.fragetyp, gegeben, aufgabe.loesung, aufgabe.max_punkte,
                              cfg["normalisierung"]["luecke"])
    snapshot = {
        "aufgabe_id": aufgabe.id, "version": aufgabe.version, "text": aufgabe.aufgabe_text,
        "fragetyp": aufgabe.fragetyp, "optionen": aufgabe.optionen, "loesung": aufgabe.loesung,
        "max_punkte": str(aufgabe.max_punkte), "erklaerung": aufgabe.erklaerung,
        "abschnitt_ids": list(aufgabe.abschnitt_ids), "pruefstatus": aufgabe.pruefstatus,
    }
    versuch = Versuch(
        lernorganisation_id=kontext.lernorganisation_id, konto_id=kontext.konto_id, uebung_id=uebung.id,
        aufgabe_id=aufgabe.id, aufgabe_version=aufgabe.version, aufgabe_snapshot=snapshot,
        gegeben=gegeben, punkte=erg["punkte"], maximum=erg["maximum"], richtig=erg["richtig"],
        hilfen=hilfen_liste, selbsteinschaetzung=selbsteinschaetzung,
        herkunft={"erzeugt_durch": "kern", "auswertung": "lösungsschlüssel", "modell": None},
    )
    session.add(versuch)
    session.flush()
    for h in hilfen:
        h.versuch_id = versuch.id

    # Wiederholungsplanung (getrennt von der Evidenz)
    zustand = session.scalars(mandant_abfrage(Wiederholungszustand, kontext.lernorganisation_id).where(
        Wiederholungszustand.konto_id == kontext.konto_id, Wiederholungszustand.aufgabe_id == aufgabe.id)).first()
    alt = wiederholung.Wiederholungszustand.start(cfg["wiederholung"]["start_ease"])
    if zustand is not None:
        alt = wiederholung.Wiederholungszustand(ease=float(zustand.ease), intervall_tage=zustand.intervall_tage,
                                                wiederholungen=zustand.wiederholungen)
    q = wiederholung.qualitaet(erg["richtig"], bool(hilfen), selbsteinschaetzung)
    neu = wiederholung.naechster_zustand(alt, q, cfg["wiederholung"])
    heute = jetzt().date()
    faellig = heute + timedelta(days=neu.intervall_tage)
    if zustand is None:
        zustand = Wiederholungszustand(lernorganisation_id=kontext.lernorganisation_id,
                                       konto_id=kontext.konto_id, aufgabe_id=aufgabe.id)
        session.add(zustand)
    zustand.ease = neu.ease
    zustand.intervall_tage = neu.intervall_tage
    zustand.wiederholungen = neu.wiederholungen
    zustand.naechste_faelligkeit = faellig.isoformat()

    # Rückmeldung: deterministisch, mit Quelle (LE-05, BS-10)
    quellen = _quellen_sicht(session, kontext, aufgabe.abschnitt_ids)
    kopf = "Richtig." if erg["richtig"] else "Noch nicht ganz."
    if erg["richtig"] and hilfen_liste:
        kopf = "Richtig, mit Hilfe. Mit Hilfen gilt das noch nicht als selbstständige Leistung."
    text = f"{kopf} {aufgabe.erklaerung}"
    from ..models import Nachricht
    session.add(Nachricht(lernorganisation_id=kontext.lernorganisation_id, konto_id=kontext.konto_id,
                          versuch_id=versuch.id, rolle="system", form="rueckmeldung", text=text,
                          quellen=[{k: v for k, v in qu.items() if k != "text"} for qu in quellen],
                          herkunft={"erzeugt_durch": "kern", "modell": None}))
    schreibe_nachweis(session, "versuch", kontext.lernorganisation_id, kontext.konto_id, versuch.id,
                      {"aufgabe_id": aufgabe.id, "aufgabe_version": aufgabe.version,
                       "punkte": str(erg["punkte"]), "maximum": str(erg["maximum"]),
                       "hilfen": len(hilfen_liste), "selbsteinschaetzung": selbsteinschaetzung,
                       "wiederholung_q": q})
    session.flush()
    return {
        "versuch_id": versuch.id,
        "richtig": erg["richtig"],
        "punkte": float(erg["punkte"]),
        "maximum": float(erg["maximum"]),
        "prozent": bewertung.prozent(erg["punkte"], erg["maximum"]),
        "hilfen_vorher": len(hilfen_liste),
        "rueckmeldung": text,
        "quellen": quellen,
        "naechster_schritt": _naechster_schritt(erg["richtig"], faellig),
        "faellig_am": faellig.isoformat(),
    }


def lernprofil(session, cfg: dict, kontext: Kontext, modul_id: str) -> list[dict]:
    """Lernprofil je Lernziel. Studierende: eigene Werte. Admin/Dozierende: nur aggregierte Zählung
    ohne Einzelversuche (AD-03, BS-07)."""
    modul = modul_im_mandanten(session, kontext, modul_id)
    from ..rechte import modul_rolle
    rolle = modul_rolle(session, kontext, modul.id)
    if rolle == "studierende":
        konto_id = kontext.konto_id
    elif rolle == "dozierende" or rolle == "assistenz" or rolle == "admin":
        raise FachFehler("nur_aggregiert", "Lehrpersonen sehen Lernprofile nur aggregiert.", status=403)
    else:
        raise nicht_gefunden("Modul")

    schwelle = cfg["evidenz"]["schwelle_aufgaben"]
    widerspruch = cfg["evidenz"]["widerspruch_nach_falsch"]
    ziele = session.scalars(
        mandant_abfrage(Lernziel, kontext.lernorganisation_id)
        .join(Lektion, Lektion.id == Lernziel.lektion_id).where(Lektion.modul_id == modul.id)
        .order_by(Lektion.reihenfolge, Lernziel.reihenfolge)).all()
    versuche = session.scalars(mandant_abfrage(Versuch, kontext.lernorganisation_id).where(
        Versuch.konto_id == konto_id).order_by(Versuch.zeitpunkt)).all()
    aufgaben = {a.id: a for a in session.scalars(mandant_abfrage(Aufgabe, kontext.lernorganisation_id)
                                                 .where(Aufgabe.modul_id == modul.id)).all()}
    ergebnis = []
    for z in ziele:
        eingaenge = [evidenz.Versuchseingang(aufgabe_id=v.aufgabe_id,
                                             punkte_voll=bool(v.richtig),
                                             hilfe_vorher=bool(v.hilfen),
                                             zeitpunkt=_als_utc(v.zeitpunkt))
                     for v in versuche if v.aufgabe_id in aufgaben and aufgaben[v.aufgabe_id].lernziel_id == z.id]
        lage = evidenz.evidenzlage(eingaenge, schwelle, widerspruch)
        ergebnis.append({"lernziel_id": z.id, "text": z.text, "handlungsstufe": z.handlungsstufe, **lage})
    return ergebnis


def lernprofil_aggregiert(session, kontext: Kontext, modul_id: str) -> dict:
    """Für Lehrpersonen: Zählungen ohne Personenbezug."""
    from ..rechte import modul_rolle
    rolle = modul_rolle(session, kontext, modul_id)
    if rolle not in ("dozierende", "admin"):
        raise FachFehler("nicht_berechtigt", "Aggregierte Sicht nur für Lehrpersonen und Administration.", status=403)
    modul_im_mandanten(session, kontext, modul_id)
    uebungen = session.scalars(mandant_abfrage(Uebung, kontext.lernorganisation_id)
                               .where(Uebung.modul_id == modul_id)).all()
    anzahl_versuche = len(session.scalars(mandant_abfrage(Versuch, kontext.lernorganisation_id)
                                          .where(Versuch.uebung_id.in_([u.id for u in uebungen]))).all()) if uebungen else 0
    anzahl_lernende = len({u.konto_id for u in uebungen})
    return {"modul_id": modul_id, "versuche": anzahl_versuche, "lernende": anzahl_lernende}
