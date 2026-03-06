from .base_handler import TEIElementHandler
from ..handlers.tei_cleaner import TEICleaner

class PersNameHandler(TEIElementHandler):
    def handle(self, node, namespaces, context_stack):
        
        key = node.get("key") or "".join(node.xpath(".//tei:persName/@key", namespaces=namespaces))

        if key:
            TEICleaner.report_key("people", key)
        
        display_text = f"{name} [{key}]" if key else name
        new_stack = context_stack + [name] if name else context_stack
        return f" {display_text} ", new_stack
