"""Minimale Browser-Oberfläche für den Lernablauf der Studierenden (Inkrement 1).

Verwaltung (Organisation, Module, Unterlagen, Aufgaben) läuft über die JSON-Schnittstelle und
das Demonstrationsskript `python -m app.demo`. Die Oberfläche folgt noch nicht der Bedienungsnorm
(D-10); sie ist zugänglich aufgebaut (Beschriftungen, Tastatur) und bewusst schlicht.
"""
import html

from flask import Blueprint, current_app, flash, redirect, render_template_string, request, session as websitzung, url_for

from .api import sitzung
from .dienste import anmeldung, lernbegleiter, lernen, verwaltung
from .fehler import FachFehler
from .rechte import lade_kontext

blueprint = Blueprint("web", __name__)

SEITE = """<!doctype html>
<html lang="de-CH"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ titel }} · Lernsoftware</title>
<style>
body{font-family:system-ui,sans-serif;max-width:52rem;margin:2rem auto;padding:0 1rem;line-height:1.5;color:#1a1a1a}
h1{font-size:1.5rem} .hinweis{background:#fff4d6;border-left:4px solid #b78100;padding:.5rem .75rem;margin:.75rem 0}
.quelle{font-size:.9rem;color:#333;border-left:3px solid #1f4e79;padding:.25rem .6rem;margin:.4rem 0}
fieldset{margin:1rem 0;padding:.75rem;border:1px solid #bbb} button{padding:.4rem .9rem}
.fehler{color:#8a1c1c;font-weight:600}
.badge{display:inline-block;font-size:.85rem;padding:.1rem .45rem;border:1px solid #555;border-radius:3px}
</style></head><body>
<main>
<h1>{{ titel }}</h1>
{% for m in get_flashed_messages() %}<p class="fehler" role="alert">{{ m }}</p>{% endfor %}
{{ inhalt|safe }}
</main></body></html>"""


def _seite(titel: str, inhalt: str):
    return render_template_string(SEITE, titel=titel, inhalt=inhalt)


def _e(text) -> str:
    return html.escape("" if text is None else str(text))


def _csrf_feld() -> str:
    return f'<input type="hidden" name="csrf" value="{_e(websitzung.get("csrf", ""))}">'


def _csrf_ok() -> bool:
    return bool(websitzung.get("csrf")) and request.form.get("csrf") == websitzung.get("csrf")


def _angemeldet_kontext(s):
    konto_id = websitzung.get("konto_id")
    org_id = websitzung.get("lernorganisation_id")
    if not konto_id or not org_id:
        raise FachFehler("nicht_angemeldet", "Bitte zuerst anmelden.", status=401)
    return lade_kontext(s, konto_id, org_id)


@blueprint.get("/")
def start():
    if websitzung.get("konto_id"):
        return redirect(url_for("web.module"))
    return redirect(url_for("web.anmelden"))


@blueprint.route("/anmelden", methods=["GET", "POST"])
def anmelden():
    if request.method == "POST":
        try:
            with sitzung() as s:
                ergebnis = anmeldung.anmelden(s, current_app.config["LERNCFG"], request.form.get("kurzname"),
                                              request.form.get("benutzername", ""), request.form.get("passwort", ""))
            if ergebnis["superadmin"]:
                flash("Super-Admin-Anmeldung ist in der Oberfläche nicht vorgesehen; bitte die Schnittstelle nutzen.")
                return redirect(url_for("web.anmelden"))
            websitzung.clear()
            websitzung["konto_id"] = ergebnis["konto_id"]
            websitzung["lernorganisation_id"] = ergebnis["lernorganisation_id"]
            websitzung["csrf"] = __import__("secrets").token_urlsafe(24)
            return redirect(url_for("web.module"))
        except FachFehler as exc:
            flash(exc.nachricht)
    inhalt = """<form method="post" aria-label="Anmeldung">
    <p><label>Lernorganisation (Kurzname)<br><input name="kurzname" required autocomplete="organization"></label></p>
    <p><label>Benutzername<br><input name="benutzername" required autocomplete="username"></label></p>
    <p><label>Passwort<br><input name="passwort" type="password" required autocomplete="current-password"></label></p>
    <p><button type="submit">Anmelden</button></p></form>"""
    return _seite("Anmelden", inhalt)


@blueprint.get("/abmelden")
def abmelden():
    websitzung.clear()
    return redirect(url_for("web.anmelden"))


@blueprint.get("/module")
def module():
    if not websitzung.get("konto_id"):
        return redirect(url_for("web.anmelden"))
    try:
        with sitzung() as s:
            k = _angemeldet_kontext(s)
            module_liste = verwaltung.module_fuer_kontext(s, k)
    except FachFehler as exc:
        flash(exc.nachricht)
        return redirect(url_for("web.anmelden"))
    zeilen = "".join(
        f'<li><a href="{url_for("web.modul", modul_id=m["id"])}">{_e(m["bezeichnung"])}</a> '
        f'<span class="badge">{_e(m["rolle"])}</span></li>' for m in module_liste)
    inhalt = f"<ul>{zeilen or '<li>Dir sind noch keine Module zugewiesen.</li>'}</ul>" \
             f'<p><a href="{url_for("web.abmelden")}">Abmelden</a></p>'
    return _seite("Meine Module", inhalt)


@blueprint.get("/module/<modul_id>")
def modul(modul_id):
    if not websitzung.get("konto_id"):
        return redirect(url_for("web.anmelden"))
    try:
        with sitzung() as s:
            k = _angemeldet_kontext(s)
            lektionen = verwaltung.lektionen_des_moduls(s, k, modul_id)
    except FachFehler as exc:
        flash(exc.nachricht)
        return redirect(url_for("web.module"))
    boxen = "".join(
        f'<label><input type="checkbox" name="lektion_ids" value="{_e(l["id"])}"> '
        f'{_e(l["reihenfolge"])}. {_e(l["titel"])}</label><br>'
        + "".join(f'<small>· {_e(z["text"])} ({_e(z["handlungsstufe"])})</small><br>' for z in l["lernziele"])
        for l in lektionen)
    inhalt = f"""<form method="post" action="{url_for('web.uebung_starten', modul_id=modul_id)}">
    {_csrf_feld()}<fieldset><legend>Lektionen wählen</legend>{boxen or 'Noch keine Lektionen.'}</fieldset>
    <p><button type="submit">Übung erzeugen</button></p></form>"""
    return _seite("Lektionen wählen", inhalt)


@blueprint.post("/module/<modul_id>/uebung")
def uebung_starten(modul_id):
    if not _csrf_ok():
        flash("Sicherheitsprüfung fehlgeschlagen. Bitte neu laden.")
        return redirect(url_for("web.module"))
    ids = request.form.getlist("lektion_ids")
    try:
        with sitzung() as s:
            k = _angemeldet_kontext(s)
            uebung = lernen.uebung_erzeugen(s, current_app.config["LERNCFG"], k, modul_id, ids)
        return redirect(url_for("web.uebung", uebung_id=uebung["id"]))
    except FachFehler as exc:
        flash(exc.nachricht)
        return redirect(url_for("web.modul", modul_id=modul_id))


@blueprint.get("/uebungen/<uebung_id>")
def uebung(uebung_id):
    letzte = websitzung.pop("letzte", None) if websitzung.get("letzte") else None
    rueck = websitzung.pop("gespraech", None) if websitzung.get("gespraech") else None
    try:
        with sitzung() as s:
            k = _angemeldet_kontext(s)
            from .models import Uebung
            from .db import mandant_abfrage
            u = s.scalars(mandant_abfrage(Uebung, k.lernorganisation_id).where(Uebung.id == uebung_id)).first()
            if u is None or u.konto_id != k.konto_id:
                raise FachFehler("nicht_gefunden", "Übung nicht gefunden.", status=404)
            from .models import Aufgabe
            aufgaben = [s.get(Aufgabe, e["id"]) for e in u.aufgaben]
            aufgaben = [a for a in aufgaben if a is not None]
            from .dienste.lernen import _aufgabe_fuer_lernende, _verfuegbare_aufgaben  # noqa: F401
            teile = []
            for a in aufgaben:
                opt = "".join(
                    f'<label><input type="{"checkbox" if a.fragetyp == "multiple_choice" else "radio"}" '
                    f'name="gegeben" value="{_e(o["id"])}"> {_e(o["text"])}</label><br>'
                    for o in (a.optionen or [])) if a.fragetyp in ("single_choice", "multiple_choice") else \
                    f'<label>Antwort<br><input name="gegeben"></label>'
                status = ("KI-erzeugt, technisch geprüft. Nicht von einer Lehrperson geprüft."
                          if a.pruefstatus == "technisch_geprueft" else f"Von Lehrperson geprüft")
                teile.append(f"""<fieldset id="aufgabe-{_e(a.id)}"><legend>{_e(a.aufgabe_text)}</legend>
                <p class="badge">{_e(status)}</p>
                <form method="post" action="{url_for('web.hilfe', uebung_id=uebung_id)}">{_csrf_feld()}
                <input type="hidden" name="aufgabe_id" value="{_e(a.id)}">
                <button name="art" value="hinweis">Hinweis anzeigen</button></form>
                <form method="post" action="{url_for('web.versuch', uebung_id=uebung_id)}">{_csrf_feld()}
                <input type="hidden" name="aufgabe_id" value="{_e(a.id)}">{opt}
                <p><label>Wie sicher fühlst du dich? <select name="selbsteinschaetzung">
                <option value="">–</option><option value="sicher">sicher</option>
                <option value="unsicher">unsicher</option><option value="unklar">unklar</option></select></label></p>
                <button type="submit">Antwort abgeben</button></form></fieldset>""")
    except FachFehler as exc:
        flash(exc.nachricht)
        return redirect(url_for("web.module"))

    rueckmeldung = ""
    if letzte:
        quellen = "".join(f'<p class="quelle">Quelle: {_e(q["unterlage"])}, Version {_e(q["version"])}, '
                          f'Abschnitt {_e(q["position"])}</p>' for q in letzte.get("quellen", []))
        rueckmeldung = f'<section aria-live="polite"><h2>Rückmeldung</h2><p>{_e(letzte["rueckmeldung"])}</p>' \
                       f'{quellen}<p>{_e(letzte["naechster_schritt"])}</p>' \
                       f'<form method="post" action="{url_for("web.rueckfrage", versuch_id=letzte["versuch_id"])}">' \
                       f'{_csrf_feld()}<label>Rückfrage an den Lernbegleiter<br>' \
                       f'<input name="frage" size="60"></label> ' \
                       f'<select name="form"><option value="erklaerung">Erklärung</option>' \
                       f'<option value="hinweis">Hinweis</option><option value="rueckfrage">Rückfrage</option>' \
                       f'<option value="beispiel">Beispiel</option></select> ' \
                       f'<button type="submit">Senden</button></form></section>'
    gesprach = ""
    if rueck:
        gesprach = f'<section><h2>Lernbegleiter</h2><p>{_e(rueck["text"])}</p>' + "".join(
            f'<p class="quelle">Quelle: {_e(q.get("unterlage"))}, Abschnitt {_e(q.get("position"))} · '
            f'Aussage: {_e(q.get("fachlich"))}</p>' for q in rueck.get("quellen", [])) + \
            f'<p class="badge">Sicherheitsgrad: {_e(rueck.get("sicherheitsgrad"))}</p>' + \
            "".join(f'<p class="hinweis">{_e(x)}</p>' for x in rueck.get("annahmen", [])) + "</section>"
    inhalt = f"""{rueckmeldung}{gesprach}{''.join(teile)}
    <p><a href="{url_for('web.module')}">Zurück zu den Modulen</a></p>"""
    return _seite("Übung", inhalt)


@blueprint.post("/uebungen/<uebung_id>/hilfe")
def hilfe(uebung_id):
    if _csrf_ok():
        try:
            with sitzung() as s:
                k = _angemeldet_kontext(s)
                lernen.hilfe_anfordern(s, k, uebung_id, request.form.get("aufgabe_id", ""),
                                       request.form.get("art", "hinweis"))
        except FachFehler as exc:
            flash(exc.nachricht)
    return redirect(url_for("web.uebung", uebung_id=uebung_id) + "#aufgabe-" + request.form.get("aufgabe_id", ""))


@blueprint.post("/uebungen/<uebung_id>/versuch")
def versuch(uebung_id):
    if not _csrf_ok():
        flash("Sicherheitsprüfung fehlgeschlagen. Bitte neu laden.")
        return redirect(url_for("web.uebung", uebung_id=uebung_id))
    gegeben = request.form.getlist("gegeben")
    gegeben_wert = gegeben if len(gegeben) != 1 else gegeben[0]
    if not gegeben:
        gegeben_wert = ""
    try:
        with sitzung() as s:
            k = _angemeldet_kontext(s)
            ergebnis = lernen.versuch_abgeben(s, current_app.config["LERNCFG"], k, uebung_id,
                                              request.form.get("aufgabe_id", ""), gegeben_wert,
                                              request.form.get("selbsteinschaetzung") or None)
        websitzung["letzte"] = ergebnis
    except FachFehler as exc:
        flash(exc.nachricht)
    return redirect(url_for("web.uebung", uebung_id=uebung_id) + "#aufgabe-" + request.form.get("aufgabe_id", ""))


@blueprint.post("/versuche/<versuch_id>/rueckfrage")
def rueckfrage(versuch_id):
    if not _csrf_ok():
        flash("Sicherheitsprüfung fehlgeschlagen. Bitte neu laden.")
        return redirect(url_for("web.module"))
    try:
        with sitzung() as s:
            k = _angemeldet_kontext(s)
            ergebnis = lernbegleiter.gespraech_fuehren(s, current_app.config["LERNCFG"],
                                                       current_app.config["MODELL"], k, versuch_id,
                                                       request.form.get("frage"),
                                                       request.form.get("form", "erklaerung"))
        websitzung["gespraech"] = ergebnis
    except FachFehler as exc:
        flash(exc.nachricht)
    return redirect(request.referrer or url_for("web.module"))
