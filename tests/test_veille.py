"""Tests hors ligne : normalisation, préfiltre et analyse des formats de chaque source.

Les fixtures reproduisent la STRUCTURE documentée des réponses d'API, avec des
contenus fictifs : elles vérifient le code, pas la qualité de la veille.
"""
import json
from datetime import date

from veille.modele import Item, charger_config, empreinte_url, normaliser_url, prequalifier
from veille.sources import arxiv, hal, inoreader, instagram, openalex, socarxiv


def test_normalisation_retire_pistage_et_www():
    a = "http://www.exemple.fr/article/?utm_source=x&id=3#haut"
    b = "https://exemple.fr/article?id=3&fbclid=abc"
    assert normaliser_url(a) == normaliser_url(b) == "https://exemple.fr/article?id=3"
    assert empreinte_url(a) == empreinte_url(b)


def test_prefiltre_mot_entier_et_prefixe():
    axes = {"Imaginaires & récits": ["agi"], "Économie politique": ["subsid*"]}
    magie = prequalifier(Item("A magic trick", "https://x", "arXiv"), axes)
    assert magie.prescore == 0
    ok = prequalifier(Item("AGI hype and state subsidies", "https://y", "arXiv"), axes)
    assert ok.axes == ["Imaginaires & récits", "Économie politique"] and ok.prescore == 2


def test_config_valide():
    c = charger_config()
    assert len(c["axes"]) == 9
    for cle in ("inoreader", "openalex", "arxiv", "hal"):
        assert cle in c


def test_openalex_resume_et_item():
    w = {
        "id": "https://openalex.org/W1", "doi": "https://doi.org/10.1/abc", "display_name": "Ghost work",
        "type": "article", "publication_date": "2026-10-20",
        "abstract_inverted_index": {"Workers": [0], "annotate": [1], "data": [2]},
        "authorships": [{"author": {"display_name": "M. Gray"}}],
        "primary_location": {"source": {"display_name": "Big Data & Society"}},
    }
    it = openalex._vers_item(w)
    assert it.resume == "Workers annotate data"
    assert it.type == "Étude publiée" and it.source == "M. Gray — Big Data & Society"
    assert it.date_publication == date(2026, 10, 20)


ATOM = """<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom">
<entry><id>http://arxiv.org/abs/2610.00001v1</id><published>2026-10-21T10:00:00Z</published>
<title>Data centers and
 water</title><summary> Water use of AI. </summary>
<author><name>A. Un</name></author><author><name>B. Deux</name></author></entry></feed>"""


def test_arxiv_atom():
    (it,) = arxiv.analyser(ATOM)
    assert it.titre == "Data centers and water"
    assert it.url == "https://arxiv.org/abs/2610.00001v1"
    assert it.source == "A. Un, B. Deux" and it.date_publication == date(2026, 10, 21)


def test_hal_dates_partielles():
    d = {"title_s": ["Le microtravail"], "uri_s": "https://hal.science/hal-1", "producedDate_s": "2026",
         "authFullName_s": ["P. Tubaro"], "docType_s": "ART", "abstract_s": ["Résumé"]}
    it = hal._vers_item(d)
    assert it.date_publication is None and it.titre == "Le microtravail" and it.resume == "Résumé"


def test_socarxiv():
    p = {"id": "abc12", "attributes": {"title": "T", "description": "D", "date_created": "2026-10-22T08:00:00"},
         "links": {"html": "https://osf.io/preprints/socarxiv/abc12"}}
    assert socarxiv._vers_item(p).date_publication == date(2026, 10, 22)


def test_inoreader_article():
    a = {"title": "L&#039;IA &amp; le travail", "canonical": [{"href": "https://media.fr/a"}],
         "summary": {"content": "<p>Un <b>texte</b></p>"}, "origin": {"title": "Média"}, "published": 1761300000}
    it = inoreader._vers_item(a)
    assert it.titre == "L'IA & le travail" and it.resume == "Un texte" and it.source == "Média"


def test_instagram_export(tmp_path):
    f = tmp_path / "saved_posts.json"
    f.write_text(json.dumps({"saved_saved_media": [
        {"title": "casilli", "string_map_data": {"Saved on": {"href": "https://www.instagram.com/p/XYZ/", "timestamp": 1761300000}}},
        {"title": "ancien", "string_map_data": {"Saved on": {"href": "https://www.instagram.com/p/OLD/", "timestamp": 1600000000}}},
    ]}))
    (it,) = instagram.collecter_export(f, date(2025, 1, 1))
    assert it.source == "@casilli" and it.canal == "Instagram"


def test_ancrage_tech_ecarte_les_hors_sujet():
    from veille.modele import a_ancrage_tech
    ancrage = charger_config()["prefiltre"]["ancrage_tech"]
    hors_sujet = Item("Article 370, Kashmir, and the Politics of Constitutional Integration in India",
                      "https://x", "SocArXiv", resume="Consent, sovereignty and judicial power.")
    pertinent = Item("Detecting AI Training in Datacentre Power", "https://y", "arXiv")
    sonnac = Item("Plateformes numériques, manipulation de l’information", "https://z", "HAL")
    assert not a_ancrage_tech(hors_sujet, ancrage)
    assert a_ancrage_tech(pertinent, ancrage) and a_ancrage_tech(sonnac, ancrage)
    # « meta » mot entier : ne doit pas capter « metabolism »
    assert not a_ancrage_tech(Item("Metabolism of soil", "https://m", "OpenAlex"), ancrage)


def test_selection_priorite_sauve_puis_flux_puis_academique():
    from veille.collecte import selectionner
    from veille.modele import ACADEMIQUE, FLUX, SAUVE
    config = charger_config()
    sauve_hors_sujet = Item("Recette de la tarte aux pommes", "https://a.fr/1", "Inoreader", origine=SAUVE)
    flux_ok = Item("Les data centers et l'eau", "https://a.fr/2", "Inoreader", origine=FLUX)
    flux_bruit = Item("Résultats du championnat de rugby", "https://a.fr/3", "Inoreader", origine=FLUX)
    academique = Item("AI and platform labor: worker surveillance", "https://a.fr/4", "arXiv")
    doublon_flux = Item("Les data centers et l'eau", "https://a.fr/2?utm_source=x", "Inoreader", origine=FLUX)
    doublon_sauve = Item("Les data centers et l'eau", "https://a.fr/2", "Inoreader", origine=SAUVE)

    retenus = selectionner([academique, flux_bruit, flux_ok, doublon_flux, sauve_hors_sujet, doublon_sauve], config)
    # Les sauvés passent sans filtre et en tête ; le doublon garde l'origine la plus prioritaire
    assert [(i.titre, i.origine) for i in retenus] == [
        ("Recette de la tarte aux pommes", SAUVE),
        ("Les data centers et l'eau", SAUVE),
        ("AI and platform labor: worker surveillance", ACADEMIQUE),
    ]


def test_notion_promeut_un_article_sauve_apres_coup(monkeypatch):
    from veille.modele import FLUX, SAUVE
    from veille.notion import Notion
    appels = []
    n = Notion(jeton="x", base_id="base")
    it = Item("Titre", "https://a.fr/1", "Inoreader", origine=SAUVE)
    n._cache = {it.empreinte: ("page-1", FLUX)}
    monkeypatch.setattr(n, "_requete", lambda methode, chemin, **kw: appels.append((methode, chemin, kw)) or {})
    assert n.ajouter(it) == "promu"
    assert appels == [("PATCH", "/pages/page-1", {"json": {"properties": {"Origine": {"select": {"name": SAUVE}}}}})]
    assert n.ajouter(it) == "existe"
