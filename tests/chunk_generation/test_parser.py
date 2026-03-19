import pytest
import os
import logging # Import it here to access levels

from app.indexer.tei_chunker import TEIChunker

# Get the logger for this specific module
logger = logging.getLogger("FMB-Pipeline.Tests")


@pytest.fixture
def sample_xml_content():
    """Fixture to load the XML file content as a string."""
    current_dir = os.path.dirname(__file__)
    fixture_path = os.path.join(current_dir, "../fixtures/sample_letter.xml")
    
    if not os.path.exists(fixture_path):
        pytest.skip(f"Fixture not found at {fixture_path}")
        
    with open(fixture_path, "r", encoding="utf-8") as f:
        return f.read()

def test_mendelssohn_chunking(sample_xml_content):
    """Tests chunking using the actual XML content from a fixture file."""
    
    # Initialize with the string from the file
    chunker = TEIChunker(sample_xml_content)
    
    # We use 3 sentences per chunk with an overlap of 1
    chunks = chunker.parse_to_chunks(sentences_per_chunk=3)

    # 1. Basic assertions
    assert len(chunks) > 0, "No chunks were generated from the fixture"
    
    # 2. Content Quality
    first_chunk_text = chunks[0]["content"]
    assert "\n" not in first_chunk_text, "Newlines should be cleaned"
    assert "  " not in first_chunk_text, "Double spaces should be cleaned"

    # 3. Categorized Metadata Check
    # We collect all keys across all chunks to verify our target ID
    all_person_keys = []
    for c in chunks:
        # Access the categorized entities: metadata -> entity_keys -> persons
        persons = c["metadata"].get("entity_keys", {}).get("persons", [])
        all_person_keys.extend(persons)

    # Check for the specific King's ID (Friedrich Wilhelm IV)
    assert "PSN0113990" in all_person_keys, "The specific person key was not captured in the metadata stack"

    # 4. Context Verification
    # Ensure the paragraph ID is captured correctly (assuming your fixture has p xml:id="...")
    assert "paragraph_id" in chunks[0]["metadata"]
    assert chunks[0]["metadata"]["letter_year"].isdigit()
