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
