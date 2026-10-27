"""Radar de résonance (règle S-03) : repère les sujets traités par plusieurs sources
indépendantes dans la période, plutôt que les plus bruyants.

    python -m veille.radar --jours 7          # écrit Résonance et Sujet radar dans Notion
    python -m veille.radar --jours 7 --sec    # affiche les groupes sans rien écrire

Méthode volontairement simple et lisible : deux fiches parlent du même sujet si leurs
titres partagent assez de termes significatifs (dont au moins un nom propre ou un terme
long). Les groupes sont formés par transitivité. La résonance d'un groupe est le nombre
de sources (domaines) distinctes. Limite connue : un même sujet traité en français et en
anglais n'est pas rapproché.
"""
from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from collections import Counter
from datetime import date
from urllib.parse import urlsplit

MOTS_VIDES = set("""
le la les un une des du de d l au aux et ou en dans sur pour par avec sans sous vers chez
ce cet cette ces son sa ses leur leurs qui que quoi dont où ne pas plus moins est sont être
a ont avoir fait faire comme mais donc car si tout tous toute toutes après avant entre
nouveau nouvelle nouveaux selon face contre depuis encore aussi déjà très bien
the a an of to in on for with by from at as is are was be it its this that these those
and or but not no new how why what when who will can could would should has have had
about after over into than more most just our your their his her we you they he she
""".split())


def termes(titre: str) -> set[str]:
    """Termes significatifs d'un titre : minuscules, sans accents, hors mots vides."""
    sans_accents = unicodedata.normalize("NFKD", titre).encode("ascii", "ignore").decode()
    mots = re.findall(r"[A-Za-z0-9][A-Za-z0-9-]+", sans_accents)
    return {m.lower() for m in mots if m.lower() not in MOTS_VIDES and len(m) >= 3}


def noms_propres(titre: str) -> set[str]:
    """Mots à majuscule hors début de titre (heuristique : entités nommées)."""
    mots = re.findall(r"\b[A-ZÀ-Ý][\w-]+", titre)[1:]
    return {unicodedata.normalize("NFKD", m).encode("ascii", "ignore").decode().lower() for m in mots}


def meme_sujet(a: dict, b: dict) -> bool:
    communs = a["termes"] & b["termes"]
    if len(communs) < 2:
        return False
    jaccard = len(communs) / len(a["termes"] | b["termes"])
    entite = bool(communs & a["noms"] & b["noms"]) or any(len(t) >= 8 for t in communs)
    return (jaccard >= 0.3 and entite) or len(communs) >= 4


def domaine(url: str) -> str:
    hote = urlsplit(url or "").netloc.lower()
    return hote.removeprefix("www.")


def grouper(fiches: list[dict]) -> list[list[dict]]:
    """Composantes connexes par union-find sur la relation « même sujet »."""
    parent = list(range(len(fiches)))

    def racine(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(len(fiches)):
        for j in range(i + 1, len(fiches)):
            if meme_sujet(fiches[i], fiches[j]):
                parent[racine(i)] = racine(j)
    groupes: dict[int, list[dict]] = {}
    for i, f in enumerate(fiches):
        groupes.setdefault(racine(i), []).append(f)
    return [g for g in groupes.values() if len(g) > 1]


def resonance(groupe: list[dict]) -> int:
    return len({f["domaine"] for f in groupe if f["domaine"]})


def libelle(groupe: list[dict], numero: int) -> str:
    frequents = Counter(t for f in groupe for t in f["termes"]).most_common(3)
    return f"R{date.today():%y%W}-{numero:02d} · " + " ".join(t for t, _ in frequents)


def depuis_notion(pages: list[dict]) -> list[dict]:
    fiches = []
    for p in pages:
        props = p["properties"]
        titre = "".join(x["plain_text"] for x in props.get("Titre", {}).get("title", []))
        url = (props.get("URL") or {}).get("url") or ""
        if titre:
            fiches.append({"id": p["id"], "titre": titre, "termes": termes(titre),
                           "noms": noms_propres(titre), "domaine": domaine(url)})
    return fiches


def main() -> int:
    p = argparse.ArgumentParser(description="Radar de résonance multi-sources")
    p.add_argument("--jours", type=int, default=7)
    p.add_argument("--sec", action="store_true")
    args = p.parse_args()

    from .notion import Notion
    notion = Notion()
    fiches = depuis_notion(notion.pages_recentes(args.jours))
    groupes = sorted(grouper(fiches), key=resonance, reverse=True)
    print(f"{len(fiches)} fiches · {len(groupes)} sujets partagés")
    for n, g in enumerate(groupes, 1):
        r, nom = resonance(g), libelle(g, n)
        print(f"  {r} sources · {nom}")
        for f in g:
            print(f"      - {f['titre'][:90]} ({f['domaine']})")
            if not args.sec:
                notion.maj(f["id"], {
                    "Résonance": {"number": r},
                    "Sujet radar": {"rich_text": [{"type": "text", "text": {"content": nom}}]},
                })
    return 0


if __name__ == "__main__":
    sys.exit(main())
