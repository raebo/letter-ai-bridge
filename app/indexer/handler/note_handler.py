from .base_handler import TEIElementHandler

class NoteHandler(TEIElementHandler):
    def handle(self, node, namespaces, context_stack):
        note_type = node.get("type")
        text = self.get_clean_text(node)

        if note_type == "single_place_comment" and context_stack:
            last_element = context_stack[-1] if context_stack else None
            # Wenn der Stack nicht leer ist, beziehen wir uns auf das letzte Element
            return f" [Info zu {last_element}: {text}] ", context_stack

        prefixes = {
                "single_place_comment": "Orts-Info",
                "biographical": "Bio-Info",
                "critical": "Kritischer Apparat"
                }
        prefix = prefixes.get(note_type, "Anm")
        return f" [{prefix}: {text}] ", context_stack
