from .base_handler import TEIElementHandler
from app.database.services.entity_resolution.retrieve_entity_infos_service import RetrieveInfosService

class PersNameHandler(TEIElementHandler):
    def handle(self, node, namespaces, context_stack):
        surface_name = "".join(node.xpath(".//text()")).strip()
        key = node.get("key")
        
        metadata_to_return = {}
        display_text = surface_name

        if key:
            # Call the base class helper
            entity = self._get_or_fetch_entity(category="people", prefix="PSN", key=key)
            
            if entity.get("info"):
                display_text = f"{entity['info']} [{key}]"
                metadata_to_return = {key: entity["metadata"]}

        new_stack = context_stack + [surface_name]
        return f" {display_text} ", new_stack, metadata_to_return
