from unittest.mock import patch
from app.indexer.tei_cleaner import TEICleaner
from app.indexer.handler.pers_name_handler import PersNameHandler
from lxml import etree

def test_note_handling():
    # Wir simulieren einen <note> Knoten
    xml = '<note xmlns="http://www.tei-c.org/ns/1.0">A. O. – Allerhöchste Ordre.</note>'
    node = etree.fromstring(xml)
    ns = {"tei": "http://www.tei-c.org/ns/1.0"}

    # process_node liefert (text, metadata), nicht einen einzelnen String
    result_text, metadata = TEICleaner.process_node(node, ns)
    assert "[Anm: A. O. – Allerhöchste Ordre.]" in result_text
    assert metadata == {}

def test_complex_word_healing():
    text = "Die Ver-\n   hältniße sind schwierig."
    healed = TEICleaner.heal_word_breaks(text)
    assert healed == "Die Verhältniße sind schwierig."

@patch('app.database.services.entity_resolution.retrieve_infos_service.RetrieveInfosService.get_info')
def test_report_key_cache_hit_matches_first_lookup_shape(mock_get_info):
    # LAB-007: report_key used to wrap the metadata dict in an extra
    # {'metadata': {...}} layer on cache storage, so a cache hit returned a
    # different shape than the original service lookup.
    mock_get_info.return_value = {"info": "Felix Mendelssohn", "metadata": {"key": "PSN1"}}

    TEICleaner.reset()
    handler = PersNameHandler()
    ns = {"tei": "http://www.tei-c.org/ns/1.0"}
    xml = ('<persName xmlns="http://www.tei-c.org/ns/1.0">Felix'
           '<name key="PSN1" style="hidden">Mendelssohn Bartholdy</name></persName>')
    node = etree.fromstring(xml)

    _, _, meta_first_lookup = handler.handle(node, ns, [])
    _, _, meta_cache_hit = handler.handle(node, ns, [])

    assert meta_first_lookup["PSN1"] == {"key": "PSN1"}
    assert meta_cache_hit["PSN1"] == meta_first_lookup["PSN1"]
    assert mock_get_info.call_count == 1
