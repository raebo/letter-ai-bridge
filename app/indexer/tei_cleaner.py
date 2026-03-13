import re
from app.indexer.handler import PlaceHandler, NoteHandler, PersNameHandler, DefaultHandler

class TEICleaner:
    _captured_keys = {
            "people": {},
            "sights": {},
            "institutions": {},
            "settlements": {},
            "countries": {},
            "creations": {},
            "protag_creations": {},
            "letters": {},
            }

    _handlers = {
        'placeName': PlaceHandler(),
        'persName': PersNameHandler(),
        'note': NoteHandler(),
        'default': DefaultHandler()
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
    def report_key(cls, category, key, info_string, **metadata):
        """
        Register a key with its info string and a flexible metadata hash.
        Usage: StringCleaner.report_key("people", "PSN1", "Felix...", notes="...", gender="m")
        """
        if category in cls._captured_keys:
            cls._captured_keys[category][key] = {
                "info": info_string,
                "metadata": metadata  # This is now a dict: {'notes': '...', 'etc': '...'}
            }

    @classmethod
    def get_captured_keys(cls, category=None):
        """Returns the dictionary for a specific category or the whole cache."""
        if category:
            # Return the specific category dict, or an empty dict if not found
            return cls._captured_keys.get(category, {})
        return cls._captured_keys

    @classmethod
    def process_node(cls, node, namespaces):
        """Dispatcher: Finds a handler or uses the default logic."""
        # Clean the tag name (remove namespace)
        tag = node.tag.split('}')[-1] if '}' in node.tag else node.tag
        
        # Get specific handler or use a fallback 'GenericHandler'

        print(f"DEBUG: tag name: {tag}")
        handler = cls._handlers.get(tag, cls._handlers['default'])
        
        # Pass the cleaner itself as a 'controller' so handlers can report keys
        result_text, updated_stack, metadata = handler.handle(node, namespaces, cls._context_stack)

        if updated_stack is not None:
            cls._context_stack = updated_stack
            # Keep stack lean (max 2 items)
            if len(cls._context_stack) > 2:
                cls._context_stack = cls._context_stack[-2:]

        return result_text, metadata
