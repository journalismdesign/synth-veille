---
name: veille-hebdo
description: Pipeline hebdomadaire de veille Synth — trie, vérifie et documente les fiches collectées dans Notion, puis publie la page « Sélection semaine N » avec 10 candidats à valider par Gerald. À lancer le dimanche soir (tâche planifiée) ou à la main.
---

# Veille hebdomadaire Synth

Tu orchestres ; les sous-agents font le travail. Ne rédige aucun contenu publiable ici.

Identifiants : `config/veille.toml`, section `[notion]`.
Semaine : numéro ISO de la semaine **suivante** (ex. « 2026-S44 ») si on est dimanche, sinon la semaine courante.

## Étapes

1. **Inventaire.** Interroge la data source Veille Synth : fiches `Statut = Collecté`
   ajoutées depuis 8 jours. Si 0 fiche : vérifie le dernier run GitHub Actions
   « Collecte veille » et signale le problème au lieu de continuer.

2. **Tri.** Découpe en lots de 40 et lance un sous-agent `trieur` par lot, **en parallèle**.
   Chaque lot reçoit la liste des URL de fiches.

3. **Vérification.** Prends les 15 meilleures fiches `Trié` (score décroissant, en
   respectant l'équilibre de `docs/grille-notation.md`). Répartis-les entre 3 sous-agents
   `verificateur` en parallèle.

4. **Recherche.** Sur les fiches non écartées à l'étape 3, lance 2 sous-agents `chercheur`
   en parallèle (moitié chacun).

5. **Sélection.** Retiens 10 candidats selon les seuils et la règle d'équilibre de la
   grille. Passe-les en `Statut = Candidat`, `Semaine = <semaine>`.
   Propose (sans changer leur statut) les 5 meilleurs pour la newsletter et 1 à 2 pour
   l'article.

6. **Page de sélection.** Crée sous la page NEWSROOM la page
   « Sélection <semaine> » contenant :
   - un mode d'emploi en 2 lignes : « Passer 5 fiches en *Retenu NL* et 1–2 en
     *Retenu article* dans la vue ci-dessous, puis lancer /redaction-hebdo » ;
   - une vue de la base filtrée sur `Semaine = <semaine>` et `Statut` ∈ {Candidat, Retenu NL, Retenu article}, triée par score ;
   - ta proposition argumentée (une ligne par sujet : pourquoi, axe, étude associée) ;
   - un bloc « Écartés notables » : 3 sujets très repris ailleurs mais écartés, et pourquoi.

7. **Compte rendu.** Termine par : nombre de fiches collectées / triées / vérifiées,
   lien vers la page de sélection, problèmes rencontrés (sources en panne, fiches illisibles).

## Garde-fous
- Ne passe jamais toi-même une fiche en « Retenu NL » ou « Retenu article » : c'est la décision de Gerald.
- Ne publie rien hors de Notion.
