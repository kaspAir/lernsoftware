"""Fachliche Fehler mit Code und HTTP-Status (Spez. §13)."""


class FachFehler(Exception):
    def __init__(self, code: str, nachricht: str, status: int = 400, felder: dict | None = None):
        super().__init__(nachricht)
        self.code = code
        self.nachricht = nachricht
        self.status = status
        self.felder = felder or {}

    def als_dict(self) -> dict:
        return {"fehler": {"code": self.code, "nachricht": self.nachricht, "felder": self.felder}}


def nicht_gefunden(objekt: str = "Objekt") -> FachFehler:
    # Bewusst 404 auch bei fremden Mandanten: Existenz wird nicht verraten (TC-MAND-01).
    return FachFehler("nicht_gefunden", f"{objekt} nicht gefunden.", status=404)


def verboten(nachricht: str = "Diese Aktion ist für deine Rolle nicht erlaubt.") -> FachFehler:
    return FachFehler("nicht_berechtigt", nachricht, status=403)
