import httpx
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class WhereaboutsService:
    def __init__(self):
        self.url_template = f"{settings.api_host}/api/people/timeline/PERS_KEY?user_auth_token={settings.api_token}"
        self.timeout = 30.0

    async def get_person_whereabouts(self, person_key: str) -> list:
        """
        Fragt die Aufenthaltsdaten für einen bestimmten Personenschlüssel ab.
        """
        target_url = self.url_template.replace("PERS_KEY", person_key)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(target_url)
                
                if response.status_code == 404:
                    logger.warning(f"Keine Daten für Person {person_key} gefunden (404).")
                    return []
                
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP Fehler für {person_key} an {target_url}: {e.response.status_code}")
                return []
            except Exception as e:
                logger.error(f"Unerwarteter Fehler bei API-Abfrage für {person_key}: {e}")
                return []


