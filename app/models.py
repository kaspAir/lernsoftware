"""Datenmodell Inkrement 1 (Spez. §3, §5, §6, §8).

Jedes mandantenbezogene Objekt trägt `lernorganisation_id` (RA-08). Das Governance-Mixin
(RA-03) ist als Felder `erstellt_am`, `aktualisiert_am`, `version`, `schema_version` vorhanden.
Die Urheberfelder stehen je Objekt am Modell.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .db import Basis

SCHEMA = "1"


def neue_id() -> str:
    return str(uuid.uuid4())


def jetzt() -> datetime:
    return datetime.now(timezone.utc)


class Mixin:
    erstellt_am: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=jetzt)
    aktualisiert_am: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=jetzt, onupdate=jetzt)
    version: Mapped[int] = mapped_column(Integer, default=1)
    schema_version: Mapped[str] = mapped_column(String(8), default=SCHEMA)


class Lernorganisation(Mixin, Basis):
    """Plattformregister (B-01). Enthält nur Registrierungsfelder, keine Inhalte."""
    __tablename__ = "lernorganisation"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=neue_id)
    name: Mapped[str] = mapped_column(String(200))
    kurzname: Mapped[str] = mapped_column(String(64), unique=True)
    status: Mapped[str] = mapped_column(String(16), default="aktiv")


class Konto(Mixin, Basis):
    """Globales Konto (BE-05). Zugehörigkeit zu Lernorganisationen über Mitgliedschaft."""
    __tablename__ = "konto"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=neue_id)
    benutzername: Mapped[str] = mapped_column(String(64), unique=True)
    anzeigename: Mapped[str] = mapped_column(String(200))
    passwort_hash: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(16), default="aktiv")
    ist_superadmin: Mapped[bool] = mapped_column(Boolean, default=False)
    fehlversuche: Mapped[int] = mapped_column(Integer, default=0)
    gesperrt_bis: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Mitgliedschaft(Mixin, Basis):
    __tablename__ = "mitgliedschaft"
    __table_args__ = (UniqueConstraint("lernorganisation_id", "konto_id", "rolle"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=neue_id)
    lernorganisation_id: Mapped[str] = mapped_column(ForeignKey("lernorganisation.id"), index=True)
    konto_id: Mapped[str] = mapped_column(ForeignKey("konto.id"), index=True)
    rolle: Mapped[str] = mapped_column(String(16))  # admin | dozierende | assistenz | studierende


class Modul(Mixin, Basis):
    __tablename__ = "modul"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=neue_id)
    lernorganisation_id: Mapped[str] = mapped_column(ForeignKey("lernorganisation.id"), index=True)
    bezeichnung: Mapped[str] = mapped_column(String(200))
    beschreibung: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(16), default="aktiv")


class Modulzuweisung(Mixin, Basis):
    """Genau eine Modulrolle je Konto und Modul (Regel in Dokument 03 §2.1)."""
    __tablename__ = "modulzuweisung"
    __table_args__ = (UniqueConstraint("modul_id", "konto_id"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=neue_id)
    lernorganisation_id: Mapped[str] = mapped_column(ForeignKey("lernorganisation.id"), index=True)
    modul_id: Mapped[str] = mapped_column(ForeignKey("modul.id"), index=True)
    konto_id: Mapped[str] = mapped_column(ForeignKey("konto.id"), index=True)
    rolle: Mapped[str] = mapped_column(String(16))  # dozierende | assistenz | studierende
    freigabe_delegiert: Mapped[bool] = mapped_column(Boolean, default=False)  # D-03


class Lektion(Mixin, Basis):
    __tablename__ = "lektion"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=neue_id)
    lernorganisation_id: Mapped[str] = mapped_column(ForeignKey("lernorganisation.id"), index=True)
    modul_id: Mapped[str] = mapped_column(ForeignKey("modul.id"), index=True)
    titel: Mapped[str] = mapped_column(String(200))
    reihenfolge: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(16), default="aktiv")


class Lernziel(Mixin, Basis):
    __tablename__ = "lernziel"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=neue_id)
    lernorganisation_id: Mapped[str] = mapped_column(ForeignKey("lernorganisation.id"), index=True)
    lektion_id: Mapped[str] = mapped_column(ForeignKey("lektion.id"), index=True)
    text: Mapped[str] = mapped_column(Text)
    handlungsstufe: Mapped[str] = mapped_column(String(32))  # Vokabular Spez. §7.3
    reihenfolge: Mapped[int] = mapped_column(Integer, default=0)


class Unterlage(Mixin, Basis):
    __tablename__ = "unterlage"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=neue_id)
    lernorganisation_id: Mapped[str] = mapped_column(ForeignKey("lernorganisation.id"), index=True)
    modul_id: Mapped[str] = mapped_column(ForeignKey("modul.id"), index=True)
    lektion_id: Mapped[str | None] = mapped_column(ForeignKey("lektion.id"), nullable=True, index=True)
    titel: Mapped[str] = mapped_column(String(200))
    dateiname: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(32))  # Spez. §4.1
    hochgeladen_von: Mapped[str] = mapped_column(String(36))
    freigegeben_von: Mapped[str | None] = mapped_column(String(36), nullable=True)
    freigegeben_am: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    freigabeform: Mapped[str | None] = mapped_column(String(32), nullable=True)
    auflage_verantwortlich: Mapped[str | None] = mapped_column(String(200), nullable=True)
    auflage_frist: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class UnterlageVersion(Mixin, Basis):
    """Unveränderliche Fassung einer Unterlage (IN-05)."""
    __tablename__ = "unterlage_version"
    __table_args__ = (UniqueConstraint("unterlage_id", "nummer"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=neue_id)
    lernorganisation_id: Mapped[str] = mapped_column(ForeignKey("lernorganisation.id"), index=True)
    unterlage_id: Mapped[str] = mapped_column(ForeignKey("unterlage.id"), index=True)
    nummer: Mapped[int] = mapped_column(Integer)
    inhalt_text: Mapped[str] = mapped_column(Text)


class Abschnitt(Mixin, Basis):
    """Zitierfähige Textstelle (IN-10). Gehört zu einer Unterlage-Version."""
    __tablename__ = "abschnitt"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=neue_id)
    lernorganisation_id: Mapped[str] = mapped_column(ForeignKey("lernorganisation.id"), index=True)
    unterlage_id: Mapped[str] = mapped_column(ForeignKey("unterlage.id"), index=True)
    unterlage_version: Mapped[int] = mapped_column(Integer)
    position: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)


class Aufgabe(Mixin, Basis):
    __tablename__ = "aufgabe"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=neue_id)
    lernorganisation_id: Mapped[str] = mapped_column(ForeignKey("lernorganisation.id"), index=True)
    modul_id: Mapped[str] = mapped_column(ForeignKey("modul.id"), index=True)
    lektion_id: Mapped[str] = mapped_column(ForeignKey("lektion.id"), index=True)
    lernziel_id: Mapped[str] = mapped_column(ForeignKey("lernziel.id"), index=True)
    aufgabe_text: Mapped[str] = mapped_column(Text)
    fragetyp: Mapped[str] = mapped_column(String(32))
    optionen: Mapped[list] = mapped_column(JSON, default=list)
    loesung: Mapped[list] = mapped_column(JSON, default=list)   # Option-IDs bzw. zulässige Texte
    max_punkte: Mapped[float] = mapped_column(Numeric(8, 2), default=1)
    erklaerung: Mapped[str] = mapped_column(Text)               # Lösungsbegründung
    hinweis: Mapped[str | None] = mapped_column(Text, nullable=True)   # Hilfe Stufe 1
    beispiel: Mapped[str | None] = mapped_column(Text, nullable=True)  # Hilfe Stufe 2
    abschnitt_ids: Mapped[list] = mapped_column(JSON, default=list)
    denkschritte: Mapped[int] = mapped_column(Integer, default=1)
    pruefstatus: Mapped[str] = mapped_column(String(32))        # technisch_geprueft | fachlich_geprueft | gesperrt | verworfen
    fachlich_geprueft_von: Mapped[str | None] = mapped_column(String(36), nullable=True)
    erstellt_von: Mapped[str] = mapped_column(String(36))


class Uebung(Mixin, Basis):
    __tablename__ = "uebung"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=neue_id)
    lernorganisation_id: Mapped[str] = mapped_column(ForeignKey("lernorganisation.id"), index=True)
    konto_id: Mapped[str] = mapped_column(ForeignKey("konto.id"), index=True)
    modul_id: Mapped[str] = mapped_column(ForeignKey("modul.id"), index=True)
    lektion_ids: Mapped[list] = mapped_column(JSON, default=list)
    aufgaben: Mapped[list] = mapped_column(JSON, default=list)  # [{id, version}] eingefroren
    modus: Mapped[str] = mapped_column(String(16), default="lernen")


class Hilfeereignis(Mixin, Basis):
    """Vor einer Antwort angezeigte Hilfe (PR-04). Wird dem nächsten Versuch zugeordnet."""
    __tablename__ = "hilfeereignis"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=neue_id)
    lernorganisation_id: Mapped[str] = mapped_column(ForeignKey("lernorganisation.id"), index=True)
    konto_id: Mapped[str] = mapped_column(ForeignKey("konto.id"), index=True)
    uebung_id: Mapped[str] = mapped_column(ForeignKey("uebung.id"), index=True)
    aufgabe_id: Mapped[str] = mapped_column(ForeignKey("aufgabe.id"), index=True)
    art: Mapped[str] = mapped_column(String(16))  # hinweis | beispiel
    zeitpunkt: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=jetzt)
    versuch_id: Mapped[str | None] = mapped_column(String(36), nullable=True)


class Versuch(Mixin, Basis):
    """Eine Abgabe. Nach Abgabe unveränderlich (Spez. §8). Doppelabgaben über den Schlüssel
    (konto_id, idempotenz_schluessel) ausgeschlossen."""
    __tablename__ = "versuch"
    __table_args__ = (UniqueConstraint("konto_id", "idempotenz_schluessel"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=neue_id)
    lernorganisation_id: Mapped[str] = mapped_column(ForeignKey("lernorganisation.id"), index=True)
    konto_id: Mapped[str] = mapped_column(ForeignKey("konto.id"), index=True)
    uebung_id: Mapped[str] = mapped_column(ForeignKey("uebung.id"), index=True)
    aufgabe_id: Mapped[str] = mapped_column(ForeignKey("aufgabe.id"), index=True)
    aufgabe_version: Mapped[int] = mapped_column(Integer)
    aufgabe_snapshot: Mapped[dict] = mapped_column(JSON)     # Kopie des Aufgabenstands (Versuchstreue)
    versuchsnummer: Mapped[int] = mapped_column(Integer, default=1)  # 1., 2., … Abgabe zu dieser Aufgabe
    idempotenz_schluessel: Mapped[str | None] = mapped_column(String(64), nullable=True)
    gegeben: Mapped[list | str | None] = mapped_column(JSON, nullable=True)
    punkte: Mapped[float] = mapped_column(Numeric(8, 2))
    maximum: Mapped[float] = mapped_column(Numeric(8, 2))
    richtig: Mapped[bool] = mapped_column(Boolean)
    hilfen: Mapped[list] = mapped_column(JSON, default=list)  # [{art, zeitpunkt}]
    selbsteinschaetzung: Mapped[str | None] = mapped_column(String(16), nullable=True)
    zeitpunkt: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=jetzt)
    herkunft: Mapped[dict] = mapped_column(JSON, default=dict)


class Wiederholungszustand(Mixin, Basis):
    __tablename__ = "wiederholungszustand"
    __table_args__ = (UniqueConstraint("konto_id", "aufgabe_id"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=neue_id)
    lernorganisation_id: Mapped[str] = mapped_column(ForeignKey("lernorganisation.id"), index=True)
    konto_id: Mapped[str] = mapped_column(ForeignKey("konto.id"), index=True)
    aufgabe_id: Mapped[str] = mapped_column(ForeignKey("aufgabe.id"), index=True)
    ease: Mapped[float] = mapped_column(Numeric(6, 4))
    intervall_tage: Mapped[int] = mapped_column(Integer)
    wiederholungen: Mapped[int] = mapped_column(Integer)
    naechste_faelligkeit: Mapped[str] = mapped_column(String(10))  # ISO-Datum


class Nachricht(Mixin, Basis):
    """Lernbegleiter-Verlauf (BS-01, BS-07). Fragen sind über den Schlüssel idempotent."""
    __tablename__ = "nachricht"
    __table_args__ = (UniqueConstraint("konto_id", "anfrage_schluessel"),)
    anfrage_schluessel: Mapped[str | None] = mapped_column(String(64), nullable=True)
    bezug_id: Mapped[str | None] = mapped_column(String(36), nullable=True)  # Antwort -> Frage
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=neue_id)
    lernorganisation_id: Mapped[str] = mapped_column(ForeignKey("lernorganisation.id"), index=True)
    konto_id: Mapped[str] = mapped_column(ForeignKey("konto.id"), index=True)
    versuch_id: Mapped[str] = mapped_column(ForeignKey("versuch.id"), index=True)
    rolle: Mapped[str] = mapped_column(String(16))  # frage | system | lernbegleiter
    form: Mapped[str] = mapped_column(String(16))   # rueckmeldung | hinweis | rueckfrage | beispiel | erklaerung | nicht_erreichbar
    text: Mapped[str] = mapped_column(Text)
    quellen: Mapped[list] = mapped_column(JSON, default=list)
    sicherheitsgrad: Mapped[str | None] = mapped_column(String(16), nullable=True)
    herkunft: Mapped[dict] = mapped_column(JSON, default=dict)  # herkunft: echt | SIMULIERT | kern | system
    zeitpunkt: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=jetzt)


class Nachweis(Basis):
    """Unveränderlicher Protokolleintrag (RA-13, NF-04). Wird nie aktualisiert."""
    __tablename__ = "nachweis"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=neue_id)
    lernorganisation_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    art: Mapped[str] = mapped_column(String(32))
    konto_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    objekt_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    kennung: Mapped[str | None] = mapped_column(String(16), nullable=True)  # z. B. NR-02
    inhalt: Mapped[dict] = mapped_column(JSON, default=dict)
    zeitpunkt: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=jetzt)
