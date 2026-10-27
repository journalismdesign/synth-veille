"""Point d'entrée de la collecte.

    python -m veille.collecte --depuis 2                # toutes les sources, 2 derniers jours
    python -m veille.collecte --sources openalex,hal --sec   # affiche sans écrire dans Notion
    python -m veille.collecte --instagram export/saved_posts.json --depuis 60

Les sources en échec n'arrêtent pas la collecte : elles sont signalées et le code
de sortie vaut 1 pour que GitHub Actions le rende visible.
"""
from __future__ import annotations

import argparse
import sys
from datetime import date, timedelta
from pathlib import Path

from .modele import ACADEMIQUE, AUTRE, ORIGINES_PAR_CANAL, SAUVE, Item, a_ancrage_tech, charger_config, prequalifier
from .sources import arxiv, hal, inoreader, instagram, openalex, socarxiv

SOURCES = {"inoreader": inoreader, "openalex": openalex, "arxiv": arxiv, "hal": hal, "socarxiv": socarxiv}


def selectionner(items: list[Item], config: dict) -> list[Item]:
    """Ordonne par priorité (sauvés > flux > académique), préfiltre et dédoublonne."""
    axes = config["axes"]
    ancrage = config["prefiltre"]["ancrage_tech"]
    # Seuil par origine : les articles sauvés passent toujours, le flux est filtré moins sévèrement
    seuils = {SAUVE: None, ACADEMIQUE: config["prefiltre"]["score_minimum_academique"]}
    seuil_defaut = config["prefiltre"]["score_minimum_flux"]

    for it in items:
        it.origine = it.origine or ORIGINES_PAR_CANAL.get(it.canal, AUTRE)
    items = sorted(items, key=lambda i: i.origine)  # tri stable

    # Le premier vu, donc le plus prioritaire, gagne le dédoublonnage
    retenus, vus = [], set()
    for it in items:
        prequalifier(it, axes)
        seuil = seuils.get(it.origine, seuil_defaut)
        if seuil is not None and (it.prescore < seuil or not a_ancrage_tech(it, ancrage)):
            continue
        if it.empreinte in vus:
            continue
        vus.add(it.empreinte)
        retenus.append(it)
    return retenus


def main() -> int:
    p = argparse.ArgumentParser(description="Collecte de veille Synth vers Notion")
    p.add_argument("--sources", default=",".join(SOURCES), help="liste séparée par des virgules")
    p.add_argument("--depuis", type=int, default=2, help="nombre de jours en arrière")
    p.add_argument("--instagram", type=Path, help="chemin d'un saved_posts.json exporté")
    p.add_argument("--sec", action="store_true", help="n'écrit rien dans Notion, affiche seulement")
    args = p.parse_args()

    config = charger_config()
    depuis = date.today() - timedelta(days=args.depuis)

    items: list[Item] = []
    echecs = []
    for nom in [s.strip() for s in args.sources.split(",") if s.strip()]:
        try:
            recus = SOURCES[nom].collecter(config, depuis)
            print(f"{nom} : {len(recus)} éléments")
            items += recus
        except Exception as e:  # une source cassée ne doit pas bloquer les autres
            echecs.append(nom)
            print(f"::error::{nom} : {e}", file=sys.stderr)
    if args.instagram:
        items += instagram.collecter_export(args.instagram, depuis)

    retenus = selectionner(items, config)
    print(f"Après préfiltre et dédoublonnage : {len(retenus)} / {len(items)}")

    if args.sec:
        for it in sorted(retenus, key=lambda i: (i.origine, -i.prescore)):
            print(f"[{it.origine[:1]} {it.canal:9}] {it.prescore:2} {it.titre[:90]}  {it.url}")
    else:
        from .notion import Notion
        notion = Notion()
        bilan = [notion.ajouter(it) for it in retenus]
        print(f"Notion : {bilan.count('cree')} nouvelles fiches, {bilan.count('promu')} promues en « Sauvé »")

    return 1 if echecs else 0


if __name__ == "__main__":
    sys.exit(main())
