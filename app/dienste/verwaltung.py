"""Verwaltung: Plattform, Konten, Module, Lektionen, Lernziele, Unterlagen, Aufgaben.

Jede Funktion erhält einen Kontext (Konto + Lernorganisation) und prüft Rechte selbst
(rechte.py). Mandantenbezogene Abfragen laufen über `mandant_abfrage`.
"""
import re
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import select

from ..db import mandant_abfrage
from ..fehler import FachFehler, nicht_gefunden, verboten
from ..kern.abschnitte import segmentiere
from ..kern.bewertung import normalisiere_text
from ..models import (Abschnitt, Aufgabe, Konto, Lektion, Lernorganisation, Lernziel, Mitgliedschaft,
                      Modul, Modulzuweisung, Unterlage, UnterlageVersion, jetzt)
from ..rechte import (Kontext, darf_freigeben, modul_im_mandanten, modul_rolle, pruefe_freigabe,
                      pruefe_modulzugriff, pruefe_verwaltung)
from ..sicherheit import hashe_passwort
from .nachweis import schreibe_nachweis

KURZNAME = re.compile(r"^[a-z0-9-]{3,32}$")
BENUTZERNAME = re.compile(r"^[a-z0-9._-]{3,64}$")
ZUWEISBAR = ("dozierende", "assistenz", "studierende")
HANDLUNGSSTUFEN = ("wiedergeben", "anwenden", "analysieren", "beurteilen_transfer")
FRAGETYPEN = ("single_choice", "multiple_choice", "luecke")
FREIGABEFORMEN = ("freigegeben", "freigegeben_unter_auflage", "nicht_freigebbar")
FREIGEGEBEN = ("freigegeben", "freigegeben_unter_auflage")


def _validierung(code: str, nachricht: str, felder: dict | None = None) -> FachFehler:
    return FachFehler(code, nachricht, status=422, felder=felder)


# ---------- Plattform (Super-Admin) ----------

def lernorganisation_anlegen(session, cfg: dict, superadmin_id: str, name: str, kurzname: str,
                             admin_benutzer: str, admin_anzeige: str, admin_passwort: str) -> dict:
    sa = session.get(Konto, superadmin_id)
    if sa is None or not sa.ist_superadmin:
        raise verboten("Nur der Super-Admin legt Lernorganisationen an.")
    if not KURZNAME.match(kurzname):
        raise _validierung("kurzname_ungueltig", "Kurzname: 3–32 Zeichen, Kleinbuchstaben, Ziffern, Bindestrich.")
    if session.scalars(select(Lernorganisation).where(Lernorganisation.kurzname == kurzname)).first():
        raise _validierung("kurzname_belegt", "Dieser Kurzname ist bereits vergeben.")
    org = Lernorganisation(name=name.strip(), kurzname=kurzname, status="aktiv")
    session.add(org)
    session.flush()
    admin = konto_anlegen_oder_verknuepfen(session, cfg, org.id, admin_benutzer, admin_anzeige,
                                           admin_passwort, rolle="admin")
    schreibe_nachweis(session, "lernorganisation_angelegt", org.id, superadmin_id, org.id,
                      {"kurzname": kurzname, "erstadministration": admin.benutzername})
    return {"id": org.id, "name": org.name, "kurzname": org.kurzname, "status": org.status}


def lernorganisationen_register(session, superadmin_id: str) -> list[dict]:
    """Registrierungsfelder aller Organisationen (PL-02, B-01). Keine Inhalte."""
    sa = session.get(Konto, superadmin_id)
    if sa is None or not sa.ist_superadmin:
        raise verboten("Nur der Super-Admin sieht das Plattformregister.")
    zeilen = session.scalars(select(Lernorganisation).order_by(Lernorganisation.kurzname)).all()
    return [{"id": z.id, "name": z.name, "kurzname": z.kurzname, "status": z.status,
             "erstellt_am": z.erstellt_am.isoformat() if z.erstellt_am else None} for z in zeilen]


# ---------- Konten und Mitgliedschaften ----------

def konto_anlegen_oder_verknuepfen(session, cfg: dict, lernorganisation_id: str, benutzername: str,
                                   anzeigename: str, passwort: str | None, rolle: str) -> Konto:
    """Legt ein Konto an oder verknüpft ein bestehendes (BE-05). Passwort eines bestehenden Kontos
    wird nie überschrieben."""
    if rolle not in ("admin", "mitglied"):
        raise _validierung("rolle_ungueltig", "Organisationsrolle: admin oder mitglied.")
    benutzername = benutzername.strip().lower()
    if not BENUTZERNAME.match(benutzername):
        raise _validierung("benutzername_ungueltig", "Benutzername: 3–64 Zeichen, Kleinbuchstaben, Ziffern, . _ -")
    konto = session.scalars(select(Konto).where(Konto.benutzername == benutzername)).first()
    if konto is None:
        if not passwort:
            raise _validierung("passwort_fehlt", "Für ein neues Konto ist ein Passwort nötig.")
        konto = Konto(benutzername=benutzername, anzeigename=anzeigename.strip(),
                      passwort_hash=hashe_passwort(passwort, cfg), status="aktiv")
        session.add(konto)
        session.flush()
    _mitgliedschaft_sicherstellen(session, lernorganisation_id, konto.id, rolle)
    return konto


def _mitgliedschaft_sicherstellen(session, lernorganisation_id: str, konto_id: str, rolle: str) -> None:
    vorhanden = session.scalars(
        select(Mitgliedschaft).where(Mitgliedschaft.lernorganisation_id == lernorganisation_id,
                                     Mitgliedschaft.konto_id == konto_id,
                                     Mitgliedschaft.rolle == rolle)
    ).first()
    if vorhanden is None:
        session.add(Mitgliedschaft(lernorganisation_id=lernorganisation_id, konto_id=konto_id, rolle=rolle))


def konto_fuer_organisation(session, kontext: Kontext, benutzername: str, anzeigename: str,
                            passwort: str, cfg: dict, rolle: str = "mitglied") -> dict:
    if kontext.org_rolle != "admin":
        raise verboten("Nur die Administration legt Konten an.")
    konto = konto_anlegen_oder_verknuepfen(session, cfg, kontext.lernorganisation_id, benutzername,
                                           anzeigename, passwort, rolle)
    schreibe_nachweis(session, "konto_angelegt", kontext.lernorganisation_id, kontext.konto_id,
                      konto.id, {"benutzername": konto.benutzername})
    return {"id": konto.id, "benutzername": konto.benutzername, "anzeigename": konto.anzeigename}


# ---------- Module und Zuweisungen ----------

def modul_anlegen(session, kontext: Kontext, bezeichnung: str, beschreibung: str = "") -> dict:
    if kontext.org_rolle != "admin":
        raise verboten("Nur die Administration legt Module an.")
    if not bezeichnung.strip():
        raise _validierung("bezeichnung_fehlt", "Modul braucht eine Bezeichnung.")
    modul = Modul(lernorganisation_id=kontext.lernorganisation_id, bezeichnung=bezeichnung.strip(),
                  beschreibung=beschreibung, status="aktiv")
    session.add(modul)
    session.flush()
    schreibe_nachweis(session, "modul_angelegt", kontext.lernorganisation_id, kontext.konto_id, modul.id,
                      {"bezeichnung": modul.bezeichnung})
    return {"id": modul.id, "bezeichnung": modul.bezeichnung}


def zuweisen(session, cfg: dict, kontext: Kontext, modul_id: str, konto_id: str, rolle: str,
             freigabe_delegiert: bool = False) -> dict:
    if kontext.org_rolle != "admin":
        raise verboten("Nur die Administration weist Personen zu.")
    modul = modul_im_mandanten(session, kontext, modul_id)
    if rolle not in ZUWEISBAR:
        raise _validierung("rolle_ungueltig", "Modulrolle: dozierende, assistenz oder studierende.")
    if freigabe_delegiert and rolle != "assistenz":
        raise _validierung("delegation_ungueltig", "Freigabe kann nur an Assistenz delegiert werden (D-03).")
    konto = session.get(Konto, konto_id)
    if konto is None:
        raise nicht_gefunden("Konto")
    _mitgliedschaft_sicherstellen(session, kontext.lernorganisation_id, konto_id, "mitglied")
    # Regel (Inkrement 1.1): Je Konto und Modul gibt es genau eine Rolle. Eine neue Zuweisung
    # ersetzt die bisherige; der Wechsel wird im Nachweis mit der alten Rolle festgehalten.
    z = session.scalars(select(Modulzuweisung).where(Modulzuweisung.modul_id == modul.id,
                                                     Modulzuweisung.konto_id == konto_id)).first()
    vorher = None
    if z is None:
        z = Modulzuweisung(lernorganisation_id=kontext.lernorganisation_id, modul_id=modul.id,
                           konto_id=konto_id, rolle=rolle, freigabe_delegiert=freigabe_delegiert)
        session.add(z)
    else:
        vorher = {"rolle": z.rolle, "freigabe_delegiert": z.freigabe_delegiert}
        z.rolle = rolle
        z.freigabe_delegiert = freigabe_delegiert
    session.flush()
    schreibe_nachweis(session, "zuweisung", kontext.lernorganisation_id, kontext.konto_id, modul.id,
                      {"konto": konto.benutzername, "rolle": rolle, "freigabe_delegiert": freigabe_delegiert,
                       "vorher": vorher})
    return {"modul_id": modul.id, "konto": konto.benutzername, "rolle": rolle,
            "freigabe_delegiert": freigabe_delegiert}


def module_fuer_kontext(session, kontext: Kontext) -> list[dict]:
    """Module, in denen das Konto eine Rolle hat (MO-03, MO-04). Admins sehen alle Module."""
    alle = session.scalars(mandant_abfrage(Modul, kontext.lernorganisation_id).order_by(Modul.bezeichnung)).all()
    ergebnis = []
    for m in alle:
        rolle = modul_rolle(session, kontext, m.id)
        if rolle is None:
            continue
        ergebnis.append({"id": m.id, "bezeichnung": m.bezeichnung, "rolle": rolle})
    return ergebnis


# ---------- Lektionen und Lernziele ----------

def lektion_anlegen(session, kontext: Kontext, modul_id: str, titel: str, reihenfolge: int | None = None) -> dict:
    pruefe_verwaltung(session, kontext, modul_id)
    if not titel.strip():
        raise _validierung("titel_fehlt", "Lektion braucht einen Titel.")
    if reihenfolge is None:
        vorhandene = session.scalars(mandant_abfrage(Lektion, kontext.lernorganisation_id)
                                     .where(Lektion.modul_id == modul_id)).all()
        reihenfolge = len(vorhandene) + 1
    lektion = Lektion(lernorganisation_id=kontext.lernorganisation_id, modul_id=modul_id,
                      titel=titel.strip(), reihenfolge=reihenfolge, status="aktiv")
    session.add(lektion)
    session.flush()
    schreibe_nachweis(session, "lektion_angelegt", kontext.lernorganisation_id, kontext.konto_id, lektion.id,
                      {"titel": lektion.titel})
    return {"id": lektion.id, "titel": lektion.titel, "reihenfolge": lektion.reihenfolge}


def lernziel_anlegen(session, kontext: Kontext, lektion_id: str, text: str, handlungsstufe: str) -> dict:
    lektion = session.scalars(mandant_abfrage(Lektion, kontext.lernorganisation_id)
                              .where(Lektion.id == lektion_id)).first()
    if lektion is None:
        raise nicht_gefunden("Lektion")
    pruefe_verwaltung(session, kontext, lektion.modul_id)
    if handlungsstufe not in HANDLUNGSSTUFEN:
        raise _validierung("handlungsstufe_ungueltig", "Handlungsstufe: " + ", ".join(HANDLUNGSSTUFEN) + ".")
    if len(text.strip()) < 5:
        raise _validierung("text_zu_kurz", "Lernziel braucht einen Text.")
    ziel = Lernziel(lernorganisation_id=kontext.lernorganisation_id, lektion_id=lektion_id,
                    text=text.strip(), handlungsstufe=handlungsstufe)
    session.add(ziel)
    session.flush()
    return {"id": ziel.id, "text": ziel.text, "handlungsstufe": ziel.handlungsstufe}


def lektionen_des_moduls(session, kontext: Kontext, modul_id: str) -> list[dict]:
    pruefe_modulzugriff(session, kontext, modul_id)
    lektionen = session.scalars(mandant_abfrage(Lektion, kontext.lernorganisation_id)
                                .where(Lektion.modul_id == modul_id, Lektion.status == "aktiv")
                                .order_by(Lektion.reihenfolge)).all()
    ergebnis = []
    for l in lektionen:
        ziele = session.scalars(mandant_abfrage(Lernziel, kontext.lernorganisation_id)
                                .where(Lernziel.lektion_id == l.id).order_by(Lernziel.reihenfolge)).all()
        ergebnis.append({"id": l.id, "titel": l.titel, "reihenfolge": l.reihenfolge,
                         "lernziele": [{"id": z.id, "text": z.text, "handlungsstufe": z.handlungsstufe} for z in ziele]})
    return ergebnis


# ---------- Unterlagen ----------

def unterlage_hochladen(session, cfg: dict, kontext: Kontext, modul_id: str, lektion_id: str | None,
                        titel: str, dateiname: str, inhalt_text: str) -> dict:
    pruefe_verwaltung(session, kontext, modul_id)
    endung = "." + dateiname.rsplit(".", 1)[-1].lower() if "." in dateiname else ""
    if endung not in cfg["unterlagen"]["erlaubte_endungen"]:
        raise _validierung("dateityp_unzulaessig", "Inkrement 1 unterstützt nur .txt und .md.")
    if len(inhalt_text.encode("utf-8")) > cfg["unterlagen"]["max_bytes_text"]:
        raise _validierung("datei_zu_gross", "Datei überschreitet die zulässige Größe.")
    if "\x00" in inhalt_text:
        raise _validierung("kein_text", "Datei enthält Binärdaten und ist kein Text.")
    if not inhalt_text.strip():
        raise _validierung("kein_text", "Die Unterlage ist leer.")
    if lektion_id is not None:
        lektion = session.scalars(mandant_abfrage(Lektion, kontext.lernorganisation_id)
                                  .where(Lektion.id == lektion_id, Lektion.modul_id == modul_id)).first()
        if lektion is None:
            raise nicht_gefunden("Lektion")
    u = Unterlage(lernorganisation_id=kontext.lernorganisation_id, modul_id=modul_id, lektion_id=lektion_id,
                  titel=titel.strip() or dateiname, dateiname=re.sub(r"[^\w.\- ]", "_", dateiname),
                  status="extrahiert", hochgeladen_von=kontext.konto_id, version=1)
    session.add(u)
    session.flush()
    _fassung_und_abschnitte(session, cfg, kontext, u, inhalt_text)
    u.status = "entwurf"
    schreibe_nachweis(session, "unterlage_hochgeladen", kontext.lernorganisation_id, kontext.konto_id, u.id,
                      {"dateiname": u.dateiname, "version": u.version})
    return _unterlage_sicht(session, kontext, u)


def _fassung_und_abschnitte(session, cfg: dict, kontext: Kontext, u: Unterlage, inhalt_text: str) -> None:
    """Schreibt die aktuelle Fassung (u.version) und ihre Abschnitte. Ältere Fassungen bleiben erhalten."""
    session.add(UnterlageVersion(lernorganisation_id=kontext.lernorganisation_id, unterlage_id=u.id,
                                 nummer=u.version, inhalt_text=inhalt_text))
    u_cfg = cfg["unterlagen"]
    for position, text in enumerate(segmentiere(inhalt_text, u_cfg["abschnitt_min_zeichen"],
                                                u_cfg["abschnitt_max_zeichen"]), start=1):
        session.add(Abschnitt(lernorganisation_id=kontext.lernorganisation_id, unterlage_id=u.id,
                              unterlage_version=u.version, position=position, text=text))
    session.flush()


def unterlage_aendern(session, cfg: dict, kontext: Kontext, unterlage_id: str, neuer_inhalt: str) -> dict:
    u = _unterlage_im_mandanten(session, kontext, unterlage_id)
    pruefe_verwaltung(session, kontext, u.modul_id)
    if not neuer_inhalt.strip():
        raise _validierung("kein_text", "Die neue Fassung ist leer.")
    vorher = u.status
    u.version = u.version + 1
    _fassung_und_abschnitte(session, cfg, kontext, u, neuer_inhalt)
    if vorher in FREIGEGEBEN:
        # RA-05 / NR-05: Inhaltsänderung macht die Freigabe ungültig, im selben Vorgang.
        u.status = "in_pruefung"
    elif vorher == "nicht_freigebbar":
        # Spez. §4.1: Eine neue Fassung einer abgelehnten Unterlage kehrt in den Entwurf zurück.
        u.status = "entwurf"
    schreibe_nachweis(session, "unterlage_geaendert", kontext.lernorganisation_id, kontext.konto_id, u.id,
                      {"von_status": vorher, "neuer_status": u.status, "version": u.version},
                      kennung="RA-05" if vorher in FREIGEGEBEN else None)
    session.flush()
    return _unterlage_sicht(session, kontext, u)


def unterlage_freigeben(session, cfg: dict, kontext: Kontext, unterlage_id: str, form: str,
                        auflage_verantwortlich: str | None = None, auflage_frist: datetime | None = None,
                        begruendung: str | None = None) -> dict:
    u = _unterlage_im_mandanten(session, kontext, unterlage_id)
    pruefe_freigabe(session, kontext, u.modul_id)
    if form not in FREIGABEFORMEN:
        raise _validierung("freigabeform_ungueltig", "Freigabeform: " + ", ".join(FREIGABEFORMEN) + ".")
    if u.status not in ("entwurf", "in_pruefung", "nicht_freigebbar"):
        raise FachFehler("zustand_ungueltig", f"Aus dem Status «{u.status}» ist keine Freigabe möglich.", status=409)
    if form == "freigegeben_unter_auflage":
        if not auflage_verantwortlich or auflage_frist is None:
            raise _validierung("auflage_unvollstaendig", "Auflage braucht Verantwortliche und Frist (IN-08).")
        if _als_utc(auflage_frist) <= jetzt():
            raise _validierung("auflage_frist_vergangen", "Die Frist der Auflage muss in der Zukunft liegen.")
        u.auflage_verantwortlich = auflage_verantwortlich
        u.auflage_frist = _als_utc(auflage_frist)
    if form == "nicht_freigebbar" and not begruendung:
        raise _validierung("begruendung_fehlt", "Nicht freigebbar verlangt eine Begründung.")
    u.status = form
    u.freigabeform = form
    u.freigegeben_von = kontext.konto_id
    u.freigegeben_am = jetzt()
    schreibe_nachweis(session, "freigabe", kontext.lernorganisation_id, kontext.konto_id, u.id,
                      {"form": form, "version": u.version, "begruendung": begruendung,
                       "auflage_verantwortlich": u.auflage_verantwortlich,
                       "auflage_frist": u.auflage_frist.isoformat() if u.auflage_frist else None},
                      kennung="RA-05")
    session.flush()
    return _unterlage_sicht(session, kontext, u)


def unterlagen_des_moduls(session, kontext: Kontext, modul_id: str) -> list[dict]:
    pruefe_modulzugriff(session, kontext, modul_id)
    rollen = modul_rolle(session, kontext, modul_id)
    q = mandant_abfrage(Unterlage, kontext.lernorganisation_id).where(Unterlage.modul_id == modul_id)
    if rollen == "studierende":
        q = q.where(Unterlage.status.in_(FREIGEGEBEN))
    return [_unterlage_sicht(session, kontext, u) for u in session.scalars(q.order_by(Unterlage.titel)).all()]


def _unterlage_im_mandanten(session, kontext: Kontext, unterlage_id: str) -> Unterlage:
    u = session.scalars(mandant_abfrage(Unterlage, kontext.lernorganisation_id)
                        .where(Unterlage.id == unterlage_id)).first()
    if u is None:
        raise nicht_gefunden("Unterlage")
    return u


def _unterlage_sicht(session, kontext: Kontext, u: Unterlage) -> dict:
    rolle = modul_rolle(session, kontext, u.modul_id)
    sicht = {"id": u.id, "titel": u.titel, "modul_id": u.modul_id, "lektion_id": u.lektion_id,
             "version": u.version, "status": u.status, "freigabeform": u.freigabeform}
    if rolle in ("dozierende", "assistenz", "admin"):
        sicht["freigabe_darf_ich"] = darf_freigeben(session, kontext, u.modul_id)
    return sicht


def unterlage_abschnitte(session, kontext: Kontext, unterlage_id: str) -> list[dict]:
    """Abschnitte der aktuellen Fassung für Lehrpersonen (Prüfansicht)."""
    u = _unterlage_im_mandanten(session, kontext, unterlage_id)
    pruefe_verwaltung(session, kontext, u.modul_id)
    return [{"id": a.id, "position": a.position, "text": a.text}
            for a in session.scalars(mandant_abfrage(Abschnitt, kontext.lernorganisation_id)
                                     .where(Abschnitt.unterlage_id == u.id,
                                            Abschnitt.unterlage_version == u.version)
                                     .order_by(Abschnitt.position)).all()]


# ---------- Aufgaben ----------

def aufgabe_anlegen(session, cfg: dict, kontext: Kontext, lernziel_id: str, aufgabe_text: str,
                    fragetyp: str, optionen: list | None, loesung: list, max_punkte,
                    erklaerung: str, abschnitt_ids: list[str], hinweis: str | None = None,
                    beispiel: str | None = None, denkschritte: int = 1) -> dict:
    ziel = session.scalars(mandant_abfrage(Lernziel, kontext.lernorganisation_id)
                           .where(Lernziel.id == lernziel_id)).first()
    if ziel is None:
        raise nicht_gefunden("Lernziel")
    lektion = session.get(Lektion, ziel.lektion_id)
    pruefe_verwaltung(session, kontext, lektion.modul_id)
    _pruefe_aufgabenform(aufgabe_text, fragetyp, optionen, loesung, max_punkte, erklaerung)
    quellen = _pruefe_quellen(session, kontext, lektion.modul_id, abschnitt_ids)
    _pruefe_dublette(session, kontext, lektion.id, aufgabe_text)

    ist_lehrperson = darf_freigeben(session, kontext, lektion.modul_id)
    aufgabe = Aufgabe(
        lernorganisation_id=kontext.lernorganisation_id, modul_id=lektion.modul_id, lektion_id=lektion.id,
        lernziel_id=ziel.id, aufgabe_text=aufgabe_text.strip(), fragetyp=fragetyp,
        optionen=optionen or [], loesung=loesung, max_punkte=Decimal(str(max_punkte)),
        erklaerung=erklaerung.strip(), hinweis=(hinweis or None), beispiel=(beispiel or None),
        abschnitt_ids=abschnitt_ids, denkschritte=denkschritte,
        pruefstatus="fachlich_geprueft" if ist_lehrperson else "technisch_geprueft",
        fachlich_geprueft_von=kontext.konto_id if ist_lehrperson else None,
        erstellt_von=kontext.konto_id,
    )
    session.add(aufgabe)
    session.flush()
    schreibe_nachweis(session, "aufgabe_angelegt", kontext.lernorganisation_id, kontext.konto_id, aufgabe.id,
                      {"pruefstatus": aufgabe.pruefstatus, "quellen": [q["id"] for q in quellen]})
    return {"id": aufgabe.id, "pruefstatus": aufgabe.pruefstatus, "version": aufgabe.version}


def _pruefe_aufgabenform(text, fragetyp, optionen, loesung, max_punkte, erklaerung) -> None:
    if fragetyp not in FRAGETYPEN:
        raise _validierung("fragetyp_ungueltig", "Fragetyp (Inkrement 1): " + ", ".join(FRAGETYPEN) + ".")
    if not (10 <= len(text.strip()) <= 600):
        raise _validierung("text_laenge", "Aufgabentext: 10 bis 600 Zeichen.")
    if not erklaerung or not erklaerung.strip():
        raise _validierung("erklaerung_fehlt", "Jede Aufgabe braucht eine Lösungsbegründung.")
    try:
        if Decimal(str(max_punkte)) <= 0:
            raise ValueError
    except Exception as exc:
        raise _validierung("max_punkte_ungueltig", "max_punkte muss größer als 0 sein.") from exc
    if fragetyp in ("single_choice", "multiple_choice"):
        if not optionen or not (2 <= len(optionen) <= 6):
            raise _validierung("optionen_anzahl", "Auswahlaufgaben brauchen 2 bis 6 Optionen.")
        ids = [o.get("id") for o in optionen]
        if len(set(ids)) != len(ids) or not all(ids):
            raise _validierung("optionen_ids", "Optionen brauchen eindeutige IDs.")
        if not loesung or not set(loesung) <= set(ids):
            raise _validierung("loesung_ungueltig", "Die Lösung verweist auf unbekannte Optionen.")
        if fragetyp == "single_choice" and len(loesung) != 1:
            raise _validierung("loesung_ungueltig", "Single Choice braucht genau eine richtige Option.")
    else:
        if not loesung or not all(isinstance(t, str) and t.strip() for t in loesung):
            raise _validierung("loesung_ungueltig", "Lückentext braucht mindestens einen zulässigen Text.")


def _pruefe_quellen(session, kontext: Kontext, modul_id: str, abschnitt_ids: list[str]) -> list[dict]:
    """Technische Gültigkeit der Quellen (Spez. §3.5): existiert, Mandant, Modul, aktuelle Fassung, freigegeben."""
    if not abschnitt_ids:
        raise _validierung("quelle_fehlt", "Jede Aufgabe braucht mindestens eine Quelle (NR-02).")
    ergebnis = []
    for aid in abschnitt_ids:
        a = session.scalars(mandant_abfrage(Abschnitt, kontext.lernorganisation_id).where(Abschnitt.id == aid)).first()
        if a is None:
            raise _validierung("quelle_unbekannt", "Eine Quelle existiert nicht in dieser Lernorganisation.")
        u = session.get(Unterlage, a.unterlage_id)
        if u.modul_id != modul_id:
            raise _validierung("quelle_fremdes_modul", "Quellen müssen aus demselben Modul stammen.")
        if a.unterlage_version != u.version:
            raise _validierung("quelle_veraltet", "Quelle verweist auf eine ältere Fassung der Unterlage.")
        if u.status not in FREIGEGEBEN:
            raise _validierung("quelle_nicht_freigegeben", "Quelle ist nicht freigegeben (IN-06).")
        ergebnis.append({"id": a.id, "unterlage_id": u.id, "titel": u.titel, "version": a.unterlage_version,
                         "position": a.position})
    return ergebnis


def _pruefe_dublette(session, kontext: Kontext, lektion_id: str, aufgabe_text: str) -> None:
    ziel = normalisiere_text(aufgabe_text, {"kleinschreibung": True, "leerraum_zusammenfassen": True,
                                            "umlaute_vergleich": True})
    bestehende = session.scalars(mandant_abfrage(Aufgabe, kontext.lernorganisation_id)
                                 .where(Aufgabe.lektion_id == lektion_id)).all()
    for b in bestehende:
        if normalisiere_text(b.aufgabe_text, {"kleinschreibung": True, "leerraum_zusammenfassen": True,
                                              "umlaute_vergleich": True}) == ziel:
            raise _validierung("dublette", "Eine gleichlautende Aufgabe existiert bereits in dieser Lektion.")


def aufgabe_fachlich_pruefen(session, kontext: Kontext, aufgabe_id: str) -> dict:
    aufgabe = session.scalars(mandant_abfrage(Aufgabe, kontext.lernorganisation_id)
                              .where(Aufgabe.id == aufgabe_id)).first()
    if aufgabe is None:
        raise nicht_gefunden("Aufgabe")
    pruefe_freigabe(session, kontext, aufgabe.modul_id)
    aufgabe.pruefstatus = "fachlich_geprueft"
    aufgabe.fachlich_geprueft_von = kontext.konto_id
    schreibe_nachweis(session, "aufgabe_fachlich_geprueft", kontext.lernorganisation_id, kontext.konto_id,
                      aufgabe.id, {"version": aufgabe.version}, kennung="LE-09")
    session.flush()
    return {"id": aufgabe.id, "pruefstatus": aufgabe.pruefstatus}


def _als_utc(dt: datetime) -> datetime:
    from datetime import timezone
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)
