from .base_handler import TEIElementHandler

from app.utils.string_cleaner import StringCleaner

class PlaceHandler(TEIElementHandler):

    def _get_key_config(self, key: str):
        key_upper = key.upper()
        if key_upper.startswith("STM"):
            return "settlements", "STM"
        if key_upper.startswith("SGH"):
            return "sights", "SGH"
        if key_upper.startswith("NST"):
            return "institions", "NST"
        return None, None

    def handle(self, node, namespaces, context_stack, cleaner = None):
        """
        Processes <placeName> tags.
        Extracts the visible name (e.g., 'Dresden') and fetches metadata 
        from nested settlement, country, or name tags.
        """
        # 1. Get the surface text (the text physically between the tags)
        # We strip to remove the XML newlines we discussed
        surface_text = "".join(node.xpath("text()", namespaces=namespaces)).strip()

        # 2. Collect all potential keys from children (settlement, name, country)
        # We look for any child with a @key attribute
        entity_nodes = node.xpath(".//*[@key]", namespaces=namespaces)
        all_keys = [n.get("key") for n in entity_nodes]

        
        if not all_keys:
            return f" {surface_text} ", context_stack, {}

        raw_info_strings = []
        metadata_to_return = {}

        for key in all_keys:
            category, prefix = self._get_key_config(key)
            
            print(f"DEBUG: Processing key '{key}' with category '{category}' and prefix '{prefix}'")

            if category and prefix:
                res = self._get_or_fetch_entity(category, prefix, key)
                
                if res:
                    # Collect info for the bracketed display
                    if res.get("info"):
                        clean_info = res['info'].replace('[', '').replace(']', '')
                        raw_info_strings.append(clean_info)
                    
                    # Store in metadata dictionary
                    metadata_to_return[key] = {
                        **res.get("metadata", {}),
                        "entity_type": category,
                        "prefix": prefix
                    }

        # 4. Consolidate info into a single bracket
        if raw_info_strings:
            combined_info = " | ".join(raw_info_strings)
            full_display = f"{surface_text} [{combined_info}]"
        else:
            full_display = surface_text

        # Clean up whitespace using your StringCleaner
        full_display = self._format_info_bracket(surface_text, raw_info_strings)

        # Final pass through StringCleaner for whitespace/newlines
        full_display = StringCleaner.normalize_content(full_display)

        return f" {full_display} ", context_stack, metadata_to_return

