"""JSON-Schnittstelle unter /api/v1 (Spez. §13). Jede Anfrage erhält eine eigene Datenbanksitzung;
Fehler verwerfen die Sitzung vollständig (nichts Halbfertiges wird gespeichert).

Anmeldung: Sitzungscookie. Schreibende Anfragen verlangen den Kopf `X-CSRF-Token` aus der Anmeldung.
"""
import functools
import secrets
from contextlib import contextmanager
from datetime import datetime

from flask import Blueprint, current_app, jsonify, request, session as websitzung

from .db import Basis
from .dienste import anmeldung, lernbegleiter, lernen, verwaltung
from .fehler import FachFehler, nicht_gefunden, verboten
from .models import Konto
from .rechte import Kontext, lade_kontext

blueprint = Blueprint("api", __name__)


@contextmanager
def sitzung():
    s = current_app.config["SITZUNG"]()
    try:
        yield s
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


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


def _kontext(s) -> Kontext:
    konto_id = websitzung.get("konto_id")
    org_id = websitzung.get("lernorganisation_id")
    if not konto_id or not org_id:
        raise FachFehler("nicht_angemeldet", "Bitte zuerst anmelden.", status=401)
    return lade_kontext(s, konto_id, org_id)


def _superadmin(s) -> str:
    konto_id = websitzung.get("superadmin_id")
    if not konto_id:
        raise FachFehler("nicht_angemeldet", "Bitte zuerst anmelden.", status=401)
    konto = s.get(Konto, konto_id)
    if konto is None or not konto.ist_superadmin:
        raise verboten()
    return konto_id


def endpunkt(funktion):
    """Umhüllt eine Dienstfunktion: CSRF-Prüfung, Datenbanksitzung, JSON-Antwort."""
    @functools.wraps(funktion)
    def huelle(*args, **kwargs):
        _csrf_pruefen()
        with sitzung() as s:
            ergebnis, status = funktion(s, *args, **kwargs)
        return jsonify(ergebnis), status
    return huelle


def _cfg():
    return current_app.config["LERNCFG"]


# ---------- Anmeldung ----------

@blueprint.post("/auth/anmelden")
def anmelden_route():
    daten = _json()
    with sitzung() as s:
        ergebnis = anmeldung.anmelden(s, _cfg(), daten.get("kurzname"), daten.get("benutzername", ""),
                                      daten.get("passwort", ""))
    websitzung.clear()
    if ergebnis["superadmin"]:
        websitzung["superadmin_id"] = ergebnis["konto_id"]
    else:
        websitzung["konto_id"] = ergebnis["konto_id"]
        websitzung["lernorganisation_id"] = ergebnis["lernorganisation_id"]
    websitzung["csrf"] = secrets.token_urlsafe(24)
    return jsonify({**ergebnis, "csrf": websitzung["csrf"]}), 200


@blueprint.post("/auth/abmelden")
def abmelden_route():
    _csrf_pruefen()
    websitzung.clear()
    return jsonify({"status": "abgemeldet"}), 200


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


@blueprint.post("/uebungen/<uebung_id>/hilfe")
@endpunkt
def hilfe(s, uebung_id):
    k = _kontext(s)
    d = _json()
    return lernen.hilfe_anfordern(s, k, uebung_id, d.get("aufgabe_id", ""), d.get("art", "")), 200


@blueprint.post("/uebungen/<uebung_id>/versuche")
@endpunkt
def versuch(s, uebung_id):
    k = _kontext(s)
    d = _json()
    return lernen.versuch_abgeben(s, _cfg(), k, uebung_id, d.get("aufgabe_id", ""), d.get("gegeben"),
                                  d.get("selbsteinschaetzung")), 201


@blueprint.post("/versuche/<versuch_id>/gespraech")
@endpunkt
def gespraech(s, versuch_id):
    k = _kontext(s)
    d = _json()
    return lernbegleiter.gespraech_fuehren(s, _cfg(), current_app.config["MODELL"], k, versuch_id,
                                           d.get("frage"), d.get("form", "erklaerung")), 200


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
