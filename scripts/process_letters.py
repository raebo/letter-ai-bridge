import builtins

from app.core.logger import setup_logging, logger
setup_logging()

import os
from datetime import datetime
import json
import torch
from tqdm import tqdm
from app.core.config import settings
from app.core.letter_ingester import LetterIngester
from app.database.connection import DBConnection
from app.database.models.letter import Letter
from app.database.models.letter_embedding import LetterEmbedding
from sentence_transformers import SentenceTransformer
from app.database.services.ingest_chunks_service import IngestChunksService


def run_pipeline():
    # 1. Setup Logging First
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_filename = os.path.join(log_dir, f"error_log_{timestamp}.jsonl") # Using JSONL (JSON Lines)

    # 2. Open the log file in "Append" mode
    with open(log_filename, "a", encoding="utf-8") as log_file:
        print(f"--- Pipeline started. Live logs: {log_filename} ---")

        # 1. Setup
        DBConnection.set_config(settings.db_params)
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2', device=device)

        # Initialize our specialized services
        letter_processor = LetterIngester(model)
        db_service = IngestChunksService()

        error_count = 0

        print(f"--- Pipeline started on {device.upper()} ---")

        if settings.truncate_embeddings_on_start:
            print("⚠️ Truncating existing embeddings as per configuration...")
            LetterEmbedding.truncate_table()
        else:
            print("ℹ️ Existing embeddings will be preserved. Only letters without embeddings will be processed.")

        # 2. Execution Loop
        # for batch in Letter.find_all_with_xml(batch_size=10):
        for batch in Letter.find_all_missing_embeddings(batch_size=10):
            for letter in tqdm(batch, desc="Ingesting batch", unit="letter"):
                try:
                    # The processor does all the heavy lifting (Header, Body, Vectors)
                    logger.info(f"+ + + + + +  + + + + + + + + Processing letter: {letter.name} (ID: {letter.id})")
                    chunks_to_upload = letter_processor.process_letter(letter)
                    
                    # The service handles the SQL
                    db_service.upload_chunks(chunks_to_upload)

                except Exception as e:
                    error_count += 1
                    # Create the error entry
                    error_entry = {
                        "name": letter.name,
                        "id": letter.id,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    }
                    # Write immediately to disk as a single line (JSONL format)
                    print(f"Error processing letter {letter.name} (ID: {letter.id}): {e}")
                    log_file.write(json.dumps(error_entry, ensure_ascii=False) + "\n")
                    log_file.flush() # Forces the OS to write to disk right now
                    
                    tqdm.write(f"FAILED: {letter.name} - See log for details.")

        db_service.close()
        print("\n--- Processing Finished ---")

        print("\n" + "="*50)
        if error_count == 0:
            print("✅ Success! No errors recorded.")
        else:
            print(f"⚠️ Processed with {error_count} errors. Check {log_filename}")
        print("="*50)

if __name__ == "__main__":
    run_pipeline()
