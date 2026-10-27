# synth-veille

Chaîne de veille éditoriale de Synth : de la collecte (Inoreader, recherche académique,
Instagram) à la sélection hebdomadaire de 10 sujets, puis aux livrables — 5 brèves de
newsletter, un article de 3 000 signes, des carrousels Instagram, un post LinkedIn.

```
Inoreader ─┐  (1 · sauvés, 2 · flux complet filtré)
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
| Chaque matin, 9 h | Veille web (rapports, enquêtes, études) déposée dans Notion, `Canal = Veille quotidienne` | Tâche planifiée « SYNTH \| Veille » |
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

## Charte codée

Méthode inspirée de Damien Van Achter (« Pourquoi et comment j'ai codé ma ligne
éditoriale », da.van.ac, 2026), adaptée à Synth.

| Élément | Où | Rôle |
|---|---|---|
| Charte (28 règles identifiées) | `charte/charte.toml` | Source unique de la ligne éditoriale, chargée en prémisse par chaque agent (`python -m veille.charte`) |
| Protocole de preuves | `veille/preuves.py` | Aucune prose sans tableau de preuves valide ; chaque affirmation typée, sourcée, statuée, appelée [Pn] |
| Relecture | `veille/relecture.py` | Lexique interdit, point médian, puces, questions en cascade, volume ; code retour 1 si bloquant |
| Radar | `veille/radar.py` | Résonance = nombre de sources indépendantes sur un même sujet (après chaque collecte) |
| Boussole des besoins | `docs/boussole-besoins.md` + propriété Notion « Besoin » | Le besoin décide du format et du canal |
| Pistes d'action | base Notion « Pistes d'action Synth » | Acteurs, mécanisme, signal de réussite |
| Correction à la règle | `/corriger-regle` + `docs/journal-charte.md` | Une erreur amende la règle, versionnée et motivée |
| Note publique | `docs/note-methodologique.md` | Brouillon de transparence pour synthmedia.fr |

## Lire la semaine dans Notion

- **« Cette semaine »** : les 30 fiches les plus intéressantes des 7 derniers jours (case
  « Top semaine », recalculée après chaque collecte par `python -m veille.top`). Les fiches
  retenues par Gerald passent en tête, puis Score, Résonance, Pré-score.
- **« Toutes les fiches (par score) »** (vue par défaut) : tout le reste, même ordre.

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
