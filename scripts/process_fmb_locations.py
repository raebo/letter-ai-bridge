import sys
import os
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.services.protag_whereabouts_service import ProtagWhereaboutsService

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/location_ingest.log')
    ]
)

logger = logging.getLogger("LocationOrchestrator")

def main():
    logger.info("=== Start: FMB Reise-Fakten Ingest ===")
    
    try:
        service = ProtagWhereaboutsService(batch_size=128)
        
        logger.info("Initialisiere GPU-Modell und lade Briefdaten...")
        service.process_locations()
        
        logger.info("=== Erfolg: Alle Orte wurden vektorisiert und gespeichert ===")
        
    except Exception as e:
        logger.error(f"Kritischer Fehler im Orchestrator: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
