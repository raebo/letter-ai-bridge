from abc import ABC, abstractmethod
from typing import Tuple
import lxml.etree as ET
from app.database.services.entity_resolution.retrieve_infos_service import RetrieveInfosService

class TEIElementHandler(ABC):

    def _format_info_bracket(self, surface_text: str, info_list: list) -> str:
        """
        Consolidates a list of strings into a single bracket, 
        removing duplicates and values already present in the surface text.
        """
        if not info_list:
            return surface_text

        unique_info = []
        seen = set()
        
        # Normalize surface text for comparison
        surface_norm = surface_text.strip().lower()

        for item in info_list:
            if not item:
                continue
            
            # Clean and normalize the item
            val = item.strip()
            val_norm = val.lower()

            # Rule 1: Don't add if it's exactly the same as the surface text
            # Rule 2: Don't add if we've already seen this piece of info
            if val_norm != surface_norm and val_norm not in seen:
                unique_info.append(val)
                seen.add(val_norm)

        if not unique_info:
            return surface_text

        # Join unique items with a pipe and wrap in brackets
        combined_info = " | ".join(unique_info)
        return f"{surface_text} [{combined_info}]"

    def _get_or_fetch_entity(self, category: str, prefix: str, key: str) -> dict:
        """
        Generic cache-first retrieval logic for all handlers.
        """
 
        # 1. Check the cleaner's internal cache
        from app.indexer.tei_cleaner import TEICleaner
        cleaner = TEICleaner()

        cached_entry = cleaner.get_captured_keys(category).get(key)
        if cached_entry:
            return cached_entry

        # 2. Fetch from modular Service
        res = RetrieveInfosService.get_info(prefix, key)
        
        if res and res.get("info"):
            # 3. Store in cache for future mentions
            TEICleaner.report_key(
                category=category, 
                key=key, 
                info_string=res["info"], 
                metadata=res.get("metadata", {}) # Pass as a single dict, not unpacked
            )
            return res

        return {"info": None, "metadata": {}}

    @abstractmethod
    def handle(self, node: ET.Element, namespaces: dict, context_stack: list) -> Tuple[str, list, dict]:
        """
        Returns: (text_result, updated_stack, metadata_dict)
        """
        pass

    def get_clean_text(self, node: ET.Element) -> str:
        # Extrahiert Text und ersetzt alle Whitespace-Sequenzen durch ein Leerzeichen
        raw_text = "".join(node.xpath(".//text()"))
        return " ".join(raw_text.split()).strip()

    def get_direct_text(self, node: ET.Element) -> str:
        """Hilfsmethode: Nur den Text des aktuellen Knotens."""
        return "".join(node.xpath("text()")).strip()
