"""Écriture des items dans la base Notion « Veille Synth », avec déduplication.

Utilise l'API REST de Notion (intégration interne, jeton NOTION_TOKEN).
La déduplication repose sur la propriété « Empreinte » (hash de l'URL normalisée).
"""
from __future__ import annotations

import os
import time
from datetime import date, timedelta

import requests

from .modele import SAUVE, Item, empreinte_url

API = "https://api.notion.com/v1"
VERSION = "2022-06-28"
LIMITE_TEXTE = 1900  # Notion limite un bloc rich_text à 2000 caractères


class Notion:
    def __init__(self, jeton: str | None = None, base_id: str | None = None):
        self.base_id = base_id or os.environ["NOTION_DATABASE_ID"]
        self._cache: dict[str, tuple[str, str]] | None = None
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

    def pages(self, filtre: dict) -> list[dict]:
        """Toutes les fiches répondant à un filtre de l'API Notion (pagination incluse)."""
        resultat, curseur = [], None
        while True:
            corps = {"page_size": 100, "filter": filtre, **({"start_cursor": curseur} if curseur else {})}
            res = self._requete("POST", f"/databases/{self.base_id}/query", json=corps)
            resultat += res.get("results", [])
            if not res.get("has_more"):
                return resultat
            curseur = res["next_cursor"]

    def pages_recentes(self, jours: int) -> list[dict]:
        """Fiches ajoutées depuis `jours` jours (radar, top de la semaine)."""
        depuis = (date.today() - timedelta(days=jours)).isoformat()
        return self.pages({"timestamp": "created_time", "created_time": {"on_or_after": depuis}})

    def maj(self, page_id: str, proprietes: dict) -> None:
        self._requete("PATCH", f"/pages/{page_id}", json={"properties": proprietes})
        time.sleep(0.35)

    def _index(self) -> dict[str, tuple[str, str]]:
        """Charge une fois toutes les fiches : empreinte -> (id de page, origine).

        Une requête par article coûtait plusieurs minutes dès que le flux Inoreader complet
        est lu ; une base de quelques milliers de fiches se parcourt en quelques pages.
        """
        if self._cache is None:
            self._cache, curseur = {}, None
            while True:
                corps = {"page_size": 100, **({"start_cursor": curseur} if curseur else {})}
                res = self._requete("POST", f"/databases/{self.base_id}/query", json=corps)
                for page in res.get("results", []):
                    p = page["properties"]
                    emp = "".join(x["plain_text"] for x in p.get("Empreinte", {}).get("rich_text", []))
                    origine = ((p.get("Origine") or {}).get("select") or {}).get("name", "")
                    # Fiches créées hors collecte (veille quotidienne, ajout manuel) : sans
                    # empreinte, on la recalcule depuis l'URL pour ne pas créer de doublon
                    url = (p.get("URL") or {}).get("url") or ""
                    emp = emp or (empreinte_url(url) if url else "")
                    if emp:
                        self._cache[emp] = (page["id"], origine)
                if not res.get("has_more"):
                    break
                curseur = res["next_cursor"]
        return self._cache

    def ajouter(self, item: Item) -> str:
        """Crée la fiche si elle est nouvelle. Renvoie « cree », « promu » ou « existe ».

        Un article déjà collecté via le flux puis sauvé par Gerald est « promu » : son
        origine passe à « Sauvé » pour remonter en tête de la vue de la semaine.
        """
        index = self._index()
        if item.empreinte in index:
            page_id, origine = index[item.empreinte]
            if item.origine == SAUVE and origine != SAUVE:
                self._requete("PATCH", f"/pages/{page_id}", json={
                    "properties": {"Origine": {"select": {"name": SAUVE}}}})
                index[item.empreinte] = (page_id, SAUVE)
                return "promu"
            return "existe"
        props = {
            "Titre": {"title": [_texte(item.titre)]},
            "URL": {"url": item.url},
            "Canal": {"select": {"name": item.canal}},
            "Type": {"select": {"name": item.type}},
            "Source": {"rich_text": [_texte(item.source)]},
            "Résumé": {"rich_text": [_texte(item.resume)]},
            "Empreinte": {"rich_text": [_texte(item.empreinte)]},
            "Statut": {"status": {"name": "Collecté"}},
            "Pré-score": {"number": item.prescore},
        }
        if item.origine:
            props["Origine"] = {"select": {"name": item.origine}}
        if item.axes:
            props["Axes"] = {"multi_select": [{"name": a} for a in item.axes]}
        if item.date_publication:
            props["Date publication"] = {"date": {"start": item.date_publication.isoformat()}}
        page = self._requete("POST", "/pages", json={
            "parent": {"database_id": self.base_id}, "properties": props,
        })
        index[item.empreinte] = (page["id"], item.origine)
        time.sleep(0.35)
        return "cree"


def _texte(contenu: str) -> dict:
    contenu = (contenu or "").strip()
    if len(contenu) > LIMITE_TEXTE:
        contenu = contenu[:LIMITE_TEXTE].rsplit(" ", 1)[0] + "…"
    return {"type": "text", "text": {"content": contenu}}
