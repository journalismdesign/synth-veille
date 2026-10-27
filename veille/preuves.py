"""Protocole bloquant des preuves (règles F-01 à F-03).

Avant toute prose, le rédacteur dresse un tableau de preuves (TSV, une affirmation par
ligne). Le texte appelle chaque affirmation par son identifiant [Pn]. Ce module vérifie
le tableau, puis la cohérence entre le texte et le tableau.

    python -m veille.preuves preuves.tsv                      # valide le tableau seul
    python -m veille.preuves preuves.tsv --texte article.md   # + appels [Pn] du texte
    python -m veille.preuves preuves.tsv --texte article.md --nettoyer > propre.md

Colonnes : id, affirmation, type, source, statut, fiche
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

TYPES = {"Fait établi", "Hypothèse", "Projection", "Discours industriel", "Opinion"}
STATUTS = {"vérifié", "contesté", "non vérifié"}
COLONNES = ["id", "affirmation", "type", "source", "statut", "fiche"]
APPEL = re.compile(r"\[(P\d+)\]")
URL = re.compile(r"^https?://\S+$")


def lire(chemin: Path) -> list[dict]:
    with chemin.open(encoding="utf-8", newline="") as f:
        lignes = list(csv.DictReader(f, delimiter="\t"))
    manquantes = set(COLONNES) - set(lignes[0].keys() if lignes else COLONNES)
    if manquantes:
        raise ValueError(f"colonnes manquantes : {', '.join(sorted(manquantes))}")
    return lignes


def valider_tableau(lignes: list[dict]) -> list[str]:
    erreurs, vus = [], set()
    if not lignes:
        return ["[F-01] tableau de preuves vide : aucune prose ne peut être écrite"]
    for n, l in enumerate(lignes, 2):
        id_, type_, source, statut = (l.get(k, "").strip() for k in ("id", "type", "source", "statut"))
        if not re.fullmatch(r"P\d+", id_):
            erreurs.append(f"[F-01] ligne {n} : identifiant « {id_} » invalide (attendu P1, P2…)")
        elif id_ in vus:
            erreurs.append(f"[F-01] ligne {n} : identifiant {id_} en double")
        vus.add(id_)
        if not l.get("affirmation", "").strip():
            erreurs.append(f"[F-01] {id_} : affirmation vide")
        if type_ not in TYPES:
            erreurs.append(f"[F-02] {id_} : type « {type_} » inconnu ({', '.join(sorted(TYPES))})")
        if statut not in STATUTS:
            erreurs.append(f"[F-02] {id_} : statut « {statut} » inconnu ({', '.join(sorted(STATUTS))})")
        # Une opinion propre à Synth peut se passer de source ; tout le reste doit en avoir une
        if type_ != "Opinion" and not URL.match(source):
            erreurs.append(f"[F-03] {id_} : source manquante ou invalide pour un « {type_} »")
        if type_ == "Fait établi" and statut != "vérifié":
            erreurs.append(f"[F-03] {id_} : un fait établi doit être « vérifié » (statut : {statut})")
    return erreurs


def valider_texte(texte: str, lignes: list[dict]) -> tuple[list[str], list[str]]:
    """Renvoie (erreurs bloquantes, alertes)."""
    connus = {l["id"].strip() for l in lignes}
    appels = set(APPEL.findall(texte))
    erreurs = [f"[F-01] appel [{a}] sans ligne dans le tableau de preuves" for a in sorted(appels - connus)]
    if not appels:
        erreurs.append("[F-01] le texte n'appelle aucune preuve [Pn]")
    alertes = [f"[F-01] preuve {p} jamais appelée dans le texte" for p in sorted(connus - appels)]
    return erreurs, alertes


def nettoyer(texte: str) -> str:
    """Retire les appels [Pn] pour la version publiable."""
    return re.sub(r" ?\[P\d+\]", "", texte)


def main() -> int:
    p = argparse.ArgumentParser(description="Contrôle du tableau de preuves (charte F-01 à F-03)")
    p.add_argument("tableau", type=Path)
    p.add_argument("--texte", type=Path)
    p.add_argument("--nettoyer", action="store_true", help="affiche le texte sans appels [Pn] si tout est valide")
    args = p.parse_args()

    lignes = lire(args.tableau)
    erreurs, alertes = valider_tableau(lignes), []
    texte = args.texte.read_text(encoding="utf-8") if args.texte else None
    if texte is not None:
        e, alertes = valider_texte(texte, lignes)
        erreurs += e

    if args.nettoyer and texte is not None and not erreurs:
        print(nettoyer(texte))
        return 0
    for ligne in erreurs:
        print("BLOQUANT", ligne)
    for ligne in alertes:
        print("ALERTE  ", ligne)
    print(f"\n{len(lignes)} preuves · {len(erreurs)} erreurs bloquantes · {len(alertes)} alertes")
    return 1 if erreurs else 0


if __name__ == "__main__":
    sys.exit(main())
