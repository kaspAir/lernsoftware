"""Browser-Oberfläche für den Studierendenablauf (Inkrement 1.1).

Alle Zustände kommen aus der Datenbank: Übung, Hinweise, Versuch, Rückmeldung, Quellen und
Gespräch sind nach Neuladen und erneuter Anmeldung unverändert vorhanden (Punkt 5).
Schreibende Formulare tragen einen Anfrage-Schlüssel; Wiederholungen desselben Absendens
erzeugen keinen zweiten Eintrag (Punkt 3).
"""
import html
import secrets
import uuid

from flask import Blueprint, current_app, flash, redirect, render_template_string, request, url_for, session as websitzung

from .dienste import anmeldung, lernbegleiter, lernen, verwaltung
from .dienste.lernen import abschnitt_sicht, uebung_sicht, versuch_sicht
from .fehler import FachFehler
from .rechte import Kontext, lade_kontext
from .sitzung import sitzung_abgelaufen, sitzung_beginnt
from .sitzung_db import sitzung

blueprint = Blueprint("web", __name__)

SEITE = """<!doctype html>
<html lang="de-CH"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ titel }} · Lernsoftware</title>
<style>
body{font-family:system-ui,sans-serif;max-width:52rem;margin:1.5rem auto;padding:0 1rem;line-height:1.5;color:#1a1a1a}
h1{font-size:1.5rem} h2{font-size:1.15rem;margin-top:1.4rem}
.modus{background:#eef3f8;border:1px solid #1f4e79;padding:.35rem .7rem;margin-bottom:1rem;font-size:.9rem}
.hinweis{background:#fff4d6;border-left:4px solid #b78100;padding:.5rem .75rem;margin:.6rem 0}
.quelle{font-size:.92rem;border-left:3px solid #1f4e79;padding:.3rem .6rem;margin:.4rem 0}
.verwendbar-nein{color:#8a1c1c}
fieldset{margin:1rem 0;padding:.75rem;border:1px solid #bbb} button{padding:.4rem .9rem;margin:.2rem 0}
.fehler{color:#8a1c1c;font-weight:600} .badge{display:inline-block;font-size:.85rem;padding:.05rem .45rem;border:1px solid #555;border-radius:3px;margin-right:.3rem}
.verlauf p{margin:.3rem 0} .frage{background:#f5f5f5;padding:.4rem .6rem}
</style></head><body>
<main>
<div class="modus" role="status">{{ modus_text }}</div>
<h1>{{ titel }}</h1>
{% for m in get_flashed_messages() %}<p class="fehler" role="alert">{{ m }}</p>{% endfor %}
{{ inhalt|safe }}
</main></body></html>"""


def _seite(titel: str, inhalt: str):
    return render_template_string(SEITE, titel=titel, inhalt=inhalt,
                                  modus_text=current_app.config["MODELL_ANZEIGE"]["text"])


def _e(text) -> str:
    return html.escape("" if text is None else str(text))


def _csrf() -> str:
    return f'<input type="hidden" name="csrf" value="{_e(websitzung.get("csrf", ""))}">'


def _schluessel_feld() -> str:
    return f'<input type="hidden" name="schluessel" value="{uuid.uuid4().hex}">'


def _csrf_ok() -> bool:
    return bool(websitzung.get("csrf")) and request.form.get("csrf") == websitzung.get("csrf")


def _kontext(s) -> Kontext:
    if websitzung.get("konto_id") and sitzung_abgelaufen(websitzung.get("angemeldet_am"),
                                                        current_app.config["LERNCFG"]["sicherheit"]["sitzung_minuten"]):
        websitzung.clear()
        raise FachFehler("sitzung_abgelaufen", "Die Sitzung ist abgelaufen. Bitte erneut anmelden.", status=401)
    konto_id = websitzung.get("konto_id")
    org_id = websitzung.get("lernorganisation_id")
    if not konto_id or not org_id:
        raise FachFehler("nicht_angemeldet", "Bitte zuerst anmelden.", status=401)
    return lade_kontext(s, konto_id, org_id)


def _mit_kontext(funktion):
    """Führt eine Seite mit Datenbanksitzung und Kontext aus; Fehler werden freundlich umgeleitet."""
    try:
        with sitzung(current_app) as s:
            return funktion(s, _kontext(s))
    except FachFehler as exc:
        if exc.status == 401:
            websitzung.clear()
            flash(exc.nachricht)
            return redirect(url_for("web.anmelden"))
        flash(exc.nachricht)
        return None


@blueprint.get("/")
def start():
    return redirect(url_for("web.module") if websitzung.get("konto_id") else url_for("web.anmelden"))


@blueprint.route("/anmelden", methods=["GET", "POST"])
def anmelden():
    if request.method == "POST":
        try:
            with sitzung(current_app) as s:
                ergebnis = anmeldung.anmelden(s, current_app.config["LERNCFG"], request.form.get("kurzname"),
                                              request.form.get("benutzername", ""), request.form.get("passwort", ""))
            if ergebnis["superadmin"]:
                flash("Der Super-Admin meldet sich über die Schnittstelle an, nicht über diese Seite.")
                return redirect(url_for("web.anmelden"))
            websitzung.clear()
            websitzung["konto_id"] = ergebnis["konto_id"]
            websitzung["lernorganisation_id"] = ergebnis["lernorganisation_id"]
            websitzung["angemeldet_am"] = sitzung_beginnt()
            websitzung["csrf"] = secrets.token_urlsafe(24)
            return redirect(url_for("web.module"))
        except FachFehler as exc:
            flash(exc.nachricht)
    inhalt = """<form method="post" aria-label="Anmeldung">
    <p><label>Lernorganisation (Kurzname)<br><input name="kurzname" required autocomplete="organization"></label></p>
    <p><label>Benutzername<br><input name="benutzername" required autocomplete="username"></label></p>
    <p><label>Passwort<br><input name="passwort" type="password" required autocomplete="current-password"></label></p>
    <p><button type="submit">Anmelden</button></p></form>
    <p class="hinweis">Die Sitzung endet 120 Minuten nach der Anmeldung.</p>"""
    return _seite("Anmelden", inhalt)


@blueprint.get("/abmelden")
def abmelden():
    websitzung.clear()
    return redirect(url_for("web.anmelden"))


@blueprint.get("/module")
def module():
    ergebnis = _mit_kontext(lambda s, k: verwaltung.module_fuer_kontext(s, k))
    if not isinstance(ergebnis, list):
        return redirect(url_for("web.anmelden"))
    zeilen = "".join(f'<li><a href="{url_for("web.modul", modul_id=m["id"])}">{_e(m["bezeichnung"])}</a> '
                     f'<span class="badge">{_e(m["rolle"])}</span></li>' for m in ergebnis)
    inhalt = f"<ul>{zeilen or '<li>Dir sind noch keine Module zugewiesen.</li>'}</ul>" \
             f'<p><a href="{url_for("web.abmelden")}">Abmelden</a></p>'
    return _seite("Meine Module", inhalt)


@blueprint.get("/module/<modul_id>")
def modul(modul_id):
    lektionen = _mit_kontext(lambda s, k: verwaltung.lektionen_des_moduls(s, k, modul_id))
    if not isinstance(lektionen, list):
        return redirect(url_for("web.module"))
    boxen = "".join(
        f'<label><input type="checkbox" name="lektion_ids" value="{_e(l["id"])}"> '
        f'{_e(l["reihenfolge"])}. {_e(l["titel"])}</label><br>'
        + "".join(f'<small>· {_e(z["text"])} ({_e(z["handlungsstufe"])})</small><br>' for z in l["lernziele"])
        for l in lektionen)
    inhalt = f"""<form method="post" action="{url_for('web.uebung_starten', modul_id=modul_id)}">
    {_csrf()}<fieldset><legend>Lektionen wählen</legend>{boxen or 'Noch keine Lektionen.'}</fieldset>
    <p><button type="submit">Übung erzeugen</button></p></form>"""
    return _seite("Lektionen wählen", inhalt)


@blueprint.post("/module/<modul_id>/uebung")
def uebung_starten(modul_id):
    if not _csrf_ok():
        flash("Sicherheitsprüfung fehlgeschlagen. Bitte die Seite neu laden.")
        return redirect(url_for("web.module"))
    ids = request.form.getlist("lektion_ids")
    ergebnis = _mit_kontext(lambda s, k: lernen.uebung_erzeugen(s, current_app.config["LERNCFG"], k, modul_id, ids))
    if isinstance(ergebnis, dict):
        return redirect(url_for("web.uebung", uebung_id=ergebnis["id"]))
    return redirect(url_for("web.modul", modul_id=modul_id))


def _gegeben_aus_formular(s, k: Kontext, uebung_id: str, aufgabe_id: str):
    """Antwortwert nach dem Fragetyp der Aufgabe: Liste für Auswahl, Text für Lücke."""
    sicht = uebung_sicht(s, k, uebung_id)
    aufgabe = next((a for a in sicht["aufgaben"] if a["id"] == aufgabe_id), None)
    if aufgabe is None:
        raise FachFehler("nicht_gefunden", "Aufgabe nicht gefunden.", status=404)
    if aufgabe["fragetyp"] == "luecke":
        return request.form.get("gegeben", "")
    return request.form.getlist("gegeben")


@blueprint.get("/uebungen/<uebung_id>")
def uebung(uebung_id):
    def seite(s, k):
        sicht = uebung_sicht(s, k, uebung_id)
        teile = []
        for a in sicht["aufgaben"]:
            anker = f"aufgabe-{_e(a['id'])}"
            status = "KI-erzeugt, technisch geprüft. Nicht von einer Lehrperson geprüft." \
                if a["pruefstatus"] == "technisch_geprueft" else "Von Lehrperson geprüft."
            body = f'<p class="badge">{_e(status)}</p><p>{_e(a["text"])}</p>'
            if not a["verfuegbar"]:
                body += f'<p class="hinweis">Diese Aufgabe ist derzeit nicht verfügbar: {_e(a["nicht_verfuegbar_grund"])}</p>'
            off = a["offene_hilfe"]
            if off["text"]:
                body += f'<p class="hinweis">Hinweis: {_e(off["text"])} <em>(wird als Hilfe vermerkt)</em></p>'
            if a["verfuegbar"] and a["hinweis_verfuegbar"] and not off["text"]:
                body += f'<form method="post" action="{url_for("web.hilfe", uebung_id=uebung_id)}">{_csrf()}' \
                        f'<input type="hidden" name="aufgabe_id" value="{_e(a["id"])}">' \
                        f'<input type="hidden" name="art" value="hinweis"><button>Hinweis anzeigen</button></form>'
            if a["verfuegbar"]:
                if a["naechste_versuchsnummer"] > 1:
                    body += f'<p class="badge">Erneute Bearbeitung (Versuch {a["naechste_versuchsnummer"]})</p>'
                eingaben = ""
                if a["fragetyp"] == "luecke":
                    eingaben = '<label>Antwort<br><input name="gegeben" maxlength="200" required></label>'
                else:
                    typ = "checkbox" if a["fragetyp"] == "multiple_choice" else "radio"
                    eingaben = "".join(
                        f'<label><input type="{typ}" name="gegeben" value="{_e(o["id"])}"> {_e(o["text"])}</label><br>'
                        for o in a["optionen"])
                body += f'<form method="post" action="{url_for("web.versuch", uebung_id=uebung_id)}">{_csrf()}' \
                        f'{_schluessel_feld()}<input type="hidden" name="aufgabe_id" value="{_e(a["id"])}">' \
                        f'<fieldset><legend>Deine Antwort</legend>{eingaben}' \
                        f'<p><label>Wie sicher fühlst du dich? <select name="selbsteinschaetzung">' \
                        f'<option value="">–</option><option value="sicher">sicher</option>' \
                        f'<option value="unsicher">unsicher</option><option value="unklar">unklar</option>' \
                        f'</select></label></p><button>Antwort abgeben</button></fieldset></form>'
            if a["versuche"]:
                links = " · ".join(f'<a href="{url_for("web.versuch_ansehen", versuch_id=v["versuch_id"])}">'
                                   f'Versuch {v["versuchsnummer"]}: {"richtig" if v["richtig"] else "nicht richtig"}</a>'
                                   for v in a["versuche"])
                body += f"<p>Bisherige Auswertungen: {links}</p>"
            teile.append(f'<fieldset id="{anker}"><legend>{_e(a["id"][:8])}</legend>{body}</fieldset>')
        return _seite("Übung", "".join(teile) +
                      f'<p><a href="{url_for("web.module")}">Zurück zu den Modulen</a></p>')
    return _mit_kontext(seite) or redirect(url_for("web.module"))


@blueprint.post("/uebungen/<uebung_id>/hilfe")
def hilfe(uebung_id):
    aufgabe_id = request.form.get("aufgabe_id", "")
    if not _csrf_ok():
        flash("Sicherheitsprüfung fehlgeschlagen. Bitte die Seite neu laden.")
        return redirect(url_for("web.uebung", uebung_id=uebung_id))
    _mit_kontext(lambda s, k: lernen.hilfe_anfordern(s, current_app.config["LERNCFG"], k, uebung_id, aufgabe_id,
                                                     request.form.get("art", "hinweis")))
    return redirect(url_for("web.uebung", uebung_id=uebung_id) + f"#aufgabe-{aufgabe_id}")


@blueprint.post("/uebungen/<uebung_id>/versuch")
def versuch(uebung_id):
    aufgabe_id = request.form.get("aufgabe_id", "")
    zurueck = redirect(url_for("web.uebung", uebung_id=uebung_id) + f"#aufgabe-{aufgabe_id}")
    if not _csrf_ok():
        flash("Sicherheitsprüfung fehlgeschlagen. Bitte die Seite neu laden.")
        return zurueck

    def abgabe(s, k):
        gegeben = _gegeben_aus_formular(s, k, uebung_id, aufgabe_id)
        return lernen.versuch_abgeben(s, current_app.config["LERNCFG"], k, uebung_id, aufgabe_id, gegeben,
                                      request.form.get("selbsteinschaetzung") or None,
                                      request.form.get("schluessel", ""))
    ergebnis = _mit_kontext(abgabe)
    if isinstance(ergebnis, dict):
        return redirect(url_for("web.versuch_ansehen", versuch_id=ergebnis["versuch_id"]))
    return zurueck


@blueprint.get("/versuche/<versuch_id>")
def versuch_ansehen(versuch_id):
    def seite(s, k):
        v = versuch_sicht(s, k, versuch_id)
        aufgabe = v["aufgabe"]
        if v["richtig"]:
            ergebnis = "Richtig" + (" (selbstständig)" if v["selbststaendig"] else " (mit Hilfe oder frühere Lösung)")
        else:
            ergebnis = "Nicht richtig"
        gegeben = ", ".join(v["antwort"]["gegeben_text"]) if isinstance(v["antwort"]["gegeben_text"], list) \
            else str(v["antwort"]["gegeben_text"])
        quellen = "".join(
            f'<p class="quelle">Quelle: {_e(q.get("unterlage"))}, Abschnitt {_e(q.get("position"))}, '
            f'zitierte Version {_e(q.get("version_zitiert"))} · '
            f'<a href="{url_for("web.abschnitt_ansehen", abschnitt_id=q["abschnitt_id"])}">Abschnitt lesen</a>'
            f'{"" if q.get("neu_verwendbar", True) else " · <span class=verwendbar-nein>nicht mehr für neue Erklärungen verwendbar</span>"}'
            f'</p>' for q in v["quellen"] if q.get("unterlage") is not None)
        verlauf = "".join(
            f'<p class="{_e(n["rolle"])}"><strong>{_e({"frage": "Du", "lernbegleiter": "Lernbegleiter", "system": "System"}.get(n["rolle"], n["rolle"]))}'
            f'{" · " + _e(n["herkunft"].get("herkunft")) if n["rolle"] == "lernbegleiter" else ""}:</strong> {_e(n["text"])}'
            + (f' <span class="badge">Sicherheitsgrad: {_e(n["sicherheitsgrad"])}</span>' if n["sicherheitsgrad"] else "")
            + "".join(f'<br><small>Annahme: {_e(x)}</small>' for x in (n["herkunft"] or {}).get("annahmen", []))
            + "</p>"
            for n in v["verlauf"] if n["rolle"] != "system" or n["form"] != "rueckmeldung")
        rueckmeldung = next((n["text"] for n in v["verlauf"] if n["form"] == "rueckmeldung"), "")
        if v["gespraech_moeglich"]:
            formular = f'<form method="post" action="{url_for("web.gespraech", versuch_id=versuch_id)}" id="gespraech">' \
                       f'{_csrf()}{_schluessel_feld()}' \
                       f'<label>Deine Frage<br><input name="frage" maxlength="500" size="60"></label> ' \
                       f'<select name="form"><option value="erklaerung">Erklärung</option>' \
                       f'<option value="hinweis">Hinweis</option><option value="rueckfrage">Rückfrage</option>' \
                       f'<option value="beispiel">Beispiel</option></select> ' \
                       f'<button>Senden</button></form>'
        else:
            formular = f'<p class="hinweis" id="gespraech">Neue Erklärungen sind derzeit nicht möglich: {_e(v["gespraech_grund"])} ' \
                       f'Der bisherige Verlauf bleibt erhalten.</p>'
        inhalt = f"""<p>Versuch {v['versuchsnummer']} · {_e(v['zeitpunkt'])}</p>
        <fieldset><legend>Aufgabe (Stand der Abgabe, Version {_e(aufgabe['version_zum_zeitpunkt'])})</legend>
        <p>{_e(aufgabe['text'])}</p>
        <p>Deine Antwort: {_e(gegeben)}</p>
        <p><strong>{_e(ergebnis)}</strong> · Punkte {_e(v['punkte'])} von {_e(v['maximum'])}</p></fieldset>
        <section aria-live="polite"><h2>Rückmeldung</h2><p>{_e(rueckmeldung)}</p>
        <p>Richtige Lösung: {_e(', '.join(aufgabe['loesung_text']) if isinstance(aufgabe['loesung_text'], list) else aufgabe['loesung_text'])}</p>
        {quellen}</section>
        <section class="verlauf"><h2>Gespräch mit dem Lernbegleiter</h2>{verlauf or '<p>Noch keine Fragen.</p>'}</section>
        <section><h2>Nächste Frage</h2>{formular}</section>
        <p><a href="{url_for('web.uebung', uebung_id=v['uebung_id'])}">Zurück zur Übung</a></p>"""
        return _seite("Versuch", inhalt)
    return _mit_kontext(seite) or redirect(url_for("web.module"))


@blueprint.post("/versuche/<versuch_id>/gespraech")
def gespraech(versuch_id):
    if not _csrf_ok():
        flash("Sicherheitsprüfung fehlgeschlagen. Bitte die Seite neu laden.")
        return redirect(url_for("web.versuch_ansehen", versuch_id=versuch_id))
    ergebnis = _mit_kontext(lambda s, k: lernbegleiter.gespraech_fuehren(
        s, current_app.config["LERNCFG"], current_app.config["MODELL"], k, versuch_id,
        request.form.get("frage"), request.form.get("form", "erklaerung"), request.form.get("schluessel", "")))
    return redirect(url_for("web.versuch_ansehen", versuch_id=versuch_id) + "#gespraech")


@blueprint.get("/abschnitte/<abschnitt_id>")
def abschnitt_ansehen(abschnitt_id):
    def seite(s, k):
        a = abschnitt_sicht(s, k, abschnitt_id)
        status = "verwendbar" if a["neu_verwendbar"] else f'nicht verwendbar: {a["hinweis"]}'
        inhalt = f"""<p class="quelle">{_e(a['unterlage'])} · Abschnitt {_e(a['position'])}</p>
        <fieldset><legend>Zitierter Stand: Version {_e(a['version_zitiert'])}</legend>
        <p>{_e(a['text'])}</p></fieldset>
        <p>Aktueller Stand: Version {_e(a['version_aktuell'])}, Status «{_e(a['status_aktuell'])}».
        Für neue Erklärungen: <strong>{_e(status)}</strong></p>
        <p><small>Der zitierte Text bleibt als Nachweis erhalten, auch wenn die Unterlage später geändert wird.</small></p>"""
        return _seite("Quelle", inhalt)
    return _mit_kontext(seite) or redirect(url_for("web.module"))
