# synth-veille — consignes pour Claude

Chaîne de veille éditoriale de Synth (synthmedia.fr), média indépendant techno-critique.

- **Hub** : base Notion « Veille Synth » (identifiants dans `config/veille.toml`, section `[notion]`).
- **Collecte** : scripts Python déterministes (`veille/`), lancés par GitHub Actions toutes les 6 h.
  Pas d'IA dans la collecte.
- **Jugement éditorial** : sous-agents dans `.claude/agents/` (trieur, verificateur, chercheur,
  redacteur, metteur-en-forme), orchestrés par les skills `/veille-hebdo` et `/redaction-hebdo`.
- **Point de décision humain** : Gerald passe les fiches en « Retenu NL » / « Retenu article ».
  Aucun agent ne prend cette décision à sa place, et rien n'est publié hors de Notion et
  des brouillons Canva. Seule exception, interne : le courriel de proposition hebdomadaire
  à la rédaction (`config/veille.toml`, `[diffusion]`).
- **Calendrier** : choix de Gerald jeudi midi, publication vendredi après-midi.

**Charte codée** : `charte/charte.toml` est la source de vérité de la ligne éditoriale
(règles identifiées P-, F-, Q-, E-, S-, D-). Tout agent la charge en prémisse
(`python -m veille.charte`). Contrôles automatiques : `python -m veille.preuves` (protocole
bloquant des preuves) et `python -m veille.relecture` (écriture, volume). Une erreur se
corrige dans la règle (`/corriger-regle`) et se consigne dans `docs/journal-charte.md`.

Référentiels à respecter : page Notion « Positionnement de Synth et de notre journalisme »,
`docs/grille-notation.md`, `docs/gabarits.md`.

Code : Python ≥ 3.11, dépendance unique `requests`, commentaires en français.
Tests hors ligne : `pytest -q`. Ajouter une source = un module `veille/sources/<nom>.py`
exposant `collecter(config, depuis) -> list[Item]`, déclaré dans `veille/collecte.py`.
