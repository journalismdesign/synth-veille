"""Chargement de la charte codée (charte/charte.toml), partagé par la relecture et les preuves."""
from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

CHARTE = Path(__file__).resolve().parent.parent / "charte" / "charte.toml"


@dataclass(frozen=True)
class Regle:
    id: str
    famille: str
    texte: str
    controle: str
    severite: str


@lru_cache(maxsize=1)
def charger() -> dict:
    with CHARTE.open("rb") as f:
        return tomllib.load(f)


def regles() -> dict[str, Regle]:
    return {r["id"]: Regle(**r) for r in charger()["regle"]}


def lexique() -> list[tuple[str, str, re.Pattern]]:
    """(id de règle, sévérité, motif compilé) pour chaque expression interdite."""
    return [(bloc["regle"], bloc["severite"], re.compile(m, re.IGNORECASE))
            for bloc in charger()["lexique"] for m in bloc["motifs"]]


def premisse() -> str:
    """Texte des règles à injecter en tête de chaque tâche d'agent."""
    lignes = [f"Charte Synth v{charger()['version']} — règles applicables :"]
    lignes += [f"[{r.id}] ({r.severite}) {r.texte}" for r in regles().values()]
    return "\n".join(lignes)


if __name__ == "__main__":
    print(premisse())
