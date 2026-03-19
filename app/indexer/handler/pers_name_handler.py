from .base_handler import TEIElementHandler

class PersNameHandler(TEIElementHandler):


    def handle(self, node, namespaces, context_stack, cleaner=None):
        # 1. Get the key from the node OR its children
        key = node.get("key") or node.xpath("./*[@key]/@key")[0] if node.xpath("./*[@key]/@key") else None
        
        # 2. Get the clean surface name (only the actual text meant to be read)
        # Often in TEI, we want the text immediate to the node, not the 'hidden' name tags
        surface_name = node.xpath("text()")[0].strip() if node.xpath("text()") else ""
        
        metadata_to_return = {}
        display_text = surface_name

        if key:
            entity = self._get_or_fetch_entity(category="people", prefix="PSN", key=key)
            
            if entity.get("info"):
                # Use the clean surface name + the DB info
                # Result: "Herr von Maßows [Person: Massow, Ludwig Friedrich (1794-1859)]"
                display_text = f"{surface_name} [{entity['info']}]"
                metadata_to_return = {key: entity["metadata"]}

        new_stack = context_stack + [surface_name]

        return f" {display_text} ", new_stack, metadata_to_return
