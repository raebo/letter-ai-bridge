import pytest
import logging
from unittest.mock import patch
import lxml.etree as ET
from app.indexer.tei_cleaner import TEICleaner

logger = logging.getLogger("FMB-Pipeline.Tests")

@patch('app.database.services.entity_resolution.retrieve_infos_service.RetrieveInfosService.get_info')
def test_contextual_place_note_linkage(mock_get_info):
    # Verifies two things together:
    # 1. PlaceHandler resolves a settlement key via the (mocked) entity
    #    service and appends its info in brackets.
    # 2. The place's surface text is pushed onto TEICleaner's context stack,
    #    so a following <note type="single_place_comment"> can reference it
    #    ("Info zu Berlin: ...") without repeating the place name in the XML.
    mock_get_info.return_value = {
        "info": "Sitz des preußischen Hofes",
        "metadata": {"key": "STM01"},
    }

    xml_data = """
    <p xmlns="http://www.tei-c.org/ns/1.0">
        Ihre Überkunft nach <placeName xml:id="p1">Berlin<settlement key="STM01">Berlin</settlement></placeName>
        <note type="single_place_comment">Mendelssohn übersiedelte erst 1841.</note>
        gefälligst zu beschleunigen.
    </p>
    """
    namespaces = {'tei': 'http://www.tei-c.org/ns/1.0'}
    root = ET.fromstring(xml_data)

    # 2. Execution
    TEICleaner._context_stack = []
    text_parts = []

    for node in root.xpath("./node()", namespaces=namespaces):
        if isinstance(node, ET._Element):
            # process_node returns (text, metadata); only the text feeds the
            # paragraph string, matching how TEIChunker consumes it.
            node_text, _ = TEICleaner.process_node(node, namespaces)
            text_parts.append(node_text)
        else:
            text_parts.append(str(node))

    full_text = "".join(text_parts)
    cleaned_text = TEICleaner.clean_whitespace(full_text)

    # 3. Validation
    assert mock_get_info.call_count == 1
    assert mock_get_info.call_args[0] == ("STM", "STM01")
    assert "Berlin [Sitz des preußischen Hofes]" in cleaned_text
    assert "[Info zu Berlin: Mendelssohn übersiedelte erst 1841.]" in cleaned_text
