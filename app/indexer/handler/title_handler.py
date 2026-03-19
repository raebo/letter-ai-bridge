from .base_handler import TEIElementHandler

import logging
logger = logging.getLogger(__name__)

class TitleHandler(TEIElementHandler):

    def _get_key_config(self, key: str):
        """Helper to map prefixes to DB categories."""
        key_upper = key.upper()
        if key_upper.startswith("PRC"):
            return "protag_creations", "PRC"
        if key_upper.startswith("CRT"):
            return "creations", "CRT"
        if key_upper.startswith("PSN"):
            return "people", "PSN"
        if key_upper.startswith("GB") or key_upper.startswith("FMB"):
            return "letters", "LET"
        return None, None


    def handle(self, node, namespaces, context_stack, cleaner=None):
        """
        Processes <title> tags which may contain nested <name> tags for:
        - ProtagCreations (PRC)
        - External Creations (CRT)
        - Letters (gb-, fmb-, LET)
        - Authors (PSN)
        """
        # 1. Clean Surface Text (e.g., "Radziwill’s Faust")
        # Grabs text from the node and child <hi> tags, but ignores <name> text content
        text_nodes = node.xpath("text() | tei:hi/text()", namespaces=namespaces)
        surface_text = "".join(node.xpath("text()", namespaces=namespaces)).strip()
        
        # 2. Collect all <name> keys
        name_nodes = node.xpath(".//tei:name[@key]", namespaces=namespaces)
        all_keys = [n.get("key") for n in name_nodes]

        if not all_keys:
            # Fallback if no keys are present
            return f" {surface_text} ", context_stack + [surface_text], {}

        raw_info_strings = []
        metadata_to_return = {}

        # 3. Iterate through all keys and fetch data based on their prefix/category
        for key in all_keys:
            category, prefix = self._get_key_config(key)
            
            if category and prefix:
                res = self._get_or_fetch_entity(category, prefix, key)
                
                if res and res.get("info"):
                    raw_info_strings.append(res['info'])
                    
                    # Store metadata AND the identified type/category
                    metadata_to_return[key] = {
                        **res.get("metadata", {}),
                        "entity_type": category,  # This tells the AI exactly what this title IS
                        "prefix": prefix
                    }

        # 4. Join the returning data
        # Example result: "Radziwill's Faust [Work Info] [Person Info]"

        if raw_info_strings:
            combined_info = " | ".join(raw_info_strings) 
            full_display = f"{surface_text} [{combined_info}]".strip()
        else:
            full_display = surface_text

        return f" {full_display} ", context_stack + [surface_text], metadata_to_return
