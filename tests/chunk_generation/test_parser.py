import pytest
import os
from app.indexer.tei_chunker import TEIChunker

def test_mendelssohn_chunking():
    # Pfad zur Fixture (lege dein XML dort ab)
    current_dir = os.path.dirname(__file__)
    fixture_path = os.path.join(current_dir, "../fixtures/sample_letter.xml")
    
    # Sicherstellen, dass die Datei existiert
    if not os.path.exists(fixture_path):
        pytest.skip("Test-XML Datei fehlt.")

    chunker = TEIChunker(fixture_path)
    chunks = chunker.parse_to_chunks(sentences_per_chunk=2)

    # Specs
    assert len(chunks) > 0
    
    # Checke den Inhalt: Keine doppelten Leerzeichen/Tabs
    assert "\n" not in chunks[0]["content"]
    assert "  " not in chunks[0]["content"]
    
    # Checke Metadaten: Die ID von Friedrich Wilhelm IV (PSN0113990)
    # sollte in den Entity-Keys auftauchen, wenn er im Absatz erwähnt wird.
    all_keys = []
    for c in chunks:
        all_keys.extend(c["metadata"]["entity_keys"])
    
    assert "PSN0113990" in all_keys
