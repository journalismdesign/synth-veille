"""Tests de la charte codée : relecture, protocole des preuves, radar de résonance."""
from pathlib import Path

from veille import charte, preuves, radar, relecture


def test_charte_charge_et_identifiants_uniques():
    regles = charte.regles()
    assert len(regles) == len(charte.charger()["regle"])
    assert {"P-03", "F-01", "Q-01", "E-07", "D-02"} <= set(regles)
    assert "[F-01]" in charte.premisse()


def test_relecture_detecte_les_tics_et_le_point_median():
    texte = ("À l'heure où tout change, ce n'est pas une crise, c'est une mutation. "
             "Les lecteurs y verront une véritable révolution.\n")
    ids = {e.regle for e in relecture.relire(texte, "newsletter")}
    assert {"E-03", "E-02", "E-07"} <= ids
    bloquants = [e for e in relecture.relire(texte, "newsletter") if e.severite == "bloquant"]
    assert any("révolution" in e.extrait for e in bloquants)


def test_relecture_accepte_le_point_median_et_ignore_les_sources():
    texte = "Les lecteur·ices de Synth.\n\n## Sources\n- Les lecteurs disent que c'est sans précédent\n"
    assert relecture.relire(texte, "newsletter") == []


def test_relecture_volume_article():
    court = "Un paragraphe sobre. " * 20
    assert any(e.regle == "E-09" for e in relecture.relire(court, "article"))
    juste = ("Une phrase factuelle et mesurée sur les data centers [P1]. " * 52)[:3000]
    assert not any(e.regle == "E-09" for e in relecture.relire(juste, "article"))


def _tableau(tmp_path: Path, lignes: list[str]) -> list[dict]:
    f = tmp_path / "preuves.tsv"
    f.write_text("\n".join(["id\taffirmation\ttype\tsource\tstatut\tfiche", *lignes]), encoding="utf-8")
    return preuves.lire(f)


def test_preuves_bloque_fait_sans_source_ou_non_verifie(tmp_path):
    lignes = _tableau(tmp_path, [
        "P1\tMeta a investi 10 Md$\tFait établi\t\tvérifié\t",
        "P2\tL'IA va remplacer 30 % des emplois\tFait établi\thttps://ex.org\tnon vérifié\t",
        "P3\tSynth juge ce choix risqué\tOpinion\t\tvérifié\t",
    ])
    erreurs = preuves.valider_tableau(lignes)
    assert any("P1" in e and "F-03" in e for e in erreurs)
    assert any("P2" in e and "vérifié" in e for e in erreurs)
    assert not any("P3" in e for e in erreurs)


def test_preuves_coherence_texte_et_nettoyage(tmp_path):
    lignes = _tableau(tmp_path, ["P1\tX\tFait établi\thttps://ex.org\tvérifié\t",
                                 "P2\tY\tHypothèse\thttps://ex.org/2\tcontesté\t"])
    erreurs, alertes = preuves.valider_texte("Constat [P1] et suite [P3].", lignes)
    assert erreurs == ["[F-01] appel [P3] sans ligne dans le tableau de preuves"]
    assert alertes == ["[F-01] preuve P2 jamais appelée dans le texte"]
    assert preuves.nettoyer("Constat [P1] et suite.") == "Constat et suite."


def _fiche(titre, url, source=""):
    return {"id": url, "titre": titre, "termes": radar.termes(titre),
            "noms": radar.noms_propres(titre), "domaine": radar.domaine(url), "source": source}


def test_radar_regroupe_un_meme_sujet_multi_sources():
    fiches = [
        _fiche("Microsoft relance la centrale nucléaire de Three Mile Island pour ses data centers", "https://www.lemonde.fr/a"),
        _fiche("Three Mile Island : Microsoft et la centrale nucléaire au service de l'IA", "https://www.mediapart.fr/b"),
        _fiche("Microsoft rouvre Three Mile Island", "https://www.lemonde.fr/c"),
        _fiche("Grève des livreurs Deliveroo à Lyon", "https://rapportsdeforce.fr/d"),
    ]
    groupes = radar.grouper(fiches)
    assert len(groupes) == 1 and len(groupes[0]) == 3
    assert radar.resonance(groupes[0]) == 2   # deux domaines distincts, pas trois


def test_top_semaine_retenus_puis_score_puis_resonance():
    from veille.top import classer
    f = lambda i, statut="Trié", score=None, res=0, pre=0: {
        "id": i, "titre": i, "statut": statut, "score": score, "resonance": res, "prescore": pre, "top": False}
    fiches = [f("non-note", pre=9), f("ecarte", "Écarté", 20), f("retenu", "Retenu NL", 11),
              f("haut", score=18), f("egal-resonant", score=15, res=4), f("egal", score=15)]
    assert [x["id"] for x in classer(fiches, 4)] == ["retenu", "haut", "egal-resonant", "egal"]
    assert "ecarte" not in [x["id"] for x in classer(fiches, 10)]


def test_radar_ignore_les_url_et_compte_les_sources_pas_les_posts():
    # Cas réel du 27/10 : les posts Bluesky de 404 Media s'agrégeaient via « https www 404media »
    a = _fiche("Texas suspends 17 data center permits https://www.404media.co/x", "https://bsky.app/1", "404 Media")
    b = _fiche("Sick of AI slop posters? https://www.404media.co/y", "https://bsky.app/2", "404 Media")
    assert radar.grouper([a, b]) == []
    c = _fiche("Google says it might use your Gmail data to target ads", "https://theverge.com/a", "The Verge")
    d = _fiche("Google privacy policy says your Gmail might be used for ads", "https://arstechnica.com/b", "Ars Technica")
    e = _fiche("Gmail might be used for ads, Google says", "https://bsky.app/3", "The Verge")
    (groupe,) = radar.grouper([c, d, e])
    assert radar.resonance(groupe) == 2   # The Verge compté une fois
