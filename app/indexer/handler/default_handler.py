from .base_handler import TEIElementHandler

class DefaultHandler(TEIElementHandler):

    def handle(self, node, namespaces, stack, cleaner):
        text, metadata = cleaner.process_children(node, namespaces)

        return text, stack, metadata
