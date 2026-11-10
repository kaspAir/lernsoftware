"""Anmeldung mit Benutzername und Passwort (BE-01, BE-03, BE-05).

Beweist: Falsche Anmeldedaten liefern immer dieselbe Meldung (keine Kontenerkennung); nach
fünf Fehlversuchen ist das Konto für 15 Minuten gesperrt, auch bei richtigem Passwort.
"""
from datetime import timedelta, timezone

from sqlalchemy import select

from ..fehler import FachFehler
from ..models import Konto, Lernorganisation, jetzt
from ..rechte import lade_kontext
from ..sicherheit import pruefe_passwort
from .nachweis import schreibe_nachweis

ALLGEMEIN = "Anmeldung fehlgeschlagen. Prüfe Organisation, Benutzername und Passwort."


def _als_utc(dt):
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)


def anmelden(session, cfg: dict, kurzname: str | None, benutzername: str, passwort: str) -> dict:
    konto = session.scalars(select(Konto).where(Konto.benutzername == (benutzername or "").strip().lower())).first()
    if konto is None:
        raise FachFehler("anmeldung_fehlgeschlagen", ALLGEMEIN, status=401)
    now = jetzt()
    if konto.gesperrt_bis is not None and now < _als_utc(konto.gesperrt_bis):
        raise FachFehler("gesperrt", "Das Konto ist vorübergehend gesperrt. Bitte später erneut versuchen.", status=423)
    if konto.status != "aktiv" or not pruefe_passwort(konto.passwort_hash, passwort or "", cfg):
        if konto.status == "aktiv":
            konto.fehlversuche = (konto.fehlversuche or 0) + 1
            if konto.fehlversuche >= cfg["sicherheit"]["fehlversuche_bis_sperre"]:
                konto.gesperrt_bis = now + timedelta(minutes=cfg["sicherheit"]["sperre_minuten"])
                konto.fehlversuche = 0
                schreibe_nachweis(session, "konto_gesperrt", None, konto.id, konto.id, {})
            # Der Fehlversuch muss bestehen bleiben, auch wenn die Anfrage mit Fehler endet.
            session.commit()
        raise FachFehler("anmeldung_fehlgeschlagen", ALLGEMEIN, status=401)

    konto.fehlversuche = 0
    konto.gesperrt_bis = None
    if not kurzname:
        if not konto.ist_superadmin:
            raise FachFehler("anmeldung_fehlgeschlagen", ALLGEMEIN, status=401)
        schreibe_nachweis(session, "anmeldung", None, konto.id, None, {"rolle": "super_admin"})
        return {"konto_id": konto.id, "superadmin": True, "lernorganisation_id": None, "org_rolle": None}

    org = session.scalars(select(Lernorganisation).where(Lernorganisation.kurzname == kurzname.strip().lower())).first()
    if org is None or org.status != "aktiv":
        raise FachFehler("anmeldung_fehlgeschlagen", ALLGEMEIN, status=401)
    try:
        kontext = lade_kontext(session, konto.id, org.id)
    except FachFehler:
        raise FachFehler("anmeldung_fehlgeschlagen", ALLGEMEIN, status=401)
    schreibe_nachweis(session, "anmeldung", org.id, konto.id, None, {"org_rolle": kontext.org_rolle})
    return {"konto_id": konto.id, "superadmin": False, "lernorganisation_id": org.id,
            "org_rolle": kontext.org_rolle}
