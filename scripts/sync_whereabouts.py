import asyncio
import logging
from psycopg2.extras import Json, execute_values
from sentence_transformers import SentenceTransformer

from app.database.models.person import Person
from app.database.connection import DBConnection
from app.utils.string_cleaner import StringCleaner
from app.core.services.whereabouts_service import WhereaboutsService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("orchestrator")

model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2', device="cuda")

async def orchestrate_sync():
    service = WhereaboutsService()
    batch_size = 50  # Anzahl der Personen pro Durchgang
    
    logger.info("Starte Batch-Synchronisation...")

    for key_batch in Person.get_all_keys_batched(batch_size=batch_size):
        logger.info(f"Verarbeite Batch mit {len(key_batch)} Personen...")
        
        all_rows_for_this_batch = []

        for key in key_batch:
            person_profile = Person.entity_profile(key)
            if not person_profile:
                continue

            events = await service.get_person_whereabouts(key)
            if not events:
                continue
            
            last = StringCleaner.normalize_name(person_profile.get('last_name')) or ""
            first = StringCleaner.normalize_name(person_profile.get('first_name')) or ""
            display_name = " ".join(filter(None, [first, last]))
            
            if not display_name:
                display_name = key

            for event in events:
                content = (f"{display_name} befand sich am {event.get('event_date')} "
                           f"in {event.get('geography', {}).get('destination', {}).get('name')}. "
                           f"Belegt durch: {event.get('letter', {}).get('title')}.")
                
                embedding = model.encode(content).tolist()
                
                metadata = {
                    "date": event.get('event_date'),
                    "source_letter": event.get('letter', {}).get('name'),
                    "person_key": key
                }
                
                all_rows_for_this_batch.append((
                    'presence', key, content, Json(metadata), embedding
                ))

        if all_rows_for_this_batch:
            save_to_db(all_rows_for_this_batch)
            logger.info(f"Batch-Insert erfolgreich: {len(all_rows_for_this_batch)} Einträge gespeichert.")
        
        # Kurze Pause um API/DB zu entlasten
        await asyncio.sleep(0.5)

def save_to_db(rows):
    conn = DBConnection.get_connection()
    try:
        with conn.cursor() as cur:
            query = """
                INSERT INTO entity_embeddings 
                (entity_type, reference_key, content, metadata, embedding, created_at, updated_at)
                VALUES %s
            """
            execute_values(cur, query, rows, template="(%s, %s, %s, %s, %s, NOW(), NOW())")
            conn.commit()
    finally:
        conn.close()

if __name__ == "__main__":
    asyncio.run(orchestrate_sync())
