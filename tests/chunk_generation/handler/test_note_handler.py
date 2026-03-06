from app.indexer.handler import NoteHandler
import lxml.etree as ET

def test_note_handler_uses_stack():
    handler = NoteHandler()
    # Mock-Knoten bauen
    node = ET.Element("note", type="single_place_comment")
    node.text = "Hier ist eine Anmerkung."
    
    # Testfall: Stack hat einen Ort
    stack = ["Leipzig"]
    result, new_stack = handler.handle(node, {}, stack)
    
    assert "Info zu Leipzig" in result
    assert new_stack == ["Leipzig"] # Stack sollte durch Note nicht verändert werden
