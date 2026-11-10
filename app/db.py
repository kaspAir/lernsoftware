"""Datenbankanbindung. Entwicklung: SQLite (Abweichung A-1); Ziel: PostgreSQL mit RLS (ADR-L-006).

Beweist: Jede mandantenbezogene Abfrage läuft über `mandant_abfrage` und verlangt eine
Lernorganisation; es gibt keinen Abfrage-Helfer ohne Mandantenbindung.
"""
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Basis(DeclarativeBase):
    pass


def erstelle_engine(url: str):
    engine = create_engine(url, future=True)
    if url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def _fremdschluessel_an(dbapi_conn, _):
            cur = dbapi_conn.cursor()
            cur.execute("PRAGMA foreign_keys=ON")
            cur.close()
    return engine


def sitzungsfabrik(engine):
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)


def mandant_abfrage(model, lernorganisation_id: str):
    """Einzige Form einer Abfrage auf mandantenbezogene Modelle (RA-08, ADR-L-006)."""
    if not lernorganisation_id:
        raise ValueError("Mandantenkontext fehlt – Abfrage verweigert")
    return select(model).where(model.lernorganisation_id == lernorganisation_id)
