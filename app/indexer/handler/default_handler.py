from .base_handler import TEIElementHandler

class DefaultHandler(TEIElementHandler):
    def handle(self, node, namespaces, context_stack):
        # 1. Get the clean text of the current node
        clean_text = self.get_clean_text(node)

        print(f"DEBUG:DefaultHandler tag name: {node}")
        
        # 2. Return it as-is with no additional metadata or context changes
        return f" {clean_text} ", context_stack, {}
