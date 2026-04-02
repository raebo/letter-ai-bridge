import asyncio
import logging
from app.api.services.summary_service import SummaryService
from app.database.models.letter_embedding import LetterEmbedding
from app.database.models.letter import Letter 

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("summary_orchestrator")

async def run_summary_pipeline():
    summary_service = SummaryService()
    
    # Der Generator wird initialisiert
    batches = Letter.get_raw_letters_batched(batch_size=20) 
    
    logger.info("Starte Zusammenfassungs-Pipeline...")

    # Äußere Schleife: Iteriert über die Batches (Listen)
    for batch in batches:
        logger.info(f"Verarbeite neuen Batch mit {len(batch)} Briefen...")
        
        # Innere Schleife: Iteriert über die einzelnen Briefe im Batch
        for letter in batch:
            letter_id = letter['id'] 
            raw_content = letter['content'] 

            if not raw_content or len(raw_content) < 50:
                logger.info(f"Überspringe {letter_id}: Zu kurz oder leer.")
                continue

            logger.info(f"Verarbeite Brief: {letter_id}")

            try:
                # 2. Schritt: Ollama (GPU)
                summary = await summary_service.generate_summary(raw_content)
                
                if summary:
                    # 3. Schritt: SentenceTransformer (GPU)
                    vector = summary_service.create_vector(summary)
                    
                    # 4. Schritt: DB (UPSERT mit Partial Index)
                    LetterEmbedding.upsert_summary(letter_id, summary, vector)
                    logger.info(f"Zusammenfassung für {letter_id} gespeichert.")
            except Exception as e:
                logger.error(f"Fehler bei Brief {letter_id}: {e}")

if __name__ == "__main__":
    asyncio.run(run_summary_pipeline())
