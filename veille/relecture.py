"""Relecture automatique d'un brouillon Markdown contre la charte codée.

    python -m veille.relecture brouillon.md [--format article|newsletter|carrousel|linkedin]

Signale chaque écart avec l'identifiant de la règle enfreinte. Code de sortie 1 si au
moins un écart est « bloquant » : le brouillon ne doit pas être proposé à Gerald en l'état.
Ce contrôle est un filet, pas un relecteur : il ne remplace ni l'agent ni Gerald.
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from .charte import charger, lexique

MARQUEUR_PREUVE = re.compile(r"\[P\d+\]")
TRIPTYQUE = re.compile(r"\b[\w’'-]{3,}, [\w’'-]{3,},? et [\w’'-]{3,}\b")
SIGNES_ARTICLE = (2700, 3300)


@dataclass
class Ecart:
    regle: str
    severite: str
    ligne: int
    extrait: str
    message: str = ""

    def __str__(self) -> str:
        loc = f"l.{self.ligne}" if self.ligne else "global"
        msg = f" — {self.message}" if self.message else ""
        return f"[{self.regle}] {self.severite.upper():8} {loc:>6}  « {self.extrait} »{msg}"


def prose(texte: str) -> str:
    """Texte publiable : sans marqueurs de preuve, sans encadré Sources, sans balisage."""
    corps = re.split(r"(?im)^#+\s*sources\b.*$", texte)[0]
    corps = MARQUEUR_PREUVE.sub("", corps)
    corps = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", corps)   # liens -> texte
    corps = re.sub(r"(?m)^#+\s*", "", corps)
    corps = re.sub(r"[*_`>]", "", corps)
    return corps


def compter_signes(texte: str) -> int:
    """Signes espaces comprises de la prose publiable, sans sauts de ligne multiples."""
    return len(re.sub(r"\s+", " ", prose(texte)).strip())


def relire(texte: str, format_: str = "article") -> list[Ecart]:
    ecarts: list[Ecart] = []
    hors_sources = re.split(r"(?im)^#+\s*sources\b.*$", texte)[0]
    lignes = hors_sources.splitlines()

    for n, ligne in enumerate(lignes, 1):
        for regle, severite, motif in lexique():
            for m in motif.finditer(ligne):
                ecarts.append(Ecart(regle, severite, n, m.group(0)))
        for mot in charger()["inclusif"]["mots"]:
            for m in re.finditer(rf"\b{mot}\b(?!·)", ligne, re.IGNORECASE):
                ecarts.append(Ecart("E-07", "alerte", n, m.group(0), "écrire au point médian"))
        if format_ in ("article", "newsletter", "linkedin") and re.match(r"\s*[-*•]\s+\S", ligne):
            ecarts.append(Ecart("E-08", "alerte", n, ligne.strip()[:60], "liste à puces dans la prose"))

    for n, paragraphe in enumerate(re.split(r"\n\s*\n", hors_sources), 1):
        if paragraphe.count("?") > 2:
            ecarts.append(Ecart("E-06", "alerte", 0, paragraphe.strip()[:60],
                                f"{paragraphe.count('?')} questions dans le paragraphe {n}"))

    triptyques = TRIPTYQUE.findall(prose(texte))
    signes = compter_signes(texte)
    if triptyques and len(triptyques) > max(2, signes // 1500):
        ecarts.append(Ecart("E-01", "alerte", 0, triptyques[0],
                            f"{len(triptyques)} énumérations ternaires pour {signes} signes"))

    if format_ == "article":
        bas, haut = SIGNES_ARTICLE
        if not bas <= signes <= haut:
            ecarts.append(Ecart("E-09", "bloquant", 0, f"{signes} signes",
                                f"attendu {bas}–{haut} (3 000 ± 10 %)"))
    return ecarts


def main() -> int:
    p = argparse.ArgumentParser(description="Relecture d'un brouillon contre la charte Synth")
    p.add_argument("fichier", type=Path)
    p.add_argument("--format", default="article", choices=["article", "newsletter", "carrousel", "linkedin"])
    args = p.parse_args()

    texte = args.fichier.read_text(encoding="utf-8")
    ecarts = relire(texte, args.format)
    for e in sorted(ecarts, key=lambda e: (e.severite != "bloquant", e.ligne)):
        print(e)
    bloquants = sum(e.severite == "bloquant" for e in ecarts)
    print(f"\n{compter_signes(texte)} signes · {len(ecarts)} écarts dont {bloquants} bloquants")
    return 1 if bloquants else 0


if __name__ == "__main__":
    sys.exit(main())
