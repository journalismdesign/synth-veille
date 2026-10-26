"""Inoreader : articles étoilés et articles d'un tag (par défaut « Synth »).

Authentification OAuth2. Le jeton de rafraîchissement s'obtient une fois pour
toutes avec `python -m veille.inoreader_auth`, puis se stocke en secret
(INOREADER_REFRESH_TOKEN). Doc : https://www.inoreader.com/developers/
"""
from __future__ import annotations

import html
import os
import re
from datetime import date, datetime, timezone
from pathlib import Path

import requests

from ..modele import Item

API = "https://www.inoreader.com/reader/api/0"
JETON_URL = "https://www.inoreader.com/oauth2/token"


def jeton_acces() -> str:
    r = requests.post(JETON_URL, timeout=30, data={
        "client_id": os.environ["INOREADER_APP_ID"],
        "client_secret": os.environ["INOREADER_APP_KEY"],
        "grant_type": "refresh_token",
        "refresh_token": os.environ["INOREADER_REFRESH_TOKEN"],
    })
    r.raise_for_status()
    donnees = r.json()
    nouveau = donnees.get("refresh_token")
    if nouveau and nouveau != os.environ["INOREADER_REFRESH_TOKEN"]:
        memoriser_nouveau_jeton(nouveau)
    return donnees["access_token"]


def memoriser_nouveau_jeton(jeton: str) -> None:
    """Inoreader fait tourner le refresh_token : on le confie à l'étape suivante du workflow.

    Le jeton est masqué dans les journaux GitHub, puis écrit dans un fichier temporaire
    (INOREADER_NOUVEAU_JETON_FICHIER) que l'étape « Mise à jour du jeton Inoreader »
    recopie dans le secret du dépôt. Hors GitHub Actions, on se contente d'avertir.
    """
    print(f"::add-mask::{jeton}")
    chemin = os.environ.get("INOREADER_NOUVEAU_JETON_FICHIER")
    if not chemin:
        print("::warning::Inoreader a émis un nouveau refresh_token, non mémorisé (pas de fichier cible).")
        return
    fichier = Path(chemin)
    fichier.write_text(jeton, encoding="utf-8")
    fichier.chmod(0o600)


def collecter(config: dict, depuis: date) -> list[Item]:
    conf = config["inoreader"]
    entetes = {"Authorization": f"Bearer {jeton_acces()}"}
    ot = int(datetime.combine(depuis, datetime.min.time(), timezone.utc).timestamp())
    items: list[Item] = []
    for flux in conf["flux"]:
        continuation = None
        while True:
            params = {"n": 100, "ot": ot}
            if continuation:
                params["c"] = continuation
            r = requests.get(f"{API}/stream/contents/{flux}", headers=entetes, params=params, timeout=30)
            r.raise_for_status()
            donnees = r.json()
            items += [_vers_item(a) for a in donnees.get("items", []) if _url(a)]
            continuation = donnees.get("continuation")
            if not continuation:
                break
    return items


def _url(article: dict) -> str | None:
    for cle in ("canonical", "alternate"):
        if article.get(cle):
            return article[cle][0].get("href")
    return None


def _vers_item(a: dict) -> Item:
    resume = re.sub(r"<[^>]+>", " ", (a.get("summary") or {}).get("content", ""))
    return Item(
        titre=html.unescape(a.get("title", "(sans titre)")),
        url=_url(a),
        canal="Inoreader",
        type="Actu",
        source=(a.get("origin") or {}).get("title", ""),
        resume=re.sub(r"\s+", " ", html.unescape(resume)).strip()[:1500],
        date_publication=datetime.fromtimestamp(a["published"], timezone.utc).date() if a.get("published") else None,
    )
