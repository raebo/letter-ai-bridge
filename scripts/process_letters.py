import os
import torch
from tqdm import tqdm
from app.core.config import settings
from app.database.connection import DBConnection
from app.database.models.letter import Letter
from app.database.models.letter_embedding import LetterEmbedding
from sentence_transformers import SentenceTransformer
from app.indexer.tei_chunker import TEIChunker
from app.database.services.ingest_chunks_service import IngestChunksService


def run_pipeline():
    # 1. Load Configuration
    DBConnection.set_config(settings.db_params)

    # 2. Setup GPU & Model
    # Leveraging the RTX 3080: uses CUDA if available
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"--- Initializing model on {device.upper()} ---")
    model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2', device=device)

    # 3. Setup Database Ingester
    ingester = IngestChunksService()

    print(f"--- Starting processing of letters from database ---")

    # Truncate the target table before inserting new data (use with caution!)
    LetterEmbedding.truncate_table()


    # 4. Loop over database batches
    # We fetch letters in batches to optimize memory usage
    for batch in Letter.find_all_with_xml(batch_size=10):
        # Using an inner progress bar for the current batch
        for letter in tqdm(batch, desc="Processing batch", unit="letter"):
            try:
                # A. Parsing & Chunking
                # The chunker now processes the XML string directly from the DB record
                chunker = TEIChunker(letter.xml_content) 
                raw_chunks = chunker.parse_to_chunks(sentences_per_chunk=3)

                processed_chunks = []
                if raw_chunks:
                    # B. Batch Vectorization
                    # Encoding all chunks of a letter at once is significantly faster on GPU
                    texts = [c['content'] for c in raw_chunks]
                    vectors = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)

                    for i, chunk in enumerate(raw_chunks):
                        full_metadata = chunk.get('metadata', {})
                        
                        # Link the chunk to the original letter via letter_id
                        full_metadata['letter_id'] = letter.id 
                        full_metadata['letter_name'] = letter.name
                        
                        processed_chunks.append({
                            "letter_id": letter.id, # This will be used in the DB schema to link back to the original letter
                            "content": chunk['content'],
                            "metadata": full_metadata,
                            "vector": vectors[i].tolist() # Convert numpy array to list for JSON/PgVector
                        })

                    # C. Database Upload
                    ingester.upload_chunks(processed_chunks)

            except Exception as e:
                # Use tqdm.write to prevent log messages from breaking the progress bar UI
                tqdm.write(f"ERROR processing letter ID {letter.name}: {e}")

    # Clean up connection
    ingester.close()
    print("\n--- All letters successfully transferred to the database ---")

if __name__ == "__main__":
    run_pipeline()
