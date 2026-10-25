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

from .modele import Item, charger_config, prequalifier
from .sources import arxiv, hal, inoreader, instagram, openalex, socarxiv

SOURCES = {"inoreader": inoreader, "openalex": openalex, "arxiv": arxiv, "hal": hal, "socarxiv": socarxiv}
# Sources déjà curatées par Gerald : pas de préfiltre éliminatoire
SOURCES_CURATEES = {"Inoreader", "Instagram", "Manuel"}


def main() -> int:
    p = argparse.ArgumentParser(description="Collecte de veille Synth vers Notion")
    p.add_argument("--sources", default=",".join(SOURCES), help="liste séparée par des virgules")
    p.add_argument("--depuis", type=int, default=2, help="nombre de jours en arrière")
    p.add_argument("--instagram", type=Path, help="chemin d'un saved_posts.json exporté")
    p.add_argument("--sec", action="store_true", help="n'écrit rien dans Notion, affiche seulement")
    args = p.parse_args()

    config = charger_config()
    depuis = date.today() - timedelta(days=args.depuis)
    axes = config["axes"]
    seuil = config["prefiltre"]["score_minimum_academique"]

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

    # Préfiltre lexical, puis dédoublonnage interne au lot
    retenus, vus = [], set()
    for it in items:
        prequalifier(it, axes)
        if it.canal not in SOURCES_CURATEES and it.prescore < seuil:
            continue
        if it.empreinte in vus:
            continue
        vus.add(it.empreinte)
        retenus.append(it)
    print(f"Après préfiltre et dédoublonnage : {len(retenus)} / {len(items)}")

    if args.sec:
        for it in sorted(retenus, key=lambda i: -i.prescore):
            print(f"[{it.canal:9}] {it.prescore:2} {it.titre[:90]}  {it.url}")
    else:
        from .notion import Notion
        notion = Notion()
        nouveaux = sum(notion.ajouter(it) for it in retenus)
        print(f"Notion : {nouveaux} nouvelles fiches")

    return 1 if echecs else 0


if __name__ == "__main__":
    sys.exit(main())
