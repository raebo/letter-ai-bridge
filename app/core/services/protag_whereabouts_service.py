import json
import logging
from sentence_transformers import SentenceTransformer
from app.database.models.entity_embedding import EntityEmbedding

logger = logging.getLogger(__name__)

class ProtagWhereaboutsService:
    def __init__(self, batch_size=128):
        self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2', device="cuda")
        self.batch_size = batch_size

    def _generate_fact_text(self, record):
        """Erzeugt den narrativen Satz aus dem Briefnamen FMB-YYYY-MM-DD-NN"""
        parts = record['letter_name'].split('-')
        if len(parts) >= 4:
            date_str = f"{parts[3]}.{parts[2]}.{parts[1]}"
            year = parts[1]
            content = (f"Am {date_str} hielt sich Felix Mendelssohn Bartholdy im 19. Jahrhundert "
                       f"in {record['place_name']} auf (Quelle: Brief {record['letter_name']}).")
            return content, year
        return None, None

    def process_locations(self):
        # 1. Rohdaten via Model holen (musst du im Model noch implementieren, siehe oben)
        records = EntityEmbedding.get_fmb_letters_with_places() 
        
        for i in range(0, len(records), self.batch_size):
            batch = records[i : i + self.batch_size]
            
            prepared_texts = []
            rows_for_db = []

            for rec in batch:
                content, year = self._generate_fact_text(rec)
                if not content: continue

                prepared_texts.append(content)
                # Metadaten für spätere Filterung (z.B. im Chat nach Jahr)
                meta = json.dumps({"year": year, "original_name": rec['letter_name']})
                
                # Wir merken uns die Daten, die Vektoren kommen gleich dazu
                rows_for_db.append({
                    "type": "travel_log",
                    "ref": str(rec['id']), # letter_id als reference_key
                    "content": content,
                    "meta": meta
                })

            if not prepared_texts: continue

            # 2. Batch-Vektorisierung auf der RTX 3080
            embeddings = self.model.encode(prepared_texts).tolist()

            # 3. Formatierung für EntityEmbedding.save_batch
            final_rows = []
            for idx, row in enumerate(rows_for_db):
                final_rows.append((
                    row["type"],
                    row["ref"],
                    row["content"],
                    row["meta"],
                    embeddings[idx] # Der frische Vektor
                ))

            # 4. Speichern via Model
            EntityEmbedding.save_batch(final_rows)
            logger.info(f"Batch {i//self.batch_size + 1} verarbeitet.")
