---
name: redaction-hebdo
description: Après validation de la sélection par Gerald, produit la newsletter (5 brèves), l'article de 3000 signes, les carrousels Instagram (textes + designs Canva) et le post LinkedIn de la semaine. À lancer à la main le lundi.
---

# Rédaction hebdomadaire Synth

1. **Lecture de la décision.** Trouve la page « Sélection <semaine> » la plus récente.
   Interroge la base : `Semaine = <semaine>` et `Statut` ∈ {Retenu NL, Retenu article}.
   - Si moins de 5 « Retenu NL » ou aucun « Retenu article » : arrête-toi et dis
     exactement ce qui manque. Ne complète pas la sélection toi-même.

2. **Rédaction.** Lance en parallèle :
   - un sous-agent `redacteur` pour la newsletter et le post LinkedIn ;
   - un sous-agent `redacteur` par fiche « Retenu article », pour l'article et son carrousel.
   Transmets à chacun l'URL de la page de sélection et les URL des fiches concernées.

3. **Mise en forme.** Quand la sous-page « Carrousels » existe, lance `metteur-en-forme`.

4. **Contrôle final** (toi-même) :
   - compte de signes de l'article dans la fourchette 2 700–3 300 ;
   - chaque brève a au moins un lien ;
   - aucune citation sans source ;
   - section « Points faibles » présente.
   Corrige ou fais corriger ce qui ne passe pas.

5. **Compte rendu.** Liens vers chaque sous-page et chaque design Canva, puis ce qu'il
   reste à faire à la main : coller la newsletter dans Heddo, importer l'article dans
   WordPress (tant que le connecteur WordPress n'est pas configuré), publier les carrousels.
