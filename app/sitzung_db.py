"""Datenbanksitzung je Anfrage: Erfolg committet, Fehler verwirft alles (keine Teilzustände)."""
from contextlib import contextmanager


@contextmanager
def sitzung(app):
    s = app.config["SITZUNG"]()
    try:
        yield s
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()
