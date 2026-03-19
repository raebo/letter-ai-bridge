from app.core.logger import setup_logging, logger
setup_logging()

import json
from app.core.config import settings

from lxml import etree
from app.core.letter_ingester import LetterIngester
from app.database.connection import DBConnection
from app.database.models.letter import Letter
from sentence_transformers import SentenceTransformer
from app.database.services.ingest_chunks_service import IngestChunksService
from app.indexer.tei_header_chunker import TEIHeaderChunker
from app.indexer.tei_chunker import TEIChunker



def run_pipeline():

    DBConnection.set_config(settings.db_params)

    # Initialize our specialized services
    db_service = IngestChunksService()
    header_parser = TEIHeaderChunker()
    namespaces = {'tei': 'http://www.tei-c.org/ns/1.0'}

    error_count = 0

    letter = Letter.find_by_name("gb-1842-12-06-01")

    
    xml_content = letter.xml_content


    # 2. Execution Loop
    # for batch in Letter.find_all_with_xml(batch_size=10):
    try:
        root = etree.fromstring(xml_content.encode('utf-8'))
        header_node = root.xpath('./tei:teiHeader', namespaces=namespaces)[0]
        header_text = header_parser.parse(header_node)
        
        # 2. Parse Body
        body_chunker = TEIChunker(xml_content)
        raw_body_chunks = body_chunker.parse_to_chunks(sentences_per_chunk=3)

        # The service handles the SQL
        #db_service.upload_chunks(chunks_to_upload)

    except Exception as e:
        error_count += 1
        # Write immediately to disk as a single line (JSONL format)
        logger.error(f"Error processing letter {letter.name} (ID: {letter.id}): {e}")

    db_service.close()
    print("\n--- Processing Finished ---")

    print("\n" + "="*50)
    if error_count == 0:
        print("✅ Success! No errors recorded.")
    else:
        print(f"⚠️ Processed with {error_count} errors.")
    print("="*50)

if __name__ == "__main__":
    run_pipeline()
