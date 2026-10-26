"""arXiv : preprints des catégories « Computers and Society », économie, IHM.

API Atom : https://info.arxiv.org/help/api/. arXiv demande ≥ 3 s entre requêtes.
"""
from __future__ import annotations

import time
import xml.etree.ElementTree as ET
from datetime import date, datetime

import requests

from ..modele import Item

API = "https://export.arxiv.org/api/query"
NS = {"a": "http://www.w3.org/2005/Atom"}


def collecter(config: dict, depuis: date) -> list[Item]:
    conf = config["arxiv"]
    items: list[Item] = []
    for categorie in conf["categories"]:
        r = requests.get(API, timeout=60, params={
            "search_query": f"cat:{categorie}",
            "sortBy": "submittedDate",
            "sortOrder": "descending",
            "max_results": conf.get("par_categorie", 100),
        })
        r.raise_for_status()
        items += [i for i in analyser(r.text) if i.date_publication and i.date_publication >= depuis]
        time.sleep(3)
    return items


def analyser(atom: str) -> list[Item]:
    racine = ET.fromstring(atom)
    items = []
    for e in racine.findall("a:entry", NS):
        texte = lambda balise: " ".join((e.findtext(balise, "", NS) or "").split())
        auteurs = [a.findtext("a:name", "", NS) for a in e.findall("a:author", NS)]
        publie = texte("a:published")
        items.append(Item(
            titre=texte("a:title"),
            url=texte("a:id").replace("http://", "https://"),
            canal="arXiv",
            type="Preprint",
            source=", ".join(auteurs[:3]) + (" et al." if len(auteurs) > 3 else ""),
            resume=texte("a:summary")[:1500],
            date_publication=datetime.fromisoformat(publie.replace("Z", "+00:00")).date() if publie else None,
        ))
    return items
