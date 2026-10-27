"""Modèle commun à toutes les sources : un « Item » de veille normalisé.

Chaque collecteur renvoie des Item ; seul le module notion.py sait les écrire.
Cela permet d'ajouter une source sans toucher au reste de la chaîne.
"""
from __future__ import annotations

import hashlib
import re
import tomllib
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

RACINE = Path(__file__).resolve().parent.parent
CONFIG = RACINE / "config" / "veille.toml"

# Paramètres de pistage retirés avant calcul de l'empreinte
PARAMS_PISTAGE = re.compile(r"^(utm_|fbclid|gclid|mc_|igshid|ref$|ref_src|s$|si$)")


# Libellés Notion de la propriété « Origine » : le préfixe numérique fixe l'ordre de tri
SAUVE, FLUX, ACADEMIQUE, AUTRE = "1 · Sauvé", "2 · Flux Inoreader", "3 · Académique", "4 · Autre"
ORIGINES_PAR_CANAL = {"Instagram": SAUVE, "Manuel": SAUVE, "Inoreader": FLUX,
                      "OpenAlex": ACADEMIQUE, "arXiv": ACADEMIQUE, "HAL": ACADEMIQUE, "SocArXiv": ACADEMIQUE}


@dataclass
class Item:
    titre: str
    url: str
    canal: str                      # Inoreader, OpenAlex, arXiv, HAL, SocArXiv, Instagram, Manuel
    type: str = "Actu"              # Actu, Étude publiée, Preprint, Rapport, Post social
    source: str = ""                # média, revue ou auteur·ices
    resume: str = ""
    date_publication: date | None = None
    axes: list[str] = field(default_factory=list)
    prescore: int = 0               # nombre de mots-clés d'axes trouvés (préfiltre, pas le score éditorial)
    origine: str = ""               # SAUVE, FLUX ou ACADEMIQUE (voir ORIGINES) ; ordre de priorité éditoriale

    @property
    def empreinte(self) -> str:
        return empreinte_url(self.url)


def normaliser_url(url: str) -> str:
    """URL canonique : https, sans www, sans pistage, sans fragment ni slash final."""
    parts = urlsplit(url.strip())
    hote = parts.netloc.lower().removeprefix("www.")
    requete = urlencode(
        sorted((k, v) for k, v in parse_qsl(parts.query) if not PARAMS_PISTAGE.match(k))
    )
    chemin = parts.path.rstrip("/") or "/"
    # Les DOI arrivent sous plusieurs hôtes : on les unifie
    if hote in {"dx.doi.org", "doi.org"}:
        chemin = chemin.lower()
    return urlunsplit(("https", hote, chemin, requete, ""))


def empreinte_url(url: str) -> str:
    return hashlib.sha1(normaliser_url(url).encode()).hexdigest()[:16]


def charger_config() -> dict:
    with CONFIG.open("rb") as f:
        return tomllib.load(f)


def motif(motcle: str) -> re.Pattern:
    """Mot entier par défaut ; un astérisque final autorise les suffixes."""
    m = motcle.lower()
    if m.endswith("*"):
        return re.compile(r"\b" + re.escape(m[:-1]))
    return re.compile(r"\b" + re.escape(m) + r"\b")


def prequalifier(item: Item, axes_motscles: dict[str, list[str]]) -> Item:
    """Préfiltre lexical bon marché : rattache l'item aux axes Synth par mots-clés.

    Ce n'est pas le tri éditorial (fait par l'agent « trieur »), seulement un moyen
    d'écarter le bruit des sources académiques avant d'encombrer Notion.
    """
    texte = f"{item.titre} {item.resume}".lower()
    for axe, motscles in axes_motscles.items():
        trouves = sum(1 for m in motscles if motif(m).search(texte))
        if trouves:
            item.axes.append(axe)
            item.prescore += trouves
    return item


def a_ancrage_tech(item: Item, motscles: list[str]) -> bool:
    """Vrai si titre ou résumé contiennent au moins un terme numérique (voir [prefiltre].ancrage_tech)."""
    texte = f"{item.titre} {item.resume}".lower()
    return any(motif(m).search(texte) for m in motscles)
