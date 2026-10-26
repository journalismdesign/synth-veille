"""Instagram : lecture de l'export « Télécharger vos informations » (format JSON).

Aucune API n'expose les publications enregistrées d'un compte. Ce module sert de
rattrapage mensuel ; au quotidien, partager le post vers l'app Notion (voir
docs/instagram.md). Fichier attendu : your_instagram_activity/saved/saved_posts.json
"""
from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path

from ..modele import Item


def collecter_export(chemin: Path, depuis: date) -> list[Item]:
    donnees = json.loads(Path(chemin).read_text(encoding="utf-8"))
    # La clé racine a changé selon les versions de l'export : on accepte les deux
    entrees = donnees.get("saved_saved_media") or donnees.get("saved_media") or []
    items = []
    for e in entrees:
        auteur = e.get("title", "")
        for valeur in (e.get("string_map_data") or {}).values():
            href, ts = valeur.get("href"), valeur.get("timestamp")
            if not href:
                continue
            jour = datetime.fromtimestamp(ts, timezone.utc).date() if ts else None
            if jour and jour < depuis:
                continue
            items.append(Item(
                titre=f"Post Instagram de @{auteur}" if auteur else "Post Instagram enregistré",
                url=href,
                canal="Instagram",
                type="Post social",
                source=f"@{auteur}" if auteur else "Instagram",
                date_publication=jour,
            ))
    return items
