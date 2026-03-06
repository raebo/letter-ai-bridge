import pytest
import lxml.etree as ET
from app.indexer.tei_cleaner import TEICleaner

def test_contextual_place_note_linkage():
    # 1. Setup: Das XML-Snippet (mit Namespace-Simulation)
    xml_data = """
    <p xmlns="http://www.tei-c.org/ns/1.0">
        Ihre Überkunft nach <placeName xml:id="p1">Berlin<settlement key="STM01">Berlin</settlement></placeName>
        <note type="single_place_comment">Mendelssohn übersiedelte erst 1841.</note>
        gefälligst zu beschleunigen.
    </p>
    """
    namespaces = {'tei': 'http://www.tei-c.org/ns/1.0'}
    root = ET.fromstring(xml_data)
    
    # 2. Execution: Wir resetten den Stack im Cleaner manuell für den Test
    TEICleaner._context_stack = []
    
    results = []
    # Wir iterieren über alle Kinder des p-Tags (Textknoten und Elemente)
    # In der echten App macht das deine Loop im Indexer
    for node in root.xpath("./node()", namespaces=namespaces):
        if isinstance(node, ET._Element):
            results.append(TEICleaner.process_node(node, namespaces))
        else:
            results.append(str(node))

    
    full_text = "".join(results)
    cleaned_text = TEICleaner.clean_whitespace(full_text)
    cleaned_text = TEICleaner.heal_word_breaks(cleaned_text)


    # 3. Validation: Prüfen, ob Berlin im Stack gelandet ist und die Note den Namen enthält
    assert "Berlin [STM01]" in cleaned_text
    assert "[Info zu Berlin: Mendelssohn übersiedelte erst 1841.]" in cleaned_text
    # Sicherstellen, dass keine Dopplung ("BerlinBerlin") durch settlement auftritt
    assert "BerlinBerlin" not in cleaned_text
