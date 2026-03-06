import re
from app.indexer.handler import PlaceHandler, NoteHandler

class TEICleaner:
    _captured_keys = {
            "people": set(),
            "sights": set(),
            "institutions": set(),
            "settlements": set(),
            "countries": set(),
            "creations": set(),
            "protag_creations": set()
            }

    _handlers = {
        'placeName': PlaceHandler(),
        'note': NoteHandler(),
    }

    _context_stack = [] # this is for storing the last contextual information, e.g. the last mentioned place, person, etc.

    @staticmethod
    def clean_whitespace(text):
        if not text:
            return ""
        return " ".join(text.split())

    @staticmethod
    def heal_word_breaks(text):
        """Löst Worttrennungen auf, z.B. 'Ver- hältniße' -> 'Verhältnisse'"""
        # Removes hyphen + optional whitespace between word parts
        return re.sub(r'(\w+)-\s*(\w+)', r'\1\2', text)

    @classmethod
    def reset(cls):
        """Setzt den Kontext zurück, z.B. am Seitenwechsel."""
        cls._context_stack = []
        for key in cls._captured_keys:
            cls._captured_keys[key].clear()

    @classmethod
    def report_key(cls, category, key):
        """Register a key under specified category for later context injection."""
        if category in cls._captured_keys:
            cls._captured_keys[category].add(key)

    @classmethod
    def get_captured_keys(cls, category):
        """Convert sets to lists for JSON serialization and return captured keys for a category."""
        return { cat: list(keys) for cat, keys in cls._captured_keys.items() if keys }

    @classmethod
    def process_node(cls, node, namespaces):
        """Transform a XML node into a clean text for KI."""
        tag = node.tag.replace(f'{{{namespaces["tei"]}}}', '') if "{" in node.tag else node.tag

        handler = cls._handlers.get(tag)

        if handler:
            result, updated_stack = handler.handle(node, namespaces, cls._context_stack)

            if updated_stack is not None:
                cls._context_stack = updated_stack
                # Optional: Stack begrenzen, damit Kontext nicht über Seiten hinweg mitschleppt
                if len(cls._context_stack) > 2:
                    cls._context_stack = []

            return result
        
        # 1. names with IDs (Context Injection)
        if tag in ['name', 'persName', 'placeName', 'title']:
            key = node.get("key")
            name_text = "".join(node.xpath(".//text()")).strip()
            return f" {name_text} [{key}] " if key else name_text

        # 2. Editorial notes (marking)
        if tag == 'note':
            note_text = "".join(node.xpath(".//text()")).strip()
            # Wir markieren Anmerkungen, damit die KI den Kontext versteht
            return f" [Anm.: {note_text}] "

        # 3. Milestones (Ignore)
        if tag in ['pb', 'lb', 'cb', 'fw']:
            return ""

        # 4. Default: Recursive text extraction
        return "".join(node.xpath(".//text()"))
