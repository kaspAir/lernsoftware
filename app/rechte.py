"""Berechtigungen (Dokument 01 §3, Spez. §2). Serverseitig an jeder Dienstfunktion geprüft.

Zwei Ebenen:
- Organisationsebene: `admin` (Membership mit Rolle admin) oder `mitglied`.
- Modulebene: Rolle aus der Modulzuweisung (`dozierende`, `assistenz`, `studierende`).

Beweist: Studierende erhalten nur Module, denen sie zugewiesen sind (MO-03); die fachliche
Freigabe liegt bei Dozierenden oder bei delegierter Assistenz (D-03); Admins geben nicht frei;
Fremde Mandanten erscheinen als «nicht gefunden» (TC-MAND-01).
"""
from dataclasses import dataclass

from sqlalchemy import select

from .fehler import nicht_gefunden, verboten
from .models import Mitgliedschaft, Modul, Modulzuweisung


@dataclass(frozen=True)
class Kontext:
    konto_id: str
    lernorganisation_id: str
    org_rolle: str  # admin | mitglied


def lade_kontext(session, konto_id: str, lernorganisation_id: str) -> Kontext:
    mitgliedschaften = session.scalars(
        select(Mitgliedschaft).where(
            Mitgliedschaft.konto_id == konto_id,
            Mitgliedschaft.lernorganisation_id == lernorganisation_id,
        )
    ).all()
    if not mitgliedschaften:
        raise nicht_gefunden("Lernorganisation")
    ist_admin = any(m.rolle == "admin" for m in mitgliedschaften)
    return Kontext(konto_id=konto_id, lernorganisation_id=lernorganisation_id,
                   org_rolle="admin" if ist_admin else "mitglied")


def modul_im_mandanten(session, kontext: Kontext, modul_id: str) -> Modul:
    modul = session.get(Modul, modul_id)
    if modul is None or modul.lernorganisation_id != kontext.lernorganisation_id:
        raise nicht_gefunden("Modul")
    return modul


def zuweisung(session, kontext: Kontext, modul_id: str) -> Modulzuweisung | None:
    return session.scalars(
        select(Modulzuweisung).where(
            Modulzuweisung.modul_id == modul_id,
            Modulzuweisung.konto_id == kontext.konto_id,
            Modulzuweisung.lernorganisation_id == kontext.lernorganisation_id,
        )
    ).first()


def modul_rolle(session, kontext: Kontext, modul_id: str) -> str | None:
    """Rolle im Modul: 'admin' für Organisationsadmins, sonst die Zuweisungsrolle, sonst None."""
    if kontext.org_rolle == "admin":
        return "admin"
    z = zuweisung(session, kontext, modul_id)
    return z.rolle if z else None


def pruefe_modulzugriff(session, kontext: Kontext, modul_id: str) -> Modul:
    """Lesezugriff auf ein Modul (Metadaten). Ohne Rolle im Modul: 404."""
    modul = modul_im_mandanten(session, kontext, modul_id)
    if modul_rolle(session, kontext, modul_id) is None:
        raise nicht_gefunden("Modul")
    return modul


def pruefe_verwaltung(session, kontext: Kontext, modul_id: str) -> None:
    """Inhalte pflegen (Lektionen, Lernziele, Unterlagen, Aufgaben): Dozierende und Assistenz."""
    modul_im_mandanten(session, kontext, modul_id)
    if modul_rolle(session, kontext, modul_id) not in ("dozierende", "assistenz"):
        raise verboten("Nur Dozierende und Assistenz des Moduls pflegen Inhalte.")


def darf_freigeben(session, kontext: Kontext, modul_id: str) -> bool:
    """Fachliche Freigabe (D-03): Dozierende; Assistenz nur bei ausdrücklicher Delegation."""
    z = zuweisung(session, kontext, modul_id)
    if z is None or kontext.org_rolle == "admin":
        return False
    if z.rolle == "dozierende":
        return True
    return z.rolle == "assistenz" and bool(z.freigabe_delegiert)


def pruefe_freigabe(session, kontext: Kontext, modul_id: str) -> None:
    if not darf_freigeben(session, kontext, modul_id):
        raise verboten("Die fachliche Freigabe liegt bei Dozierenden oder delegierter Assistenz (D-03).")


def pruefe_studierend(session, kontext: Kontext, modul_id: str) -> None:
    modul_im_mandanten(session, kontext, modul_id)
    z = zuweisung(session, kontext, modul_id)
    if z is None or z.rolle != "studierende":
        raise nicht_gefunden("Modul")
