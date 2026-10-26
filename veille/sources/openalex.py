"""OpenAlex : articles et preprints récents en sciences sociales et économie.

API ouverte : https://docs.openalex.org. Le paramètre `mailto` place les requêtes
dans le « polite pool » ; OPENALEX_API_KEY est facultative.
"""
from __future__ import annotations

import os
from datetime import date

import requests

from ..modele import Item

API = "https://api.openalex.org/works"


def collecter(config: dict, depuis: date) -> list[Item]:
    conf = config["openalex"]
    items: list[Item] = []
    for requete in conf["requetes"]:
        params = {
            "search": requete,
            "filter": ",".join([
                f"from_publication_date:{depuis.isoformat()}",
                "type:article|preprint|report",
                f"language:{'|'.join(conf.get('langues', ['en', 'fr']))}",
                f"primary_topic.field.id:{'|'.join(conf['champs'])}",
            ]),
            "sort": "publication_date:desc",
            "per_page": conf.get("par_requete", 25),
            "mailto": conf["mailto"],
        }
        if os.environ.get("OPENALEX_API_KEY"):
            params["api_key"] = os.environ["OPENALEX_API_KEY"]
        r = requests.get(API, params=params, timeout=30)
        if r.status_code == 400:
            # Filtre de champ disciplinaire refusé (syntaxe d'identifiant à vérifier) :
            # on relance sans lui, le préfiltre lexical prendra le relais
            print(f"::warning::OpenAlex a refusé le filtre de champ : {r.text[:200]}")
            params["filter"] = params["filter"].rsplit(",", 1)[0]
            r = requests.get(API, params=params, timeout=30)
        r.raise_for_status()
        items += [_vers_item(w) for w in r.json().get("results", [])]
    return items


def reconstruire_resume(index_inverse: dict | None) -> str:
    """OpenAlex fournit le résumé en index inversé {mot: [positions]}."""
    if not index_inverse:
        return ""
    positions = {p: mot for mot, ps in index_inverse.items() for p in ps}
    return " ".join(positions[i] for i in sorted(positions))


def _vers_item(w: dict) -> Item:
    lieu = (w.get("primary_location") or {})
    revue = (lieu.get("source") or {}).get("display_name", "")
    auteurs = ", ".join(a["author"]["display_name"] for a in w.get("authorships", [])[:3])
    url = w.get("doi") or lieu.get("landing_page_url") or w["id"]
    return Item(
        titre=w.get("display_name") or w.get("title") or "(sans titre)",
        url=url,
        canal="OpenAlex",
        type="Preprint" if w.get("type") == "preprint" else ("Rapport" if w.get("type") == "report" else "Étude publiée"),
        source=" — ".join(x for x in (auteurs, revue) if x),
        resume=reconstruire_resume(w.get("abstract_inverted_index"))[:1500],
        date_publication=date.fromisoformat(w["publication_date"]) if w.get("publication_date") else None,
    )
