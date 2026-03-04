import os
import yaml
import glob
import torch
from tqdm import tqdm  # Für die Fortschrittsanzeige
from sentence_transformers import SentenceTransformer
from app.indexer.tei_chunker import TEIChunker
from app.database.ingest_chunks import ChunkIngester

def load_config(env="development"):
    with open("config/settings.yml", "r") as f:
        return yaml.safe_load(f)[env]

def run_pipeline():
    # 1. Konfiguration laden
    config = load_config()
    db_params = config['database']
    input_path = config['paths']['letters_input']

    # 2. Setup GPU & Model
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"--- Initialisiere Modell auf {device.upper()} ---")
    model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2', device=device)

    # 3. Setup Datenbank-Ingester
    ingester = ChunkIngester(db_params)

    # 4. Dateien finden
    xml_files = glob.glob(os.path.join(input_path, "**/*.xml"))
    if not xml_files:
        print(f"Keine XML-Dateien in {input_path} gefunden!")
        return

    print(f"--- Starte Verarbeitung von {len(xml_files)} Briefen ---")

    # 5. Loop mit Fortschrittsbalken (tqdm)
    # desc ist die Beschreibung, unit='file' zeigt die Dateien pro Sekunde
    for file_path in tqdm(xml_files, desc="Briefe indexieren", unit="file"):
        file_name = os.path.basename(file_path)

        try:
            # A. Parsing & Chunking
            chunker = TEIChunker(file_path)
            raw_chunks = chunker.parse_to_chunks(sentences_per_chunk=3)

            print(f"Gefundene Chunks in {file_name}: {len(raw_chunks)}")

            processed_chunks = []
            if raw_chunks:
                # Wir holen uns alle Texte eines Briefes in eine Liste für Batch-Encoding
                texts = [c['content'] for c in raw_chunks]
                
                # B. Batch-Vektorisierung (Viel schneller als einzeln!)
                # Die RTX 3080 liebt Batches
                vectors = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)


                for i, chunk in enumerate(raw_chunks):
                    full_metadata = chunk.get('metadata', {})
                    full_metadata['source_file'] = file_name
                    
                    processed_chunks.append({
                        "content": chunk['content'],
                        "metadata": full_metadata,
                        "vector": vectors[i].tolist()
                    })

                # C. Datenbank-Upload
                ingester.upload_chunks(processed_chunks)

        except Exception as e:
            # Wir nutzen tqdm.write, damit die Fehlermeldung den Balken nicht zerschießt
            tqdm.write(f"FEHLER in {file_name}: {e}")

    ingester.close()
    print("\n--- Alle Briefe erfolgreich in die Datenbank übertragen ---")

if __name__ == "__main__":
    run_pipeline()
