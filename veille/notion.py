"""Écriture des items dans la base Notion « Veille Synth », avec déduplication.

Utilise l'API REST de Notion (intégration interne, jeton NOTION_TOKEN).
La déduplication repose sur la propriété « Empreinte » (hash de l'URL normalisée).
"""
from __future__ import annotations

import os
import time

import requests

from .modele import Item

API = "https://api.notion.com/v1"
VERSION = "2022-06-28"
LIMITE_TEXTE = 1900  # Notion limite un bloc rich_text à 2000 caractères


class Notion:
    def __init__(self, jeton: str | None = None, base_id: str | None = None):
        self.base_id = base_id or os.environ["NOTION_DATABASE_ID"]
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {jeton or os.environ['NOTION_TOKEN']}",
            "Notion-Version": VERSION,
            "Content-Type": "application/json",
        })

    def _requete(self, methode: str, chemin: str, **kw) -> dict:
        # Notion limite à ~3 requêtes/s : on réessaie sur 429 en respectant Retry-After
        for tentative in range(5):
            r = self.session.request(methode, f"{API}{chemin}", timeout=30, **kw)
            if r.status_code == 429:
                time.sleep(float(r.headers.get("Retry-After", 2 ** tentative)))
                continue
            r.raise_for_status()
            return r.json()
        raise RuntimeError(f"Notion : trop de requêtes refusées sur {chemin}")

    def existe(self, empreinte: str) -> bool:
        res = self._requete("POST", f"/databases/{self.base_id}/query", json={
            "filter": {"property": "Empreinte", "rich_text": {"equals": empreinte}},
            "page_size": 1,
        })
        return bool(res.get("results"))

    def ajouter(self, item: Item) -> bool:
        """Crée la fiche si elle n'existe pas. Renvoie True si une fiche a été créée."""
        if self.existe(item.empreinte):
            return False
        props = {
            "Titre": {"title": [_texte(item.titre)]},
            "URL": {"url": item.url},
            "Canal": {"select": {"name": item.canal}},
            "Type": {"select": {"name": item.type}},
            "Source": {"rich_text": [_texte(item.source)]},
            "Résumé": {"rich_text": [_texte(item.resume)]},
            "Empreinte": {"rich_text": [_texte(item.empreinte)]},
            "Statut": {"status": {"name": "Collecté"}},
        }
        if item.axes:
            props["Axes"] = {"multi_select": [{"name": a} for a in item.axes]}
        if item.date_publication:
            props["Date publication"] = {"date": {"start": item.date_publication.isoformat()}}
        self._requete("POST", "/pages", json={
            "parent": {"database_id": self.base_id}, "properties": props,
        })
        time.sleep(0.35)
        return True


def _texte(contenu: str) -> dict:
    contenu = (contenu or "").strip()
    if len(contenu) > LIMITE_TEXTE:
        contenu = contenu[:LIMITE_TEXTE].rsplit(" ", 1)[0] + "…"
    return {"type": "text", "text": {"content": contenu}}
