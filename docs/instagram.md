# Faire entrer les saves Instagram dans la veille

Instagram n'expose aucune API pour les publications enregistrées d'un compte
personnel. Deux voies complémentaires :

## 1. Au fil de l'eau (recommandé) — partage vers Notion

1. Installer l'app Notion sur le téléphone.
2. Sur un post Instagram : ✈️ Partager → « Copier le lien » ou feuille de partage → **Notion**.
3. Choisir la base **Veille Synth**, mettre `Canal = Instagram`, `Type = Post social`.
   Une ligne de contexte dans « Résumé » aide beaucoup l'agent trieur.

Durée : ~5 secondes par post. C'est le seul geste manuel de la chaîne.

## 2. Rattrapage mensuel — export officiel

1. Instagram → Paramètres → Espace comptes → Vos informations et autorisations →
   **Télécharger vos informations** → format **JSON**, période « dernier mois ».
2. Décompresser, récupérer `your_instagram_activity/saved/saved_posts.json`.
3. `python -m veille.collecte --sources "" --instagram chemin/saved_posts.json --depuis 31`

Les doublons avec la voie 1 sont éliminés par l'empreinte d'URL.
