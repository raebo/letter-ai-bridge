from app.indexer.tei_cleaner import TEICleaner
from lxml import etree

def test_note_handling():
    # Wir simulieren einen <note> Knoten
    xml = '<note xmlns="http://www.tei-c.org/ns/1.0">A. O. – Allerhöchste Ordre.</note>'
    node = etree.fromstring(xml)
    ns = {"tei": "http://www.tei-c.org/ns/1.0"}
    
    result = TEICleaner.process_node(node, ns)
    assert "[Anm.: A. O. – Allerhöchste Ordre.]" in result

def test_complex_word_healing():
    text = "Die Ver-\n   hältniße sind schwierig."
    healed = TEICleaner.heal_word_breaks(text)
    assert healed == "Die Verhältniße sind schwierig."
