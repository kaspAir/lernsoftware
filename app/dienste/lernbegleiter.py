"""Lernbegleiter: Rückfragen zu einem Versuch mit strenger Ausgabeprüfung (BS-01 bis BS-08, Spez. §10).

Ablauf einer Rückfrage:
1. Anfrage-Schlüssel prüfen; bei bekanntem Schlüssel wird der gespeicherte Stand zurückgegeben
   (kein zweites Modell, keine zweite Nachricht).
2. Frage speichern (Eindeutigkeit des Schlüssels greift hier).
3. Zulässigkeit prüfen: Alle Quellen des Versuchs müssen aktuell freigegeben sein (sonst keine neue
   Erklärung, der Verlauf bleibt erhalten).
4. Kontext begrenzt zusammenstellen (Aufgabe, Optionen, Lösung, Hilfen, Verlauf, Lernstand, Abschnitte).
5. Modellaufruf über den Adapter; jede Ausgabe wird vollständig geprüft (kern/modellpruefung.py).
6. Antwort oder klar gekennzeichnete Systemmeldung speichern; Nachweis mit Kennung bei Ablehnung.

Beweist: Keine Quelle außerhalb der Eingabe (NR-02); keine Bewertungssprache (BS-06); keine
ungeprüfte Ausgabe; kein Modellaufruf bei nicht mehr verwendbaren Quellen; Wiederholungen derselben
Frage erzeugen keinen zweiten Aufruf.
"""
import re

from sqlalchemy.exc import IntegrityError

from ..db import mandant_abfrage
from ..fehler import FachFehler, nicht_gefunden
from ..kern import evidenz
from ..kern.modellpruefung import FORMEN, AusgabeUngueltig, pruefe_modellausgabe
from ..models import Abschnitt, Nachricht, Uebung, Unterlage, Versuch, Lernziel
from ..modell.adapter import (ModellAufruf, ModellFehler, PseudonymisierungBlockiert)
from ..rechte import Kontext, pruefe_studierend
from .lernen import _optionstext_snap, _snapshot_verfuegbar, _als_utc
from .nachweis import schreibe_nachweis

SCHLUESSEL = re.compile(r"^[A-Za-z0-9_-]{8,64}$")

STANDARD_NICHT_BELEGT = ("In den freigegebenen Unterlagen finde ich dazu keine belegte Antwort. "
                         "Du kannst die Frage an die Lehrperson weiterleiten.")
STANDARD_NICHT_ERREICHBAR = "Der Lernbegleiter ist gerade nicht erreichbar. Deine Frage ist gespeichert."
STANDARD_BLOCKIERT = "Der Lernbegleiter braucht eine Entscheidung zu einer Fundstelle. Die Frage wurde nicht gesendet."
STANDARD_UNGEPRUEFT = "Die Antwort des Lernbegleiters konnte nicht sicher geprüft werden und wird nicht angezeigt."


def _schluessel(schluessel) -> str:
    if not isinstance(schluessel, str) or not SCHLUESSEL.match(schluessel):
        raise FachFehler("schluessel_ungueltig", "Der Anfrage-Schlüssel fehlt oder ist ungültig.", status=422)
    return schluessel


def _antwort_zu(session, kontext: Kontext, frage: Nachricht) -> Nachricht | None:
    return session.scalars(mandant_abfrage(Nachricht, kontext.lernorganisation_id).where(
        Nachricht.bezug_id == frage.id)).first()


def _darstellung(session, kontext: Kontext, frage: Nachricht, antwort: Nachricht | None, wiederholt: bool = False) -> dict:
    return {
        "frage_id": frage.id,
        "frage": frage.text,
        "form": frage.form,
        "antwort": None if antwort is None else {
            "id": antwort.id, "form": antwort.form, "text": antwort.text, "quellen": antwort.quellen,
            "sicherheitsgrad": antwort.sicherheitsgrad, "herkunft": antwort.herkunft,
            "annahmen": (antwort.herkunft or {}).get("annahmen", []),
            "luecke": (antwort.herkunft or {}).get("luecke"),
        },
        "wiederholt": wiederholt,
        "hinweis_wiederholung": "Diese Frage wurde bereits gestellt. Es wurde keine neue Antwort erzeugt."
        if wiederholt else None,
    }


def gespraech_fuehren(session, cfg: dict, adapter, kontext: Kontext, versuch_id: str,
                      frage: str | None, form: str, schluessel) -> dict:
    schluessel = _schluessel(schluessel)
    if form not in FORMEN:
        raise FachFehler("form_ungueltig", "Form: hinweis, rueckfrage, beispiel oder erklaerung.", status=422)
    frage_text = (frage or "").strip()
    max_frage = cfg["lernbegleiter"]["frage_max_zeichen"]
    if len(frage_text) > max_frage:
        raise FachFehler("frage_zu_lang", f"Die Frage darf höchstens {max_frage} Zeichen lang sein.", status=422,
                         felder={"frage": "zu lang"})
    if form == "rueckfrage" and not frage_text:
        raise FachFehler("frage_fehlt", "Bitte formuliere deine Rückfrage.", status=422, felder={"frage": "fehlt"})

    versuch = session.scalars(mandant_abfrage(Versuch, kontext.lernorganisation_id)
                              .where(Versuch.id == versuch_id)).first()
    if versuch is None or versuch.konto_id != kontext.konto_id:
        raise nicht_gefunden("Versuch")
    uebung = session.get(Uebung, versuch.uebung_id)
    pruefe_studierend(session, kontext, uebung.modul_id)

    # 1. Wiederholung derselben Frage: gespeicherten Stand zurückgeben, nichts neu erzeugen
    bekannt = session.scalars(mandant_abfrage(Nachricht, kontext.lernorganisation_id).where(
        Nachricht.konto_id == kontext.konto_id, Nachricht.anfrage_schluessel == schluessel)).first()
    if bekannt is not None:
        if bekannt.versuch_id != versuch.id:
            raise FachFehler("schluessel_wiederverwendet", "Dieser Anfrage-Schlüssel gehört zu einer anderen Frage.",
                             status=409)
        return _darstellung(session, kontext, bekannt, _antwort_zu(session, kontext, bekannt), wiederholt=True)

    # 2. Frage speichern; ein paralleler Doppelklick scheitert hier an der Eindeutigkeit
    frage_nachricht = Nachricht(
        lernorganisation_id=kontext.lernorganisation_id, konto_id=kontext.konto_id, versuch_id=versuch.id,
        rolle="frage", form=form, text=frage_text or "(Erklärung angefordert)",
        anfrage_schluessel=schluessel, herkunft={"erzeugt_durch": "mensch", "konto": kontext.konto_id})
    session.add(frage_nachricht)
    try:
        session.flush()
    except IntegrityError:
        session.rollback()
        bekannt = session.scalars(mandant_abfrage(Nachricht, kontext.lernorganisation_id).where(
            Nachricht.konto_id == kontext.konto_id, Nachricht.anfrage_schluessel == schluessel)).first()
        if bekannt is None:
            raise
        return _darstellung(session, kontext, bekannt, _antwort_zu(session, kontext, bekannt), wiederholt=True)

    snap = versuch.aufgabe_snapshot
    # 3. Zulässigkeit: nur mit aktuell verwendbaren Quellen
    zulaessig, grund = _snapshot_verfuegbar(session, kontext, snap)
    if not zulaessig:
        schreibe_nachweis(session, "erklaerung_nicht_zulaessig", kontext.lernorganisation_id, kontext.konto_id,
                          versuch.id, {"grund": grund})
        antwort = _system(session, kontext, versuch, frage_nachricht, "nicht_erreichbar",
                          f"Zu dieser Aufgabe kann derzeit keine neue Erklärung erstellt werden: {grund} "
                          "Dein bisheriger Verlauf bleibt erhalten.", {"erzeugt_durch": "kern", "grund": grund})
        return _darstellung(session, kontext, frage_nachricht, antwort)

    # 4./5. Kontext und Modellaufruf
    auftrag = _kontext_bauen(session, cfg, kontext, versuch, frage_text, form)
    erlaubte = {a["id"] for a in auftrag["abschnitte"]}
    herkunft_modell = {"erzeugt_durch": f"system:modell:{adapter.modellname}", "herkunft": adapter.herkunft}
    antwort_daten = None
    grund_fehler = None
    for versuchsnummer in range(cfg["lernbegleiter"]["schema_wiederholungen"] + 1):
        try:
            rohdaten = adapter.aufrufen(ModellAufruf(auftrag, mandant=kontext.lernorganisation_id,
                                                     sitzung="ls-" + kontext.konto_id[:8]))
        except PseudonymisierungBlockiert:
            schreibe_nachweis(session, "pseudonymisierung_blockiert", kontext.lernorganisation_id,
                              kontext.konto_id, versuch.id, {"versuch": versuch.id})
            antwort = _system(session, kontext, versuch, frage_nachricht, "blockiert", STANDARD_BLOCKIERT,
                              {"erzeugt_durch": "system", "grund": "pseudonymisierung_blockiert"})
            return _darstellung(session, kontext, frage_nachricht, antwort)
        except ModellFehler as exc:
            schreibe_nachweis(session, "modell_nicht_erreichbar", kontext.lernorganisation_id,
                              kontext.konto_id, versuch.id, {"grund": str(exc)})
            antwort = _system(session, kontext, versuch, frage_nachricht, "nicht_erreichbar",
                              STANDARD_NICHT_ERREICHBAR, {"erzeugt_durch": "system", "grund": "nicht_erreichbar"})
            return _darstellung(session, kontext, frage_nachricht, antwort)
        try:
            antwort_daten = pruefe_modellausgabe(rohdaten, erlaubte, cfg["lernbegleiter"]["verbotene_muster"])
            break
        except AusgabeUngueltig as exc:
            grund_fehler = exc
            antwort_daten = None
            schreibe_nachweis(session, "modellausgabe_abgelehnt", kontext.lernorganisation_id, kontext.konto_id,
                              versuch.id, {"grund": exc.grund, "kategorie": exc.kennung, "versuch": versuchsnummer},
                              kennung="NR-02" if exc.kennung == "quelle" else ("BS-06" if exc.kennung == "bewertung" else None))
            if exc.kennung in ("quelle", "bewertung"):
                break  # keine Wiederholung bei inhaltlichen Verstössen

    if antwort_daten is None:
        text = STANDARD_NICHT_BELEGT if grund_fehler and grund_fehler.kennung in ("quelle", "bewertung") \
            else STANDARD_UNGEPRUEFT
        antwort = _system(session, kontext, versuch, frage_nachricht, "abgelehnt", text,
                          {"erzeugt_durch": "kern", "grund": grund_fehler.kennung if grund_fehler else "schema"})
        return _darstellung(session, kontext, frage_nachricht, antwort)

    quellen = _quellen_anreichern(session, kontext, antwort_daten["quellen"])
    if not quellen and not antwort_daten["luecke"]:
        # Ohne Quelle keine Aussage: die Lücke wird benannt (BS-05)
        antwort_daten["text"] = STANDARD_NICHT_BELEGT
        antwort_daten["luecke"] = "Keine belegende Quelle in den freigegebenen Abschnitten."
        antwort_daten["sicherheitsgrad"] = "unbestaetigt"
    annahmen = antwort_daten["annahmen"]
    if antwort_daten["sicherheitsgrad"] != "sicher" and not annahmen:
        annahmen = ["Der Sicherheitsgrad ist nicht «sicher»; die Annahmen sind hier nicht angegeben."]  # BS-04
    herkunft = {**herkunft_modell, "annahmen": annahmen, "luecke": antwort_daten["luecke"]}
    antwort_nachricht = Nachricht(
        lernorganisation_id=kontext.lernorganisation_id, konto_id=kontext.konto_id, versuch_id=versuch.id,
        rolle="lernbegleiter", form=antwort_daten["form"], text=antwort_daten["text"], quellen=quellen,
        sicherheitsgrad=antwort_daten["sicherheitsgrad"], herkunft=herkunft, bezug_id=frage_nachricht.id)
    session.add(antwort_nachricht)
    schreibe_nachweis(session, "modellaufruf", kontext.lernorganisation_id, kontext.konto_id, versuch.id,
                      {"modell": adapter.modellname, "herkunft": adapter.herkunft, "form": antwort_daten["form"],
                       "quellen": len(quellen), "frage_id": frage_nachricht.id})
    session.flush()
    return _darstellung(session, kontext, frage_nachricht, antwort_nachricht)


def _system(session, kontext: Kontext, versuch: Versuch, frage: Nachricht, form: str, text: str,
            herkunft: dict) -> Nachricht:
    antwort = Nachricht(lernorganisation_id=kontext.lernorganisation_id, konto_id=kontext.konto_id,
                        versuch_id=versuch.id, rolle="system", form=form, text=text, quellen=[],
                        herkunft=herkunft, bezug_id=frage.id)
    session.add(antwort)
    session.flush()
    return antwort


def _kontext_bauen(session, cfg: dict, kontext: Kontext, versuch: Versuch, frage_text: str, form: str) -> dict:
    """Begrenzter, nachvollziehbarer Kontext für das Modell (Inkrement 1.1, Punkt 5)."""
    snap = versuch.aufgabe_snapshot
    max_zeichen = cfg["lernbegleiter"]["kontext_max_zeichen"]
    optionen = [{"id": o["id"], "text": o.get("text", o["id"])} for o in snap.get("optionen") or []]
    gegeben = versuch.gegeben if isinstance(versuch.gegeben, list) else [versuch.gegeben]
    if snap["fragetyp"] == "luecke":
        gegeben_text, loesung_text = str(versuch.gegeben), list(snap["loesung"])
    else:
        gegeben_text = [_optionstext_snap(snap, x) for x in gegeben]
        loesung_text = [_optionstext_snap(snap, x) for x in snap["loesung"]]

    abschnitte = []
    for aid in snap.get("abschnitt_ids", []):
        a = session.scalars(mandant_abfrage(Abschnitt, kontext.lernorganisation_id).where(Abschnitt.id == aid)).first()
        if a is not None:
            abschnitte.append({"id": a.id, "text": a.text[:1200]})

    verlauf_rows = session.scalars(mandant_abfrage(Nachricht, kontext.lernorganisation_id).where(
        Nachricht.versuch_id == versuch.id, Nachricht.rolle.in_(("frage", "lernbegleiter"))
    ).order_by(Nachricht.zeitpunkt.desc(), Nachricht.id.desc())).all()
    verlauf = [{"rolle": n.rolle, "form": n.form, "text": n.text[:400]}
               for n in reversed(verlauf_rows[: cfg["lernbegleiter"]["verlauf_max"]])]

    hilfen = [h.get("art") for h in versuch.hilfen]
    lernstand = _lernstand_fuer_lernziel(session, cfg, kontext, versuch.konto_id, snap.get("lernziel_id"))

    auftrag = {
        "form": form,
        "frage": frage_text or "Erkläre das Ergebnis dieser Aufgabe.",
        "aufgabe": {"text": snap["text"], "version_zum_zeitpunkt": versuch.aufgabe_version,
                    "fragetyp": snap["fragetyp"], "optionen": optionen},
        "antwort": {"gegeben": gegeben_text, "richtig": versuch.richtig,
                    "punkte": float(versuch.punkte), "maximum": float(versuch.maximum)},
        "loesung": {"richtig": loesung_text, "begruendung": snap["erklaerung"]},
        "hilfen_verwendet": hilfen,
        "verlauf": verlauf,
        "lernstand": lernstand,
        "abschnitte": abschnitte,
        "lernziel_ids": [snap["lernziel_id"]] if snap.get("lernziel_id") else [],
        "pseudonym": "Lernende/r",
    }
    # Obergrenze: zuerst den Verlauf kürzen, dann die Abschnitte; nichts wird stillschweigend abgeschnitten
    while len(str(auftrag)) > max_zeichen and auftrag["verlauf"]:
        auftrag["verlauf"] = auftrag["verlauf"][1:]
    auftrag["kontext_gekuerzt"] = len(str(auftrag)) > max_zeichen
    return auftrag


def _lernstand_fuer_lernziel(session, cfg: dict, kontext: Kontext, konto_id: str, lernziel_id) -> dict | None:
    if not lernziel_id:
        return None
    versuche = session.scalars(mandant_abfrage(Versuch, kontext.lernorganisation_id).where(
        Versuch.konto_id == konto_id).order_by(Versuch.zeitpunkt)).all()
    eingaenge = [evidenz.Versuchseingang(aufgabe_id=v.aufgabe_id, punkte_voll=bool(v.richtig),
                                         hilfe_vorher=bool(v.hilfen), zeitpunkt=_als_utc(v.zeitpunkt))
                 for v in versuche if v.aufgabe_snapshot.get("lernziel_id") == lernziel_id]
    lage = evidenz.evidenzlage(eingaenge, cfg["evidenz"]["schwelle_aufgaben"], cfg["evidenz"]["widerspruch_nach_falsch"])
    return {"evidenzlage": lage["evidenzlage"], "selbststaendig_aufgaben": lage["selbststaendig_aufgaben"]}


def _quellen_anreichern(session, kontext: Kontext, quellen: list[dict]) -> list[dict]:
    ausgabe = []
    for q in quellen:
        a = session.scalars(mandant_abfrage(Abschnitt, kontext.lernorganisation_id)
                            .where(Abschnitt.id == q["abschnitt_id"])).first()
        u = session.get(Unterlage, a.unterlage_id) if a else None
        ausgabe.append({"abschnitt_id": q["abschnitt_id"], "unterlage": u.titel if u else None,
                        "version": a.unterlage_version if a else None,
                        "position": a.position if a else None,
                        "aussage": q.get("aussage", ""), "fachlich": "ungeprueft"})
    return ausgabe
