# synth-veille

Chaîne de veille éditoriale de Synth : de la collecte (Inoreader, recherche académique,
Instagram) à la sélection hebdomadaire de 10 sujets, puis aux livrables — 5 brèves de
newsletter, un article de 3 000 signes, des carrousels Instagram, un post LinkedIn.

```
Inoreader ─┐
OpenAlex  ─┤                          ┌─ trieur (×n, parallèle)
arXiv     ─┤  GitHub Actions /6 h     │
HAL       ─┼──────────────────────▶ Notion ── /veille-hebdo ──┼─ verificateur (×3)
SocArXiv  ─┤  préfiltre + dédoublon.  « Veille Synth »        └─ chercheur (×2)
Instagram ─┘  (partage → Notion)          │
                                          ▼
                              « Sélection semaine N » ── Gerald valide (10 min)
                                          │
                                  /redaction-hebdo ── redacteur (×n) ── metteur-en-forme (Canva)
                                          ▼
                     Newsletter · Article · Carrousels · LinkedIn  (brouillons Notion/Canva)
```

## Calendrier

| Quand | Quoi | Qui |
|---|---|---|
| En continu | Collecte vers Notion | GitHub Actions |
| En continu | Partage des posts Instagram vers Notion | Gerald (5 s/post) |
| Dimanche soir | `/veille-hebdo` → page « Sélection semaine N » | Tâche planifiée Claude |
| Lundi matin | Cocher 5 « Retenu NL » + 1–2 « Retenu article » | Gerald |
| Lundi | `/redaction-hebdo` → brouillons | Claude |
| Lundi–mardi | Relecture, publication | Gerald |

## Mise en route

1. **Notion** — créer une intégration interne (https://www.notion.so/profile/integrations),
   capacités lecture/écriture de contenu ; partager avec elle la base « Veille Synth »
   (menu ··· → Connexions). Secrets : `NOTION_TOKEN`, `NOTION_DATABASE_ID =
   fdd64e2eb6514b498e43b99b7c22f0f0`.
2. **Inoreader** — créer une app développeur, puis lancer `python -m veille.inoreader_auth`
   sur votre machine (voir l'en-tête du fichier). Secrets : `INOREADER_APP_ID`,
   `INOREADER_APP_KEY`, `INOREADER_REFRESH_TOKEN`. Créer le tag **Synth** dans Inoreader.
   L'accès API dépend de votre offre Inoreader : à vérifier sur la page développeurs.
   Inoreader renouvelle ce jeton à chaque connexion : le workflow l'enregistre lui-même,
   à condition de lui donner le secret `GH_SECRETS_PAT` — un jeton GitHub *fine-grained*
   (https://github.com/settings/personal-access-tokens/new), limité au seul dépôt
   `synth-veille`, permission **Secrets : Read and write**, aucune autre.
3. **GitHub** — ajouter les secrets (Settings → Secrets and variables → Actions), puis lancer
   le workflow « Collecte veille » à la main une première fois avec `depuis = 14`.
4. **Instagram** — voir `docs/instagram.md`.
5. **Canva** — créer un modèle de marque « Synth carrousel » (8 pages, champs
   `titre_1…8`, `texte_1…8`) et reporter son ID dans `config/veille.toml` (facultatif).
6. **Tâche planifiée** — depuis une session Claude Code sur ce dépôt :
   « planifie /veille-hebdo chaque dimanche à 20 h 47, heure de Paris ».

## Usage local

```bash
pip install -r requirements.txt
pytest -q
python -m veille.collecte --sources openalex,arxiv,hal --depuis 7 --sec   # aperçu sans écrire
```

## Réglages

- `config/veille.toml` : axes et mots-clés du préfiltre, requêtes académiques, flux Inoreader.
- `docs/grille-notation.md` : barème éditorial sur 20 et règles d'équilibre.
- `docs/gabarits.md` : formats des livrables.

## Limites connues

- **Instagram** : aucune API pour les publications enregistrées ; partage manuel ou export mensuel.
- **Heddo** : pas d'intégration ; la newsletter est livrée en Markdown à coller.
- **WordPress** : l'article reste un brouillon Notion tant que le connecteur WordPress n'est pas configuré.
- **OpenAlex** : la syntaxe du filtre disciplinaire (`fields/33`) n'a pas pu être testée en direct ;
  en cas de refus, le collecteur relance sans ce filtre et le signale dans les logs.
- **SSRN** : couvert indirectement via OpenAlex.
