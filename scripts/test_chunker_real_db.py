from lxml import etree
from app.core.config import settings
from app.database.connection import DBConnection
from app.indexer.tei_chunker import TEIChunker
from pathlib import Path

# 1. Setup
DBConnection.set_config(settings.db_params)

# 2. Your XML Paragraph
# Note: I added a xmlns to simulate real TEI behavior

def test_paragraph_processing():

    ROOT_DIR = Path(__file__).resolve().parent.parent
    file_path = ROOT_DIR / "tests" / "fixtures" / "letter_p_pers_name.xml"

    try:
        xml_content = file_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"Error: Could not find file at {file_path}")
        return
    

    print(f"DEBUG: XML Snippet length: {len(xml_content)}")
    
    # Initialize Chunker (which internally uses TEICleaner and Handlers)
    chunker = TEIChunker(xml_content=xml_content) 
    
    # Process the paragraph
    # Assuming your chunker has a method that takes a paragraph element
    chunks = chunker.parse_to_chunks(sentences_per_chunk=3)  # Adjust as needed

    print(f"DEBUG: Number of chunks found: {len(chunks)}")
    
    if not chunks:
        print("Empty! Check if the Chunker is finding the <p> tags.")
    
    for chunk in chunks:
        print("-" * 30)
        print(f"CONTENT: {chunk['content']}")
        print(f"METADATA: {chunk['metadata']}")

if __name__ == "__main__":
    test_paragraph_processing()
