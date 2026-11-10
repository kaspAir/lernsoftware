"""JSON-Schnittstelle unter /api/v1 (Spez. §13). Jede Anfrage erhält eine eigene Datenbanksitzung;
Fehler verwerfen die Sitzung vollständig.

Anmeldung: Sitzungscookie (120 Minuten ab Anmeldung, app/sitzung.py). Schreibende Anfragen verlangen
den Kopf `X-CSRF-Token`. Abgaben und Gesprächsfragen verlangen den Kopf `Idempotency-Key`
(8 bis 64 Zeichen), damit Wiederholungen derselben Anfrage keinen zweiten Eintrag erzeugen.
"""
import functools
import secrets

from flask import Blueprint, current_app, jsonify, request, session as websitzung

from .db import Basis  # noqa: F401
from .dienste import anmeldung, lernbegleiter, lernen, verwaltung
from .fehler import FachFehler, verboten
from .models import Konto
from .rechte import Kontext, lade_kontext
from .sitzung import sitzung_abgelaufen, sitzung_beginnt
from .sitzung_db import sitzung

blueprint = Blueprint("api", __name__)


def _json() -> dict:
    daten = request.get_json(silent=True)
    if daten is None:
        if request.method in ("POST", "PUT", "PATCH") and request.content_length:
            raise FachFehler("json_ungueltig", "Erwartet wird ein JSON-Objekt.", status=400)
        return {}
    if not isinstance(daten, dict):
        raise FachFehler("json_ungueltig", "Erwartet wird ein JSON-Objekt.", status=400)
    return daten


def _csrf_pruefen():
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        erwartet = websitzung.get("csrf")
        if not erwartet or request.headers.get("X-CSRF-Token") != erwartet:
            raise FachFehler("csrf_fehlt", "Sicherheitsprüfung fehlgeschlagen. Bitte neu anmelden.", status=403)


def _cfg():
    return current_app.config["LERNCFG"]


def sitzung_pruefen() -> None:
    """Gilt für Web und API: Ablauf nach 120 Minuten ab Anmeldung (Festlegung 1.1)."""
    if websitzung.get("konto_id") or websitzung.get("superadmin_id"):
        if sitzung_abgelaufen(websitzung.get("angemeldet_am"), _cfg()["sicherheit"]["sitzung_minuten"]):
            websitzung.clear()
            raise FachFehler("sitzung_abgelaufen", "Die Sitzung ist abgelaufen. Bitte erneut anmelden.", status=401)


def _kontext(s) -> Kontext:
    sitzung_pruefen()
    konto_id = websitzung.get("konto_id")
    org_id = websitzung.get("lernorganisation_id")
    if not konto_id or not org_id:
        raise FachFehler("nicht_angemeldet", "Bitte zuerst anmelden.", status=401)
    return lade_kontext(s, konto_id, org_id)


def _superadmin(s) -> str:
    sitzung_pruefen()
    konto_id = websitzung.get("superadmin_id")
    if not konto_id:
        raise FachFehler("nicht_angemeldet", "Bitte zuerst anmelden.", status=401)
    konto = s.get(Konto, konto_id)
    if konto is None or konto.status != "aktiv" or not konto.ist_superadmin:
        websitzung.clear()
        raise FachFehler("nicht_angemeldet", "Die Sitzung ist nicht mehr gültig.", status=401)
    return konto_id


def _schluessel() -> str:
    return request.headers.get("Idempotency-Key", "")


def endpunkt(funktion):
    """Umhüllt eine Dienstfunktion: CSRF-Prüfung, Datenbanksitzung, JSON-Antwort."""
    @functools.wraps(funktion)
    def huelle(*args, **kwargs):
        _csrf_pruefen()
        with sitzung(current_app) as s:
            ergebnis, status = funktion(s, *args, **kwargs)
        return jsonify(ergebnis), status
    return huelle


# ---------- Anmeldung und Zustand ----------

@blueprint.post("/auth/anmelden")
def anmelden_route():
    daten = _json()
    with sitzung(current_app) as s:
        ergebnis = anmeldung.anmelden(s, _cfg(), daten.get("kurzname"), daten.get("benutzername", ""),
                                      daten.get("passwort", ""))
    websitzung.clear()
    if ergebnis["superadmin"]:
        websitzung["superadmin_id"] = ergebnis["konto_id"]
    else:
        websitzung["konto_id"] = ergebnis["konto_id"]
        websitzung["lernorganisation_id"] = ergebnis["lernorganisation_id"]
    websitzung["angemeldet_am"] = sitzung_beginnt()
    websitzung["csrf"] = secrets.token_urlsafe(24)
    return jsonify({**ergebnis, "csrf": websitzung["csrf"],
                    "sitzung_endet_nach_minuten": _cfg()["sicherheit"]["sitzung_minuten"]}), 200


@blueprint.post("/auth/abmelden")
def abmelden_route():
    _csrf_pruefen()
    websitzung.clear()
    return jsonify({"status": "abgemeldet"}), 200


@blueprint.get("/modell")
def modell_info():
    m = current_app.config["MODELL"]
    return jsonify({"herkunft": m.herkunft, "modellname": m.modellname,
                    "anzeige": current_app.config["MODELL_ANZEIGE"]}), 200


# ---------- Super-Admin ----------

@blueprint.get("/superadmin/lernorganisationen")
@endpunkt
def sa_liste(s):
    sa = _superadmin(s)
    return verwaltung.lernorganisationen_register(s, sa), 200


@blueprint.post("/superadmin/lernorganisationen")
@endpunkt
def sa_anlegen(s):
    sa = _superadmin(s)
    d = _json()
    org = verwaltung.lernorganisation_anlegen(s, _cfg(), sa, d.get("name", ""), d.get("kurzname", ""),
                                              d.get("admin_benutzername", ""), d.get("admin_anzeigename", ""),
                                              d.get("admin_passwort", ""))
    return org, 201


# ---------- Verwaltung ----------

@blueprint.post("/konten")
@endpunkt
def konto_anlegen(s):
    k = _kontext(s)
    d = _json()
    return verwaltung.konto_fuer_organisation(s, k, d.get("benutzername", ""), d.get("anzeigename", ""),
                                              d.get("passwort", ""), _cfg(), d.get("rolle", "mitglied")), 201


@blueprint.get("/module")
@endpunkt
def module_liste(s):
    k = _kontext(s)
    return verwaltung.module_fuer_kontext(s, k), 200


@blueprint.post("/module")
@endpunkt
def modul_anlegen(s):
    k = _kontext(s)
    d = _json()
    return verwaltung.modul_anlegen(s, k, d.get("bezeichnung", ""), d.get("beschreibung", "")), 201


@blueprint.post("/module/<modul_id>/zuweisungen")
@endpunkt
def zuweisen(s, modul_id):
    k = _kontext(s)
    d = _json()
    return verwaltung.zuweisen(s, _cfg(), k, modul_id, d.get("konto_id", ""), d.get("rolle", ""),
                               bool(d.get("freigabe_delegiert", False))), 201


@blueprint.get("/module/<modul_id>/lektionen")
@endpunkt
def lektionen(s, modul_id):
    k = _kontext(s)
    return verwaltung.lektionen_des_moduls(s, k, modul_id), 200


@blueprint.post("/module/<modul_id>/lektionen")
@endpunkt
def lektion_anlegen(s, modul_id):
    k = _kontext(s)
    d = _json()
    return verwaltung.lektion_anlegen(s, k, modul_id, d.get("titel", ""), d.get("reihenfolge")), 201


@blueprint.post("/lektionen/<lektion_id>/lernziele")
@endpunkt
def lernziel_anlegen(s, lektion_id):
    k = _kontext(s)
    d = _json()
    return verwaltung.lernziel_anlegen(s, k, lektion_id, d.get("text", ""), d.get("handlungsstufe", "")), 201


@blueprint.post("/module/<modul_id>/unterlagen")
@endpunkt
def unterlage_hochladen(s, modul_id):
    k = _kontext(s)
    d = _json()
    return verwaltung.unterlage_hochladen(s, _cfg(), k, modul_id, d.get("lektion_id"), d.get("titel", ""),
                                          d.get("dateiname", ""), d.get("inhalt", "")), 201


@blueprint.get("/module/<modul_id>/unterlagen")
@endpunkt
def unterlagen_liste(s, modul_id):
    k = _kontext(s)
    return verwaltung.unterlagen_des_moduls(s, k, modul_id), 200


@blueprint.post("/unterlagen/<unterlage_id>/aenderung")
@endpunkt
def unterlage_aendern(s, unterlage_id):
    k = _kontext(s)
    d = _json()
    return verwaltung.unterlage_aendern(s, _cfg(), k, unterlage_id, d.get("inhalt", "")), 200


@blueprint.post("/unterlagen/<unterlage_id>/freigabe")
@endpunkt
def unterlage_freigabe(s, unterlage_id):
    from datetime import datetime
    k = _kontext(s)
    d = _json()
    frist = d.get("auflage_frist")
    frist_dt = datetime.fromisoformat(frist) if frist else None
    return verwaltung.unterlage_freigeben(s, _cfg(), k, unterlage_id, d.get("form", ""),
                                          d.get("auflage_verantwortlich"), frist_dt,
                                          d.get("begruendung")), 200


@blueprint.get("/unterlagen/<unterlage_id>/abschnitte")
@endpunkt
def unterlage_abschnitte(s, unterlage_id):
    k = _kontext(s)
    return verwaltung.unterlage_abschnitte(s, k, unterlage_id), 200


@blueprint.post("/module/<modul_id>/aufgaben")
@endpunkt
def aufgabe_anlegen(s, modul_id):
    k = _kontext(s)
    d = _json()
    return verwaltung.aufgabe_anlegen(
        s, _cfg(), k, d.get("lernziel_id", ""), d.get("aufgabe_text", ""), d.get("fragetyp", ""),
        d.get("optionen"), d.get("loesung", []), d.get("max_punkte", 1), d.get("erklaerung", ""),
        d.get("abschnitt_ids", []), d.get("hinweis"), d.get("beispiel"), int(d.get("denkschritte", 1))), 201


@blueprint.post("/aufgaben/<aufgabe_id>/fachlich-pruefen")
@endpunkt
def aufgabe_pruefen(s, aufgabe_id):
    k = _kontext(s)
    return verwaltung.aufgabe_fachlich_pruefen(s, k, aufgabe_id), 200


# ---------- Lernen ----------

@blueprint.post("/module/<modul_id>/uebungen")
@endpunkt
def uebung_erzeugen(s, modul_id):
    k = _kontext(s)
    d = _json()
    return lernen.uebung_erzeugen(s, _cfg(), k, modul_id, list(d.get("lektion_ids", []))), 201


@blueprint.get("/uebungen/<uebung_id>")
@endpunkt
def uebung_lesen(s, uebung_id):
    k = _kontext(s)
    return lernen.uebung_sicht(s, k, uebung_id), 200


@blueprint.post("/uebungen/<uebung_id>/hilfe")
@endpunkt
def hilfe(s, uebung_id):
    k = _kontext(s)
    d = _json()
    return lernen.hilfe_anfordern(s, _cfg(), k, uebung_id, d.get("aufgabe_id", ""), d.get("art", "")), 200


@blueprint.post("/uebungen/<uebung_id>/versuche")
@endpunkt
def versuch(s, uebung_id):
    k = _kontext(s)
    d = _json()
    ergebnis = lernen.versuch_abgeben(s, _cfg(), k, uebung_id, d.get("aufgabe_id", ""), d.get("gegeben"),
                                      d.get("selbsteinschaetzung"), _schluessel())
    return ergebnis, (200 if ergebnis.get("wiederholt") else 201)


@blueprint.get("/versuche/<versuch_id>")
@endpunkt
def versuch_lesen(s, versuch_id):
    k = _kontext(s)
    return lernen.versuch_sicht(s, k, versuch_id), 200


@blueprint.post("/versuche/<versuch_id>/gespraech")
@endpunkt
def gespraech(s, versuch_id):
    k = _kontext(s)
    d = _json()
    ergebnis = lernbegleiter.gespraech_fuehren(s, _cfg(), current_app.config["MODELL"], k, versuch_id,
                                               d.get("frage"), d.get("form", "erklaerung"), _schluessel())
    return ergebnis, (200 if ergebnis.get("wiederholt") else 201)


@blueprint.get("/abschnitte/<abschnitt_id>")
@endpunkt
def abschnitt(s, abschnitt_id):
    k = _kontext(s)
    return lernen.abschnitt_sicht(s, k, abschnitt_id), 200


@blueprint.get("/module/<modul_id>/lernprofil")
@endpunkt
def lernprofil(s, modul_id):
    k = _kontext(s)
    return lernen.lernprofil(s, _cfg(), k, modul_id), 200


@blueprint.get("/module/<modul_id>/lernprofil/aggregiert")
@endpunkt
def lernprofil_agg(s, modul_id):
    k = _kontext(s)
    return lernen.lernprofil_aggregiert(s, k, modul_id), 200
