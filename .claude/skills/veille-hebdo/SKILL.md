---
name: veille-hebdo
description: Pipeline hebdomadaire de veille Synth — trie, vérifie et documente les fiches collectées dans Notion, puis publie la page « Sélection semaine N » avec 10 candidats à valider par Gerald. À lancer le dimanche soir (tâche planifiée) ou à la main.
---

# Veille hebdomadaire Synth

Tu orchestres ; les sous-agents font le travail. Ne rédige aucun contenu publiable ici.

Identifiants : `config/veille.toml`, section `[notion]`.
Semaine : numéro ISO de la semaine **suivante** (ex. « 2026-S44 ») si on est dimanche, sinon la semaine courante.

## Étapes

0. **Charte.** Exécute `python -m veille.charte` et applique ces règles en prémisse.
   Le radar (`python -m veille.radar`) a tourné après la dernière collecte : la propriété
   `Résonance` indique combien de sources indépendantes traitent chaque sujet [S-03].

1. **Inventaire.** Interroge la data source Veille Synth : fiches `Statut = Collecté`
   ajoutées depuis 8 jours, triées par `Origine` puis `Pré-score` décroissant.
   Compte-les par origine (1 · Sauvé, 2 · Flux Inoreader, 3 · Académique).
   Si 0 fiche Inoreader : vérifie le dernier run GitHub Actions « Collecte veille »
   et signale le problème avant de continuer.

2. **Tri, dans l'ordre de priorité.** Lots de 40, un sous-agent `trieur` par lot, en parallèle :
   - d'abord **toutes** les fiches « 1 · Sauvé » (Gerald les a choisies) ;
   - puis **toutes** les fiches « 2 · Flux Inoreader » ;
   - enfin les fiches « 3 · Académique », limitées aux 40 meilleurs `Pré-score`.
     Les autres restent « Collecté » : elles servent de réservoir au `chercheur`.

3. **Vérification.** Prends les 15 meilleures fiches `Trié` issues d'Inoreader
   (Sauvé et Flux), plus au plus 3 fiches académiques si leur score ≥ 16. Répartis-les
   entre 3 sous-agents `verificateur` en parallèle.

4. **Recherche.** Sur les fiches Inoreader non écartées à l'étape 3, lance 2 sous-agents
   `chercheur` en parallèle (moitié chacun). Ils cherchent l'étude associée **d'abord
   parmi les fiches « 3 · Académique » de la base**, puis sur le web.

5. **Sélection.** Retiens 10 candidats selon les seuils et la règle d'équilibre de la
   grille, dont **au moins 7 issus d'Inoreader** (Sauvé ou Flux) : la recherche académique
   adosse les sujets, elle ne les remplace pas. Passe-les en `Statut = Candidat`, `Semaine = <semaine>`.
   Couvre au moins quatre `Besoin` différents [D-01] et examine en priorité les sujets de
   `Résonance` ≥ 3 [S-03].
   Propose (sans changer leur statut) un **top 5** et **5 autres propositions**, chacun
   avec sa destination (NL ou Insta), et 1 à 2 candidats article. Ordonne le top 5 par
   mort-kilomètre [S-04] : `Échelle` France d'abord, puis Europe, puis International,
   chaque groupe par score. Les sujets internationaux vont de préférence dans les 5 autres.

6. **Page de sélection.** Crée sous la page NEWSROOM la page
   « Sélection <semaine> » contenant :
   - un mode d'emploi en 2 lignes : « Passer 5 fiches en *Retenu NL* et 1–2 en
     *Retenu article* dans la vue ci-dessous, puis lancer /redaction-hebdo » ;
   - une vue de la base filtrée sur `Semaine = <semaine>` et `Statut` ∈ {Candidat, Retenu NL, Retenu article}, triée par score ;
   - ta proposition argumentée (une ligne par sujet : pourquoi, axe, origine, étude associée) ;
   - un bloc « Écartés notables » : 3 sujets très repris ailleurs mais écartés, et pourquoi.

7. **Diffusion interne de la proposition** (identifiants : `config/veille.toml`,
   sections `[notion]` et `[diffusion]`).
   - **Courriel** à `courriel_redaction`, en HTML sobre (noir, blanc, accent #00E6CC,
     IBM Plex Mono) avec une version texte : objet « Veille Synth S<n> — top 5 + 5
     propositions · choix <jour> » ; pour chaque sujet, rang, destination, échelle, score,
     deux lignes d'angle (qui décide, qui est exposé), ce qui reste à vérifier, liens vers
     les sources. Rappelle l'échéancier : choix jeudi midi, publication vendredi après-midi.
     Les faits non vérifiés sont présentés comme tels (« selon… », « à vérifier »).
   - **Encart** dans la page « Aujourd'hui » (`page_aujourdhui`) : un callout au-dessus de
     « 01 — Aujourd'hui » listant les 5 sujets du top, leur destination et leur source.
     Remplace l'encart de la semaine précédente au lieu d'en empiler un nouveau.
   - **Carte newsletter** : dans Production Synth (`data_source_production`), la carte
     `Canal = Newsletter` dont la date de publication est le prochain vendredi ; pose le
     sommaire provisoire (5 brèves : angle, source, points à vérifier) et une section
     « En réserve ». Ne change ni son `Statut` ni sa date ; si la date ne tombe pas un
     vendredi, signale-le dans `Notes`. Les sujets Insta du top vont dans une carte
     `Canal = Instagram` de la même semaine si elle existe, sinon signale-le.

8. **Compte rendu.** Termine par : nombre de fiches collectées / triées / vérifiées,
   lien vers la page de sélection, problèmes rencontrés (sources en panne, fiches illisibles).

## Garde-fous
- Ne passe jamais toi-même une fiche en « Retenu NL » ou « Retenu article » : c'est la décision de Gerald.
- Ne publie rien hors de Notion. Le courriel à la rédaction (étape 7) est interne et n'est pas une publication.
