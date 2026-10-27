---
name: corriger-regle
description: Quand Gerald signale une erreur dans un contenu Synth (fait faux, tic d'écriture, mauvais sujet, mauvais format), remonte à la règle de la charte qui l'a laissée passer, propose son amendement, et après accord met à jour charte/charte.toml, le journal et les tests. À lancer avec la description de l'erreur.
---

# Corriger la règle, pas seulement le texte (règle P-03)

Entrée : la description de l'erreur par Gerald, et si possible le lien du contenu ou de la fiche.

1. **Qualifier l'erreur.** Fait (famille F), prisme oublié (Q), écriture (E), sélection (S)
   ou distribution (D) ? Cite le passage fautif.
2. **Trouver la règle.** Lis `charte/charte.toml`. Trois cas :
   - une règle existait mais n'a pas été appliquée → pourquoi ? (contrôle « agent » non
     exécuté, lexique trop étroit, consigne d'agent ambiguë) ;
   - une règle existait mais était mal formulée → proposer la reformulation ;
   - aucune règle ne couvrait le cas → proposer une nouvelle règle avec un identifiant libre
     dans la bonne famille.
3. **Proposer, ne pas appliquer.** Présente à Gerald : règle visée, formulation actuelle,
   formulation proposée, mode de contrôle (auto / agent / humain), et si « auto » le motif
   ou le test qui l'attrapera. Attends son accord explicite.
4. **Appliquer après accord.**
   - Modifie `charte/charte.toml` (incrémente `version` selon le barème du journal).
   - Si le contrôle est automatique : ajoute le motif au lexique ou le contrôle dans
     `veille/relecture.py` / `veille/preuves.py`, et un test dans `tests/test_charte.py`
     reproduisant l'erreur d'origine.
   - Si le contrôle est fait par un agent : amende la consigne de l'agent concerné dans
     `.claude/agents/`.
   - Ajoute l'entrée datée dans `docs/journal-charte.md`.
   - `pytest -q`, puis commit et PR.
5. **Corriger le contenu** lui-même seulement ensuite, et le relancer dans
   `python -m veille.relecture` pour vérifier que la nouvelle règle l'attrape.
