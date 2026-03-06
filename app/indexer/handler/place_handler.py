from .base_handler import TEIElementHandler

class PlaceHandler(TEIElementHandler):
    def handle(self, node, namespaces, context_stack):
        name = self.get_direct_text(node) or "".join(node.xpath(".//tei:settlement/text()", namespaces=namespaces)).strip()
        key = node.get("key") or "".join(node.xpath(".//tei:settlement/@key", namespaces=namespaces))
        
        display_text = f"{name} [{key}]" if key else name
        new_stack = context_stack + [name] if name else context_stack
        return f" {display_text} ", new_stack
