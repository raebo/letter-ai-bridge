import logging
import sys
from pathlib import Path
from app.core.config import settings

def setup_logging():
    """Initializes the global logging configuration."""
    log_format = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    
    handlers = [logging.StreamHandler(sys.stdout)]

    # If file logging is enabled in settings
    if getattr(settings, "LOG_TO_FILE", False):
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        file_handler = logging.FileHandler(log_dir / "pipeline.log", encoding="utf-8")
        handlers.append(file_handler)

    logging.basicConfig(
        level=logging.INFO if not settings.DEBUG else logging.DEBUG,
        format=log_format,
        handlers=handlers,
        force=True # Overwrites any default basicConfig
    )

# Create a convenience object
logger = logging.getLogger("FMB-Pipeline")
