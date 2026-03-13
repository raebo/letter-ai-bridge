from .base_handler import TEIElementHandler

class TitleHandler(TEIElementHandler):
    def handle(self, node, namespaces, context_stack):
        """
        Processes <title> tags which may contain nested <name> tags for:
        - ProtagCreations (PRC)
        - External Creations (CRT)
        - Letters (gb-, fmb-, LET)
        - Authors (PSN)
        """
        # 1. Capture the immediate surface text (e.g., "Paulus" or "Schreiben vom 6ten")
        # We use a specific XPath to avoid grabbing the hidden text inside child <name> tags
        surface_text = "".join(node.xpath("text() | tei:hi/text()", namespaces=namespaces)).strip()
        
        collected_metadata = {}
        info_expansions = []

        # 2. Iterate through nested <name> tags to find entities
        name_nodes = node.xpath(".//tei:name", namespaces=namespaces)
        
        for name in name_nodes:
            key = name.get("key")
            name_type = name.get("type") # 'person', 'author', 'letter', 'dramatic_work', etc.
            
            if not key:
                continue

            # 3. Decision Logic: Determine Category and Prefix
            category, prefix = self._identify_entity_type(key, name_type)

            # 4. Fetch the expanded info from your Service
            # This calls RetrieveInfosService.get_info(prefix, key)
            res = self._get_or_fetch_entity(category=category, prefix=prefix, key=key)
            
            if res and res.get("info"):
                info_expansions.append(res["info"])
                # Merge the metadata into the chunk's metadata dictionary
                if res.get("metadata"):
                    collected_metadata[key] = res["metadata"]

        # 5. Assemble the final display text
        # Result: "Paulus [MWV A 14] [Mendelssohn Bartholdy, Felix]"
        expansion_str = " ".join([f"[{info}]" for info in info_expansions])
        display_text = f"{surface_text} {expansion_str}".strip()

        # Update the context stack with the clean title
        new_stack = context_stack + [surface_text]

        return display_text, new_stack, collected_metadata

    def _identify_entity_type(self, key: str, name_type: str) -> tuple:
        """
        Helper to map XML attributes and key formats to your Model prefixes.
        """
        key_upper = key.upper()
        
        # Priority 1: Check by Key Prefix
        if key_upper.startswith("PRC"):
            return "protag_creations", "PRC"
        if key_upper.startswith("CRT"):
            return "creations", "CRT"
        if key_upper.startswith("PSN"):
            return "people", "PSN"
        
        # Priority 2: Check for Letters (gb-, fmb-, or LET)
        if key.lower().startswith(("gb-", "fmb-")):
            return "letters", "LET"
            
        # Priority 3: Fallback by XML 'type' attribute
        if name_type == "author":
            return "people", "PSN"
        if name_type in ["dramatic_work", "musical_work"]:
            return "creations", "CRT"
            
        return "general", "CRT"
