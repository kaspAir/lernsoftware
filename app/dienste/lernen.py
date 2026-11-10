"""Lernen und Üben: Übung, Hilfe, Abgabe, Versuchssicht, Lernprofil, Wiederholung.

Ablauf: Lektion wählen → Übung → Hilfe (optional, vermerkt) → Abgabe (idempotent) → Auswertung im
Kern → Rückmeldung mit Quelle → Versuch dauerhaft abrufbar.

Trennung der Prüfungen (Inkrement 1.1, Punkt 4):
- historische Anzeige eines gespeicherten Versuchs: immer möglich, solange die Person Zugriff auf
  das Modul hat; zeigt den damaligen Aufgabenstand;
- aktuelle Verfügbarkeit einer Aufgabe: `aufgabe_verfuegbar` (Freigabe, Version, Lektion);
- Zulässigkeit einer neuen Erklärung: nur bei aktuell verwendbaren Quellen (siehe lernbegleiter).

Beweist: Eine Abgabe mit gleichem Idempotenzschlüssel erzeugt keinen zweiten Versuch und keine zweite
Fortschreibung; Hilfen und frühere Lösungsanzeigen machen die nächste Abgabe nicht selbstständig.
"""
import re
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from ..db import mandant_abfrage
from ..fehler import FachFehler, nicht_gefunden
from ..kern import antwort as antwortkern
from ..kern import bewertung, evidenz, wiederholung
from ..models import (Abschnitt, Aufgabe, Hilfeereignis, Lektion, Lernziel, Modul, Nachricht, Unterlage,
                      UnterlageVersion, Uebung, Versuch, Wiederholungszustand, jetzt)
from ..rechte import Kontext, modul_im_mandanten, modul_rolle, pruefe_studierend
from .nachweis import schreibe_nachweis
from .verwaltung import FREIGEGEBEN

VERFUEGBAR = ("technisch_geprueft", "fachlich_geprueft")
SELBSTEINSCHAETZUNG = ("sicher", "unsicher", "unklar")
SCHLUESSEL = re.compile(r"^[A-Za-z0-9_-]{8,64}$")


def _als_utc(dt: datetime) -> datetime:
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)


def _schluessel_pruefen(schluessel) -> str:
    if not isinstance(schluessel, str) or not SCHLUESSEL.match(schluessel):
        raise FachFehler("schluessel_ungueltig",
                         "Der Anfrage-Schlüssel fehlt oder ist ungültig (8 bis 64 Zeichen: Buchstaben, Ziffern, _ -).",
                         status=422)
    return schluessel


# ---------- Verfügbarkeit (aktueller Stand) ----------

def aufgabe_verfuegbar(session, kontext: Kontext, aufgabe: Aufgabe) -> tuple[bool, str | None]:
    """Aktuelle Verfügbarkeit einer Aufgabe für neue Abgaben und Hilfen (IN-07, D-06)."""
    if aufgabe.pruefstatus not in VERFUEGBAR:
        return False, "Die Aufgabe ist gesperrt oder verworfen."
    lektion = session.get(Lektion, aufgabe.lektion_id)
    if lektion is None or lektion.status != "aktiv":
        return False, "Die Lektion ist nicht mehr aktiv."
    modul = session.get(Modul, aufgabe.modul_id)
    if modul is None or modul.status != "aktiv":
        return False, "Das Modul ist nicht mehr aktiv."
    for aid in aufgabe.abschnitt_ids:
        ok, grund = abschnitt_aktuell_verwendbar(session, kontext, aid)
        if not ok:
            return False, grund
    return True, None


def abschnitt_aktuell_verwendbar(session, kontext: Kontext, abschnitt_id: str) -> tuple[bool, str | None]:
    a = session.scalars(mandant_abfrage(Abschnitt, kontext.lernorganisation_id).where(Abschnitt.id == abschnitt_id)).first()
    if a is None:
        return False, "Eine Quelle ist nicht mehr vorhanden."
    u = session.get(Unterlage, a.unterlage_id)
    if u is None:
        return False, "Eine Quelle ist nicht mehr vorhanden."
    if u.status == "in_pruefung":
        return False, "Eine Quelle wird gerade überarbeitet (in Prüfung)."
    if u.status not in FREIGEGEBEN:
        return False, "Eine Quelle ist nicht freigegeben."
    if a.unterlage_version != u.version:
        return False, "Eine Quelle hat eine neuere Fassung; die Aufgabe bezieht sich auf eine ältere."
    return True, None


def _verfuegbare_aufgaben(session, kontext: Kontext, modul_id: str, lektion_ids: list[str]) -> list[Aufgabe]:
    kandidaten = session.scalars(
        mandant_abfrage(Aufgabe, kontext.lernorganisation_id)
        .where(Aufgabe.modul_id == modul_id, Aufgabe.lektion_id.in_(lektion_ids),
               Aufgabe.pruefstatus.in_(VERFUEGBAR))).all()
    ergebnis = [a for a in kandidaten if aufgabe_verfuegbar(session, kontext, a)[0]]
    ziele = {z.id: z for z in session.scalars(mandant_abfrage(Lernziel, kontext.lernorganisation_id)).all()}
    ergebnis.sort(key=lambda a: (ziele[a.lernziel_id].reihenfolge if a.lernziel_id in ziele else 0,
                                 a.erstellt_am or datetime.min))
    return ergebnis


def _aufgabe_fuer_lernende(a: Aufgabe) -> dict:
    """Sicht ohne Lösung und ohne Erklärung (Lösung erst nach Abgabe)."""
    return {"id": a.id, "version": a.version, "text": a.aufgabe_text, "fragetyp": a.fragetyp,
            "optionen": a.optionen, "max_punkte": float(a.max_punkte), "pruefstatus": a.pruefstatus,
            "hinweis_verfuegbar": bool(a.hinweis), "beispiel_verfuegbar": bool(a.beispiel)}


# ---------- Übung ----------

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
        raise FachFehler("keine_aufgaben",
                         "Zu den gewählten Lektionen sind noch keine verfügbaren Aufgaben vorhanden.", status=409)
    uebung = Uebung(lernorganisation_id=kontext.lernorganisation_id, konto_id=kontext.konto_id,
                    modul_id=modul_id, lektion_ids=list(lektion_ids),
                    aufgaben=[{"id": a.id, "version": a.version} for a in aufgaben], modus="lernen")
    session.add(uebung)
    session.flush()
    schreibe_nachweis(session, "uebung_erzeugt", kontext.lernorganisation_id, kontext.konto_id, uebung.id,
                      {"anzahl": len(aufgaben), "lektionen": list(lektion_ids)})
    return {"id": uebung.id, "modus": uebung.modus, "aufgaben": [_aufgabe_fuer_lernende(a) for a in aufgaben]}


def _uebung_des_kontos(session, kontext: Kontext, uebung_id: str) -> Uebung:
    u = session.scalars(mandant_abfrage(Uebung, kontext.lernorganisation_id).where(Uebung.id == uebung_id)).first()
    if u is None or u.konto_id != kontext.konto_id:
        raise nicht_gefunden("Übung")
    pruefe_studierend(session, kontext, u.modul_id)  # aktuelle Modulberechtigung, auch bei begonnener Übung
    return u


def _aufgabe_in_uebung(session, kontext: Kontext, uebung: Uebung, aufgabe_id: str) -> Aufgabe:
    if aufgabe_id not in [e["id"] for e in uebung.aufgaben]:
        raise nicht_gefunden("Aufgabe")
    a = session.scalars(mandant_abfrage(Aufgabe, kontext.lernorganisation_id).where(Aufgabe.id == aufgabe_id)).first()
    if a is None:
        raise nicht_gefunden("Aufgabe")
    return a


def uebung_sicht(session, kontext: Kontext, uebung_id: str) -> dict:
    """Übung mit dem aktuellen Stand je Aufgabe: Verfügbarkeit, offene Hilfe, bisherige Versuche."""
    uebung = _uebung_des_kontos(session, kontext, uebung_id)
    aufgaben = []
    for e in uebung.aufgaben:
        a = session.get(Aufgabe, e["id"])
        if a is None:
            continue
        verfuegbar, grund = aufgabe_verfuegbar(session, kontext, a)
        versuche = session.scalars(mandant_abfrage(Versuch, kontext.lernorganisation_id).where(
            Versuch.konto_id == kontext.konto_id, Versuch.aufgabe_id == a.id).order_by(Versuch.versuchsnummer)).all()
        offene = session.scalars(mandant_abfrage(Hilfeereignis, kontext.lernorganisation_id).where(
            Hilfeereignis.konto_id == kontext.konto_id, Hilfeereignis.aufgabe_id == a.id,
            Hilfeereignis.uebung_id == uebung.id, Hilfeereignis.versuch_id.is_(None))).all()
        arten = {h.art for h in offene}
        aufgaben.append({
            **_aufgabe_fuer_lernende(a),
            "verfuegbar": verfuegbar, "nicht_verfuegbar_grund": grund,
            "offene_hilfe": {"art": "hinweis" if "hinweis" in arten else ("beispiel" if "beispiel" in arten else None),
                             "text": a.hinweis if "hinweis" in arten else (a.beispiel if "beispiel" in arten else None)},
            "versuche": [{"versuch_id": v.id, "versuchsnummer": v.versuchsnummer, "richtig": v.richtig,
                          "zeitpunkt": _als_utc(v.zeitpunkt).isoformat()} for v in versuche],
            "naechste_versuchsnummer": len(versuche) + 1,
        })
    return {"id": uebung.id, "modul_id": uebung.modul_id, "aufgaben": aufgaben}


def hilfe_anfordern(session, cfg: dict, kontext: Kontext, uebung_id: str, aufgabe_id: str, art: str) -> dict:
    if art not in ("hinweis", "beispiel"):
        raise FachFehler("hilfeart_ungueltig", "Hilfeart: hinweis oder beispiel.", status=422)
    uebung = _uebung_des_kontos(session, kontext, uebung_id)
    aufgabe = _aufgabe_in_uebung(session, kontext, uebung, aufgabe_id)
    verfuegbar, grund = aufgabe_verfuegbar(session, kontext, aufgabe)
    if not verfuegbar:
        raise FachFehler("aufgabe_nicht_verfuegbar", f"Hilfe ist derzeit nicht verfügbar: {grund}", status=409)
    text = aufgabe.hinweis if art == "hinweis" else aufgabe.beispiel
    if not text:
        return {"art": art, "text": None, "hinweis": "Für diese Aufgabe ist keine Hilfe dieser Art hinterlegt."}
    bereits = session.scalars(mandant_abfrage(Hilfeereignis, kontext.lernorganisation_id).where(
        Hilfeereignis.konto_id == kontext.konto_id, Hilfeereignis.aufgabe_id == aufgabe.id,
        Hilfeereignis.uebung_id == uebung.id, Hilfeereignis.art == art,
        Hilfeereignis.versuch_id.is_(None))).first()
    if bereits is None:
        session.add(Hilfeereignis(lernorganisation_id=kontext.lernorganisation_id, konto_id=kontext.konto_id,
                                  uebung_id=uebung.id, aufgabe_id=aufgabe.id, art=art))
        session.flush()
    return {"art": art, "text": text, "wirkt_bei": "nächster Abgabe (wird als Hilfe vermerkt)"}


# ---------- Abgabe ----------

def _hilfen_vorher(session, kontext: Kontext, uebung_id: str, aufgabe_id: str) -> list[dict]:
    offene = session.scalars(mandant_abfrage(Hilfeereignis, kontext.lernorganisation_id).where(
        Hilfeereignis.konto_id == kontext.konto_id, Hilfeereignis.aufgabe_id == aufgabe_id,
        Hilfeereignis.uebung_id == uebung_id, Hilfeereignis.versuch_id.is_(None))).all()
    liste = [{"art": h.art, "zeitpunkt": _als_utc(h.zeitpunkt).isoformat()} for h in offene]
    frueher = session.scalars(mandant_abfrage(Versuch, kontext.lernorganisation_id).where(
        Versuch.konto_id == kontext.konto_id, Versuch.aufgabe_id == aufgabe_id)).first()
    if frueher is not None:
        # Eine frühere Auswertung zeigte die Lösung: die nächste Abgabe ist nicht selbstständig.
        liste.append({"art": "loesung_gesehen", "zeitpunkt": None})
    return liste


def _ergebnis(session, kontext: Kontext, versuch: Versuch, wiederholt: bool) -> dict:
    nachricht = session.scalars(mandant_abfrage(Nachricht, kontext.lernorganisation_id).where(
        Nachricht.versuch_id == versuch.id, Nachricht.form == "rueckmeldung")).first()
    faellig = (nachricht.herkunft or {}).get("faellig_am") if nachricht else None
    return {
        "versuch_id": versuch.id,
        "versuchsnummer": versuch.versuchsnummer,
        "aufgabe_id": versuch.aufgabe_id,
        "richtig": versuch.richtig,
        "punkte": float(versuch.punkte),
        "maximum": float(versuch.maximum),
        "prozent": bewertung.prozent(versuch.punkte, versuch.maximum),
        "hilfen_vorher": len([h for h in versuch.hilfen if h.get("art") != "loesung_gesehen"]),
        "selbststaendig": not versuch.hilfen,
        "rueckmeldung": nachricht.text if nachricht else "",
        "quellen": _quellen_sicht(session, kontext, versuch.aufgabe_snapshot.get("abschnitt_ids", [])),
        "naechster_schritt": _naechster_schritt(versuch.richtig, faellig),
        "faellig_am": faellig,
        "wiederholt": wiederholt,
        "hinweis_wiederholung": "Dies ist die gespeicherte Auswertung. Es wurde kein neuer Versuch angelegt."
        if wiederholt else None,
    }


def versuch_abgeben(session, cfg: dict, kontext: Kontext, uebung_id: str, aufgabe_id: str,
                    gegeben, selbsteinschaetzung: str | None, schluessel) -> dict:
    schluessel = _schluessel_pruefen(schluessel)
    if selbsteinschaetzung is not None and selbsteinschaetzung not in SELBSTEINSCHAETZUNG:
        raise FachFehler("selbsteinschaetzung_ungueltig", "Selbsteinschätzung: sicher, unsicher oder unklar.", status=422)

    uebung = _uebung_des_kontos(session, kontext, uebung_id)  # Berechtigung gilt auch für Wiederholungen

    # Wiederholung desselben Requests: gespeicherte Auswertung zurückgeben, nichts neu schreiben
    vorhanden = session.scalars(mandant_abfrage(Versuch, kontext.lernorganisation_id).where(
        Versuch.konto_id == kontext.konto_id, Versuch.idempotenz_schluessel == schluessel)).first()
    if vorhanden is not None:
        if vorhanden.uebung_id != uebung.id or vorhanden.aufgabe_id != aufgabe_id:
            raise FachFehler("schluessel_wiederverwendet", "Dieser Anfrage-Schlüssel gehört zu einer anderen Abgabe.",
                             status=409)
        return _ergebnis(session, kontext, vorhanden, wiederholt=True)

    aufgabe = _aufgabe_in_uebung(session, kontext, uebung, aufgabe_id)
    verfuegbar, grund = aufgabe_verfuegbar(session, kontext, aufgabe)
    if not verfuegbar:
        raise FachFehler("aufgabe_nicht_verfuegbar", f"Diese Aufgabe ist derzeit nicht verfügbar: {grund}", status=409)
    gegeben = antwortkern.normalisiere_antwort(aufgabe.fragetyp, aufgabe.optionen, gegeben)

    erg = bewertung.werte_aus(aufgabe.fragetyp, gegeben, aufgabe.loesung, aufgabe.max_punkte,
                              cfg["normalisierung"]["luecke"])
    hilfen = _hilfen_vorher(session, kontext, uebung.id, aufgabe.id)
    vorherige = session.scalars(mandant_abfrage(Versuch, kontext.lernorganisation_id).where(
        Versuch.konto_id == kontext.konto_id, Versuch.aufgabe_id == aufgabe.id)).all()
    snapshot = {
        "aufgabe_id": aufgabe.id, "version": aufgabe.version, "text": aufgabe.aufgabe_text,
        "fragetyp": aufgabe.fragetyp, "optionen": aufgabe.optionen, "loesung": aufgabe.loesung,
        "max_punkte": str(aufgabe.max_punkte), "erklaerung": aufgabe.erklaerung,
        "abschnitt_ids": list(aufgabe.abschnitt_ids), "lernziel_id": aufgabe.lernziel_id,
        "pruefstatus": aufgabe.pruefstatus,
    }
    versuch = Versuch(
        lernorganisation_id=kontext.lernorganisation_id, konto_id=kontext.konto_id, uebung_id=uebung.id,
        aufgabe_id=aufgabe.id, aufgabe_version=aufgabe.version, aufgabe_snapshot=snapshot,
        gegeben=gegeben, punkte=erg["punkte"], maximum=erg["maximum"], richtig=erg["richtig"],
        hilfen=hilfen, selbsteinschaetzung=selbsteinschaetzung, versuchsnummer=len(vorherige) + 1,
        idempotenz_schluessel=schluessel,
        herkunft={"erzeugt_durch": "kern", "auswertung": "lösungsschlüssel", "modell": None},
    )
    session.add(versuch)
    try:
        session.flush()  # Eindeutigkeit des Schlüssels greift hier (Doppelabgabe, parallele Anfragen)
    except IntegrityError:
        session.rollback()
        vorhanden = session.scalars(mandant_abfrage(Versuch, kontext.lernorganisation_id).where(
            Versuch.konto_id == kontext.konto_id, Versuch.idempotenz_schluessel == schluessel)).first()
        if vorhanden is None:
            raise
        return _ergebnis(session, kontext, vorhanden, wiederholt=True)

    for h in session.scalars(mandant_abfrage(Hilfeereignis, kontext.lernorganisation_id).where(
            Hilfeereignis.konto_id == kontext.konto_id, Hilfeereignis.aufgabe_id == aufgabe.id,
            Hilfeereignis.uebung_id == uebung.id, Hilfeereignis.versuch_id.is_(None))).all():
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
    faellig = jetzt().date() + timedelta(days=neu.intervall_tage)
    if zustand is None:
        zustand = Wiederholungszustand(lernorganisation_id=kontext.lernorganisation_id,
                                       konto_id=kontext.konto_id, aufgabe_id=aufgabe.id)
        session.add(zustand)
    zustand.ease = neu.ease
    zustand.intervall_tage = neu.intervall_tage
    zustand.wiederholungen = neu.wiederholungen
    zustand.naechste_faelligkeit = faellig.isoformat()

    # Rückmeldung: deterministisch, mit Lösung und Quelle (LE-05, BS-10)
    loesung_text = ", ".join(_optionstext(aufgabe, x) for x in aufgabe.loesung) if aufgabe.fragetyp != "luecke" \
        else " oder ".join(aufgabe.loesung)
    if erg["richtig"]:
        kopf = "Richtig." if not hilfen else "Richtig, aber nicht selbstständig (Hilfe oder frühere Lösung)."
    else:
        kopf = "Noch nicht ganz."
    text = f"{kopf} Richtige Lösung: {loesung_text}. {aufgabe.erklaerung}"
    session.add(Nachricht(lernorganisation_id=kontext.lernorganisation_id, konto_id=kontext.konto_id,
                          versuch_id=versuch.id, rolle="system", form="rueckmeldung", text=text,
                          quellen=[{"abschnitt_id": a} for a in aufgabe.abschnitt_ids],
                          herkunft={"erzeugt_durch": "kern", "faellig_am": faellig.isoformat()}))
    schreibe_nachweis(session, "versuch", kontext.lernorganisation_id, kontext.konto_id, versuch.id,
                      {"aufgabe_id": aufgabe.id, "aufgabe_version": aufgabe.version,
                       "versuchsnummer": versuch.versuchsnummer, "punkte": str(erg["punkte"]),
                       "maximum": str(erg["maximum"]), "hilfen": len(hilfen), "wiederholung_q": q,
                       "selbsteinschaetzung": selbsteinschaetzung},
                      kennung=None)
    session.flush()
    return _ergebnis(session, kontext, versuch, wiederholt=False)


def _optionstext(aufgabe: Aufgabe, option_id: str) -> str:
    for o in aufgabe.optionen or []:
        if o.get("id") == option_id:
            return o.get("text", option_id)
    return option_id


def _naechster_schritt(richtig: bool, faellig: str | None) -> str:
    if richtig:
        return f"Nächste Wiederholung am {faellig}." if faellig else "Nächste Wiederholung wird geplant."
    return f"Nächster Schritt: Abschnitt erneut lesen. Diese Aufgabe erscheint wieder am {faellig}." \
        if faellig else "Nächster Schritt: Abschnitt erneut lesen."


# ---------- Quellen (historischer Stand + aktueller Status) ----------

def _quellen_sicht(session, kontext: Kontext, abschnitt_ids: list[str]) -> list[dict]:
    quellen = []
    for aid in abschnitt_ids:
        a = session.scalars(mandant_abfrage(Abschnitt, kontext.lernorganisation_id).where(Abschnitt.id == aid)).first()
        if a is None:
            quellen.append({"abschnitt_id": aid, "verfuegbar": False, "hinweis": "Quelle nicht mehr vorhanden."})
            continue
        u = session.get(Unterlage, a.unterlage_id)
        verwendbar, grund = abschnitt_aktuell_verwendbar(session, kontext, aid)
        quellen.append({
            "abschnitt_id": a.id,
            "unterlage": u.titel if u else None,
            "position": a.position,
            "version_zitiert": a.unterlage_version,
            "version_aktuell": u.version if u else None,
            "status_aktuell": u.status if u else None,
            "neu_verwendbar": verwendbar,
            "hinweis": None if verwendbar else grund,
            "text": a.text,
        })
    return quellen


def abschnitt_sicht(session, kontext: Kontext, abschnitt_id: str) -> dict:
    """Einzelner zitierter Abschnitt mit historischem Stand und aktuellem Freigabestatus.
    Lesbar, solange die Person das Modul sehen darf; bei Entzug schlägt die Modulprüfung fehl."""
    a = session.scalars(mandant_abfrage(Abschnitt, kontext.lernorganisation_id).where(Abschnitt.id == abschnitt_id)).first()
    if a is None:
        raise nicht_gefunden("Abschnitt")
    u = session.get(Unterlage, a.unterlage_id)
    pruefe_studierend(session, kontext, u.modul_id)
    verwendbar, grund = abschnitt_aktuell_verwendbar(session, kontext, abschnitt_id)
    version_text = session.scalars(mandant_abfrage(UnterlageVersion, kontext.lernorganisation_id).where(
        UnterlageVersion.unterlage_id == u.id, UnterlageVersion.nummer == a.unterlage_version)).first()
    return {
        "abschnitt_id": a.id, "unterlage": u.titel, "position": a.position,
        "version_zitiert": a.unterlage_version, "version_aktuell": u.version, "status_aktuell": u.status,
        "neu_verwendbar": verwendbar, "hinweis": None if verwendbar else grund,
        "text": a.text,
        "volltext_version": version_text.inhalt_text if version_text else None,
    }


# ---------- Versuchssicht ----------

def versuch_sicht(session, kontext: Kontext, versuch_id: str) -> dict:
    v = session.scalars(mandant_abfrage(Versuch, kontext.lernorganisation_id).where(Versuch.id == versuch_id)).first()
    if v is None or v.konto_id != kontext.konto_id:
        raise nicht_gefunden("Versuch")
    uebung = session.get(Uebung, v.uebung_id)
    pruefe_studierend(session, kontext, uebung.modul_id)  # aktuelle Berechtigung auch für gespeicherte Ansicht
    snap = v.aufgabe_snapshot
    gegeben = v.gegeben if isinstance(v.gegeben, list) else [v.gegeben]
    verlauf = session.scalars(mandant_abfrage(Nachricht, kontext.lernorganisation_id).where(
        Nachricht.versuch_id == v.id).order_by(Nachricht.zeitpunkt, Nachricht.id)).all()
    aktuell_verfuegbar, grund = _snapshot_verfuegbar(session, kontext, snap)
    return {
        "versuch_id": v.id,
        "uebung_id": v.uebung_id,
        "versuchsnummer": v.versuchsnummer,
        "zeitpunkt": _als_utc(v.zeitpunkt).isoformat(),
        "aufgabe": {"id": snap["aufgabe_id"], "version_zum_zeitpunkt": v.aufgabe_version, "text": snap["text"],
                    "fragetyp": snap["fragetyp"], "optionen": snap["optionen"],
                    "loesung_text": [_optionstext_snap(snap, x) for x in snap["loesung"]]
                    if snap["fragetyp"] != "luecke" else snap["loesung"],
                    "erklaerung": snap["erklaerung"]},
        "antwort": {"gegeben": gegeben,
                    "gegeben_text": [_optionstext_snap(snap, x) for x in gegeben]
                    if snap["fragetyp"] != "luecke" else gegeben},
        "richtig": v.richtig, "punkte": float(v.punkte), "maximum": float(v.maximum),
        "prozent": bewertung.prozent(v.punkte, v.maximum),
        "hilfen": v.hilfen,
        "selbststaendig": not v.hilfen,
        "selbsteinschaetzung": v.selbsteinschaetzung,
        "quellen": _quellen_sicht(session, kontext, snap.get("abschnitt_ids", [])),
        "verlauf": [{"id": n.id, "rolle": n.rolle, "form": n.form, "text": n.text,
                     "quellen": n.quellen, "sicherheitsgrad": n.sicherheitsgrad,
                     "herkunft": n.herkunft, "zeitpunkt": _als_utc(n.zeitpunkt).isoformat()} for n in verlauf],
        "gespraech_moeglich": aktuell_verfuegbar,
        "gespraech_grund": grund,
    }


def _optionstext_snap(snap: dict, option_id: str) -> str:
    for o in snap.get("optionen") or []:
        if o.get("id") == option_id:
            return o.get("text", option_id)
    return str(option_id)


def _snapshot_verfuegbar(session, kontext: Kontext, snap: dict) -> tuple[bool, str | None]:
    """Für neue Erklärungen: alle Quellen des damaligen Stands müssen noch aktuell freigegeben sein."""
    for aid in snap.get("abschnitt_ids", []):
        ok, grund = abschnitt_aktuell_verwendbar(session, kontext, aid)
        if not ok:
            return False, grund
    return True, None


# ---------- Lernprofil ----------

def lernprofil(session, cfg: dict, kontext: Kontext, modul_id: str) -> list[dict]:
    """Lernprofil je Lernziel für die eigene Person (Lehrpersonen: nur aggregiert)."""
    modul = modul_im_mandanten(session, kontext, modul_id)
    rolle = modul_rolle(session, kontext, modul.id)
    if rolle == "studierende":
        konto_id = kontext.konto_id
    elif rolle in ("dozierende", "assistenz", "admin"):
        raise FachFehler("nur_aggregiert", "Lehrpersonen sehen Lernprofile nur aggregiert.", status=403)
    else:
        raise nicht_gefunden("Modul")
    pruefe_studierend(session, kontext, modul.id)

    schwelle = cfg["evidenz"]["schwelle_aufgaben"]
    widerspruch = cfg["evidenz"]["widerspruch_nach_falsch"]
    ziele = session.scalars(
        mandant_abfrage(Lernziel, kontext.lernorganisation_id)
        .join(Lektion, Lektion.id == Lernziel.lektion_id).where(Lektion.modul_id == modul.id)
        .order_by(Lektion.reihenfolge, Lernziel.reihenfolge)).all()
    versuche = session.scalars(mandant_abfrage(Versuch, kontext.lernorganisation_id).where(
        Versuch.konto_id == konto_id).order_by(Versuch.zeitpunkt)).all()
    ergebnis = []
    for z in ziele:
        eingaenge = [evidenz.Versuchseingang(aufgabe_id=v.aufgabe_id, punkte_voll=bool(v.richtig),
                                             hilfe_vorher=bool(v.hilfen), zeitpunkt=_als_utc(v.zeitpunkt))
                     for v in versuche if v.aufgabe_snapshot.get("lernziel_id") == z.id]
        lage = evidenz.evidenzlage(eingaenge, schwelle, widerspruch)
        ergebnis.append({"lernziel_id": z.id, "text": z.text, "handlungsstufe": z.handlungsstufe, **lage})
    return ergebnis


def lernprofil_aggregiert(session, kontext: Kontext, modul_id: str) -> dict:
    """Für Lehrpersonen: Zählungen ohne Personenbezug."""
    rolle = modul_rolle(session, kontext, modul_id)
    if rolle not in ("dozierende", "admin"):
        raise FachFehler("nicht_berechtigt", "Aggregierte Sicht nur für Lehrpersonen und Administration.", status=403)
    modul_im_mandanten(session, kontext, modul_id)
    uebungen = session.scalars(mandant_abfrage(Uebung, kontext.lernorganisation_id)
                               .where(Uebung.modul_id == modul_id)).all()
    anzahl_versuche = len(session.scalars(mandant_abfrage(Versuch, kontext.lernorganisation_id)
                                          .where(Versuch.uebung_id.in_([u.id for u in uebungen]))).all()) if uebungen else 0
    return {"modul_id": modul_id, "versuche": anzahl_versuche, "lernende": len({u.konto_id for u in uebungen})}
