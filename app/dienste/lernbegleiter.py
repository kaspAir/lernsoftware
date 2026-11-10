"""Lernbegleiter: Rückfragen zu einem Versuch mit Quellenprüfung (BS-01 bis BS-08, Spez. §10).

Ablauf: Kontext sammeln (pseudonymisiert) → Modellaufruf über den Adapter → Schema-, Quellen-
und Sprachprüfung im Kern → Antwort oder Standardtext. Bei jeder Ablehnung ein Nachweis mit Kennung.

Beweist:
- Eine Quelle außerhalb der übergebenen Abschnitte führt zur Ablehnung (NR-02, BS-02).
- Bewertungssprache führt zur Ablehnung (BS-06).
- Ohne Modell oder bei Ausfall entsteht keine erfundene Erklärung (Spez. §12).
- Jede Antwort trägt Herkunft: Modell (echt oder SIMULIERT) oder Kern.
"""
from ..db import mandant_abfrage
from ..fehler import FachFehler, nicht_gefunden
from ..kern import evidenz
from ..models import Abschnitt, Aufgabe, Konto, Lektion, Nachricht, Unterlage, Versuch
from ..modell.adapter import ModellAufruf, ModellFehler, PseudonymisierungBlockiert
from ..rechte import Kontext
from .nachweis import schreibe_nachweis

FORMEN = ("hinweis", "rueckfrage", "beispiel", "erklaerung")
SICHERHEIT = ("sicher", "wahrscheinlich", "unbestaetigt")

STANDARD_NICHT_BELEGT = "In den freigegebenen Unterlagen finde ich dazu keine belegte Antwort. Du kannst die Frage an die Lehrperson weiterleiten."
STANDARD_NICHT_ERREICHBAR = "Der Lernbegleiter ist gerade nicht erreichbar. Deine Antwort ist gespeichert."
STANDARD_BLOCKIERT = "Der Lernbegleiter braucht eine Entscheidung zu einer Fundstelle. Die Frage wurde nicht gesendet."


def _pseudonym(konto_id: str) -> str:
    return "Lernende/r " + konto_id[:6]


def gespraech_fuehren(session, cfg: dict, adapter, kontext: Kontext, versuch_id: str,
                      frage: str | None, form: str) -> dict:
    if form not in FORMEN:
        raise FachFehler("form_ungueltig", "Form: hinweis, rueckfrage, beispiel oder erklaerung.", status=422)
    versuch = session.scalars(mandant_abfrage(Versuch, kontext.lernorganisation_id)
                              .where(Versuch.id == versuch_id)).first()
    if versuch is None or versuch.konto_id != kontext.konto_id:
        raise nicht_gefunden("Versuch")

    snap = versuch.aufgabe_snapshot
    abschnitte = []
    for aid in snap["abschnitt_ids"]:
        a = session.scalars(mandant_abfrage(Abschnitt, kontext.lernorganisation_id).where(Abschnitt.id == aid)).first()
        if a is not None:
            abschnitte.append({"id": a.id, "text": a.text})
    erlaubte_ids = {a["id"] for a in abschnitte}

    # Lernprofil nur als Lernzieltexte und Zählwerte, ohne Namen (NF-02, RA-09)
    aufgabe = session.get(Aufgabe, versuch.aufgabe_id)
    auftrag = {
        "form": form,
        "frage": (frage or "").strip() or "Erkläre das Ergebnis dieser Aufgabe.",
        "versuch": {"aufgabe_version": versuch.aufgabe_version, "aufgabe_text": snap["text"],
                    "gegeben": versuch.gegeben, "richtig": versuch.richtig,
                    "punkte": float(versuch.punkte), "maximum": float(versuch.maximum)},
        "loesung": {"erklaerung": snap["erklaerung"]},
        "abschnitte": abschnitte,
        "lernziel_ids": [aufgabe.lernziel_id] if aufgabe else [],
        "pseudonym": _pseudonym(kontext.konto_id),
    }

    nachricht_frage = Nachricht(lernorganisation_id=kontext.lernorganisation_id, konto_id=kontext.konto_id,
                                versuch_id=versuch.id, rolle="frage", form=form,
                                text=(frage or "").strip() or "(Erklärung angefordert)",
                                herkunft={"erzeugt_durch": "mensch", "konto": kontext.konto_id})
    session.add(nachricht_frage)

    ergebnis = _modell_mit_pruefung(session, cfg, adapter, kontext, versuch, auftrag, erlaubte_ids)
    session.add(Nachricht(lernorganisation_id=kontext.lernorganisation_id, konto_id=kontext.konto_id,
                          versuch_id=versuch.id, rolle="lernbegleiter", form=ergebnis["form"],
                          text=ergebnis["text"], quellen=ergebnis["quellen"],
                          sicherheitsgrad=ergebnis.get("sicherheitsgrad"), herkunft=ergebnis["herkunft"]))
    session.flush()
    return ergebnis


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


def _standard(form_, text, herkunft, sicherheit="unbestaetigt", luecke=None):
    return {"form": form_, "text": text, "quellen": [], "luecke": luecke,
            "sicherheitsgrad": sicherheit, "annahmen": [], "herkunft": herkunft}


def _modell_mit_pruefung(session, cfg, adapter, kontext, versuch, auftrag, erlaubte_ids) -> dict:
    herkunft = {"erzeugt_durch": f"system:modell:{adapter.modellname}", "herkunft": adapter.herkunft,
                "anbieter_pfad": "vorschaltdienst" if adapter.herkunft == "echt" else "testadapter"}
    aufruf = ModellAufruf(auftrag, mandant=kontext.lernorganisation_id, sitzung="ls-" + kontext.konto_id[:8])
    versuche = cfg["lernbegleiter"]["schema_wiederholungen"] + 1

    rohdaten = None
    for _ in range(versuche):
        try:
            rohdaten = adapter.aufrufen(aufruf)
        except PseudonymisierungBlockiert:
            schreibe_nachweis(session, "pseudonymisierung_blockiert", kontext.lernorganisation_id,
                              kontext.konto_id, versuch.id, {"versuch": versuch.id})
            return _standard(auftrag["form"], STANDARD_BLOCKIERT, herkunft)
        except ModellFehler as exc:
            schreibe_nachweis(session, "modell_nicht_erreichbar", kontext.lernorganisation_id,
                              kontext.konto_id, versuch.id, {"grund": str(exc)})
            return _standard(auftrag["form"], STANDARD_NICHT_ERREICHBAR, herkunft)
        if _schema_ok(rohdaten):
            break
        rohdaten = None
    if rohdaten is None:
        schreibe_nachweis(session, "modell_schema_fehler", kontext.lernorganisation_id, kontext.konto_id,
                          versuch.id, {"wiederholungen": versuche - 1})
        return _standard(auftrag["form"], STANDARD_NICHT_ERREICHBAR, herkunft)

    schreibe_nachweis(session, "modellaufruf", kontext.lernorganisation_id, kontext.konto_id, versuch.id,
                      {"modell": adapter.modellname, "herkunft": adapter.herkunft,
                       "form": auftrag["form"]})

    # Quellenprüfung (NR-02): jede Quelle muss in der übergebenen Menge sein
    quellen = rohdaten.get("quellen") or []
    unbekannt = [q for q in quellen if q.get("abschnitt_id") not in erlaubte_ids]
    if unbekannt:
        schreibe_nachweis(session, "quelle_abgelehnt", kontext.lernorganisation_id, kontext.konto_id,
                          versuch.id, {"unbekannte_ids": [q.get("abschnitt_id") for q in unbekannt]},
                          kennung="NR-02")
        return _standard(auftrag["form"], STANDARD_NICHT_BELEGT, herkunft)

    # Bewertungssprache (BS-06)
    text = rohdaten["text"]
    verboten = [m for m in cfg["lernbegleiter"]["verbotene_muster"] if m.lower() in text.lower()]
    if verboten:
        schreibe_nachweis(session, "bewertungssprache_abgelehnt", kontext.lernorganisation_id,
                          kontext.konto_id, versuch.id, {"muster_anzahl": len(verboten)}, kennung="BS-06")
        return _standard(auftrag["form"], STANDARD_NICHT_BELEGT, herkunft)

    # Keine Quelle und keine benannte Lücke: unbelegt (BS-05)
    if not quellen:
        luecke = rohdaten.get("luecke") or "Keine Quelle in den freigegebenen Abschnitten"
        return _standard(auftrag["form"], STANDARD_NICHT_BELEGT, herkunft, luecke=luecke)

    sicherheit = rohdaten.get("sicherheitsgrad")
    if sicherheit not in SICHERHEIT:
        sicherheit = "unbestaetigt"
    annahmen = [str(x) for x in (rohdaten.get("annahmen") or [])]
    if sicherheit != "sicher" and not annahmen:
        annahmen = ["Sicherheitsgrad nicht «sicher»: Annahmen fehlen im Modellausgabe."]  # BS-04
    return {
        "form": auftrag["form"] if auftrag["form"] in FORMEN else "erklaerung",
        "text": text,
        "quellen": _quellen_anreichern(session, kontext, quellen),
        "luecke": rohdaten.get("luecke"),
        "sicherheitsgrad": sicherheit,
        "annahmen": annahmen,
        "herkunft": herkunft,
    }


def _schema_ok(daten) -> bool:
    if not isinstance(daten, dict):
        return False
    if not isinstance(daten.get("text"), str) or not daten["text"].strip():
        return False
    if not isinstance(daten.get("quellen", []), list):
        return False
    for q in daten.get("quellen", []):
        if not isinstance(q, dict) or not isinstance(q.get("abschnitt_id"), str):
            return False
    return True
