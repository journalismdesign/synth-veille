"""SocArXiv : preprints de sciences sociales, via l'API OSF.

L'API ne propose pas de recherche plein texte fiable : on récupère les dépôts
récents et le préfiltre lexical (modele.prequalifier) fait le tri.
Doc : https://developer.osf.io/
"""
from __future__ import annotations

from datetime import date

import requests

from ..modele import Item

API = "https://api.osf.io/v2/preprints/"


def collecter(config: dict, depuis: date) -> list[Item]:
    conf = config.get("socarxiv", {})
    url, params = API, {
        "filter[provider]": "socarxiv",
        "filter[date_created][gte]": depuis.isoformat(),
        "page[size]": 100,
    }
    items: list[Item] = []
    for _ in range(conf.get("pages_max", 5)):
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        donnees = r.json()
        items += [_vers_item(p) for p in donnees.get("data", [])]
        url, params = (donnees.get("links") or {}).get("next"), None
        if not url:
            break
    return items


def _vers_item(p: dict) -> Item:
    a = p["attributes"]
    return Item(
        titre=a.get("title") or "(sans titre)",
        url=(p.get("links") or {}).get("html") or f"https://osf.io/preprints/socarxiv/{p['id']}",
        canal="SocArXiv",
        type="Preprint",
        source="SocArXiv",
        resume=(a.get("description") or "")[:1500],
        date_publication=date.fromisoformat(a["date_created"][:10]) if a.get("date_created") else None,
    )
