"""Passwörter (BE-02, Argon2id) und Konfiguration laden.

Beweist: Passwörter werden nie im Klartext gespeichert; die Prüfung verwendet Argon2id.
"""
from pathlib import Path

import yaml
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

CONFIG_PFAD = Path(__file__).resolve().parent.parent / "config" / "basis.yaml"


def lade_basis_konfig(pfad: Path = CONFIG_PFAD) -> dict:
    with open(pfad, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def passwort_hasher(cfg: dict) -> PasswordHasher:
    a = cfg["sicherheit"]["argon2"]
    return PasswordHasher(time_cost=a["zeit_kosten"], memory_cost=a["speicher_kib"], parallelism=a["parallelitaet"])


def hashe_passwort(klartext: str, cfg: dict) -> str:
    if len(klartext) < 10:
        raise ValueError("Passwort muss mindestens 10 Zeichen haben")
    return passwort_hasher(cfg).hash(klartext)


def pruefe_passwort(hash_wert: str, klartext: str, cfg: dict) -> bool:
    try:
        return passwort_hasher(cfg).verify(hash_wert, klartext)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False
