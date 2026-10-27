"""Top de la semaine : coche « Top semaine » sur les N fiches les plus intéressantes.

    python -m veille.top              # 30 fiches, fenêtre de 7 jours
    python -m veille.top --sec        # affiche le classement sans rien écrire

Notion ne sait pas limiter une vue à N lignes : la vue « Cette semaine » filtre donc sur
cette case, recalculée après chaque collecte. Les fiches retenues par Gerald passent
toujours en tête ; les autres sont classées par Score éditorial, puis Résonance, puis
Pré-score (une fiche pas encore notée par le trieur ne passe qu'après les notées).
"""
from __future__ import annotations

import argparse
import sys

RETENUS = {"Retenu NL", "Retenu article", "Candidat"}


def valeurs(page: dict) -> dict:
    p = page["properties"]
    nombre = lambda nom: (p.get(nom) or {}).get("number")
    return {
        "id": page["id"],
        "titre": "".join(x["plain_text"] for x in p.get("Titre", {}).get("title", [])),
        "statut": ((p.get("Statut") or {}).get("status") or {}).get("name", ""),
        "score": nombre("Score"),
        "resonance": nombre("Résonance") or 0,
        "prescore": nombre("Pré-score") or 0,
        "top": bool((p.get("Top semaine") or {}).get("checkbox")),
    }


def classer(fiches: list[dict], n: int) -> list[dict]:
    """Les n fiches à cocher, dans l'ordre d'intérêt."""
    eligibles = [f for f in fiches if f["statut"] != "Écarté"]
    eligibles.sort(key=lambda f: (f["statut"] in RETENUS, f["score"] is not None,
                                  f["score"] or 0, f["resonance"], f["prescore"]), reverse=True)
    return eligibles[:n]


def main() -> int:
    p = argparse.ArgumentParser(description="Coche « Top semaine » sur les meilleures fiches")
    p.add_argument("-n", type=int, default=30)
    p.add_argument("--jours", type=int, default=7)
    p.add_argument("--sec", action="store_true")
    args = p.parse_args()

    from .notion import Notion
    notion = Notion()
    recentes = [valeurs(pg) for pg in notion.pages_recentes(args.jours)]
    top = classer(recentes, args.n)
    ids_top = {f["id"] for f in top}
    for rang, f in enumerate(top, 1):
        print(f"{rang:2}. {f['score'] if f['score'] is not None else '—':>4}  {f['statut']:14} {f['titre'][:80]}")

    # Décocher aussi les fiches plus anciennes encore marquées (semaine précédente)
    cochees = [valeurs(pg) for pg in notion.pages({"property": "Top semaine", "checkbox": {"equals": True}})]
    a_decocher = [f for f in cochees if f["id"] not in ids_top]
    a_cocher = [f for f in top if not f["top"]]
    print(f"\n+{len(a_cocher)} cochées, -{len(a_decocher)} décochées")
    if not args.sec:
        for f in a_cocher:
            notion.maj(f["id"], {"Top semaine": {"checkbox": True}})
        for f in a_decocher:
            notion.maj(f["id"], {"Top semaine": {"checkbox": False}})
    return 0


if __name__ == "__main__":
    sys.exit(main())
