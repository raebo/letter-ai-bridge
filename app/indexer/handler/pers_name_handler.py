from .base_handler import TEIElementHandler


class PersNameHandler(TEIElementHandler):
    def handle(self, node, namespaces, context_stack):
        # 1. Get the name as written in the text (e.g., "Felix")
        surface_name = "".join(node.xpath(".//text()")).strip()
        key = node.get("key")
        
        metadata_to_return = {}
        display_text = surface_name

        if key:
            # 2. Fetch the "Master Data" from your DB
            entity = self._get_or_fetch_entity(category="people", prefix="PSN", key=key)
            
            if entity.get("info"):
                # 3. Enhance the text: "Felix [Mendelssohn Bartholdy, Jacob Ludwig Felix (PSN0001)]"
                # This makes the chunk highly searchable for the full name!
                display_text = f"{entity['info']} [{key}]"
                
                # 4. Store the structured metadata  later filtering
                metadata_to_return = {key: entity["metadata"]}

        new_stack = context_stack + [surface_name]
        
        # Return the enhanced text, the context, and the DB metadata
        return f" {display_text} ", new_stack, metadata_to_return
