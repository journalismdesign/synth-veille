# synth-veille — consignes pour Claude

Chaîne de veille éditoriale de Synth (synthmedia.fr), média indépendant techno-critique.

- **Hub** : base Notion « Veille Synth » (identifiants dans `config/veille.toml`, section `[notion]`).
- **Collecte** : scripts Python déterministes (`veille/`), lancés par GitHub Actions toutes les 6 h.
  Pas d'IA dans la collecte.
- **Jugement éditorial** : sous-agents dans `.claude/agents/` (trieur, verificateur, chercheur,
  redacteur, metteur-en-forme), orchestrés par les skills `/veille-hebdo` et `/redaction-hebdo`.
- **Point de décision humain** : Gerald passe les fiches en « Retenu NL » / « Retenu article ».
  Aucun agent ne prend cette décision à sa place, et rien n'est publié hors de Notion et
  des brouillons Canva.

Référentiels à respecter : page Notion « Positionnement de Synth et de notre journalisme »,
`docs/grille-notation.md`, `docs/gabarits.md`.

Code : Python ≥ 3.11, dépendance unique `requests`, commentaires en français.
Tests hors ligne : `pytest -q`. Ajouter une source = un module `veille/sources/<nom>.py`
exposant `collecter(config, depuis) -> list[Item]`, déclaré dans `veille/collecte.py`.
