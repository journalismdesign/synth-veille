"""HAL : archive ouverte de la recherche française, domaine SHS.

API Solr : https://api.archives-ouvertes.fr/docs/search
"""
from __future__ import annotations

from datetime import date

import requests

from ..modele import Item

API = "https://api.archives-ouvertes.fr/search/"
TYPES = {"ART": "Étude publiée", "UNDEFINED": "Preprint", "REPORT": "Rapport", "OUV": "Étude publiée",
         "COUV": "Étude publiée", "COMM": "Étude publiée", "THESE": "Étude publiée"}


def collecter(config: dict, depuis: date) -> list[Item]:
    conf = config["hal"]
    items: list[Item] = []
    for requete in conf["requetes"]:
        r = requests.get(API, timeout=30, params={
            "q": requete,
            "fq": [f"submittedDate_tdate:[{depuis.isoformat()}T00:00:00Z TO NOW]", "level0_domain_s:shs"],
            "fl": "title_s,uri_s,abstract_s,producedDate_s,authFullName_s,docType_s,journalTitle_s",
            "sort": "submittedDate_tdate desc",
            "rows": conf.get("par_requete", 30),
            "wt": "json",
        })
        r.raise_for_status()
        items += [_vers_item(d) for d in r.json()["response"]["docs"]]
    return items


def _premier(valeur) -> str:
    return (valeur[0] if isinstance(valeur, list) and valeur else valeur) or ""


def _vers_item(d: dict) -> Item:
    produit = _premier(d.get("producedDate_s"))
    try:
        # producedDate_s peut valoir « 2026 », « 2026-10 » ou « 2026-10-12 »
        dp = date.fromisoformat(produit) if len(produit) == 10 else None
    except ValueError:
        dp = None
    auteurs = d.get("authFullName_s", [])
    return Item(
        titre=_premier(d.get("title_s")) or "(sans titre)",
        url=d["uri_s"],
        canal="HAL",
        type=TYPES.get(d.get("docType_s", ""), "Étude publiée"),
        source=" — ".join(x for x in (", ".join(auteurs[:3]), _premier(d.get("journalTitle_s"))) if x),
        resume=_premier(d.get("abstract_s"))[:1500],
        date_publication=dp,
    )
