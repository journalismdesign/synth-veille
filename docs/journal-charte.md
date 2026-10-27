# Journal de la charte

Chaque modification de `charte/charte.toml` est consignée ici (règle P-03). Quand une
erreur passe, on ne corrige pas seulement le texte : on remonte à la règle qui l'a
laissée passer, on l'amende, et on note pourquoi. Commande : `/corriger-regle`.

Format d'une entrée :

```
## vX.Y.Z — AAAA-MM-JJ
- Règle : <id> (créée | amendée | supprimée)
- Incident : <ce qui est arrivé, lien vers le contenu ou la fiche>
- Cause : <pourquoi la règle existante ne l'a pas empêché>
- Changement : <ancienne formulation → nouvelle formulation>
- Contrôle : <auto | agent | humain> — test ajouté : <oui/non, lequel>
```

Versions : majeur = changement de principe (famille P) ; mineur = règle ajoutée ou
amendée ; correctif = lexique ou formulation.

---

## v1.1.0 — 2026-10-27
- Règle : S-04 (créée)
- Incident : la sélection de la semaine 44 classait au même rang des sujets américains et
  français à score voisin ; Gerald demande d'appliquer le mort-kilomètre.
- Cause : aucune règle ne pondérait la proximité ; S-03 (résonance) favorise mécaniquement
  la presse anglophone, plus nombreuse dans les flux.
- Changement : nouvelle règle S-04 ; bonus de proximité dans `docs/grille-notation.md`
  (+2 France, +1 Europe et francophonie) ; propriété Notion `Échelle` ; top 5 ordonné par
  échelle puis score.
- Contrôle : agent (`trieur`, `/veille-hebdo`) — test ajouté : oui, présence de S-04.

## v1.0.0 — 2026-10-27
- Création de la charte codée à partir de la page Notion « Positionnement de Synth et de
  notre journalisme », de `docs/grille-notation.md` et de `docs/gabarits.md`.
- 28 règles en 7 familles (Principes, Faits, Prismes, Écriture, Sélection, Distribution).
- Méthode inspirée de Damien Van Achter, « Pourquoi et comment j'ai codé ma ligne
  éditoriale » (da.van.ac, 12 juillet 2026) : charte codée, protocole de preuves
  bloquant, boussole des besoins, radar multi-sources, base de pistes d'action, correction
  à la règle.
