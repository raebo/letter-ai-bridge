import re
from lxml import etree

from app.indexer.handler import PlaceHandler, NoteHandler, TitleHandler, PersNameHandler, DefaultHandler
from app.utils.string_cleaner import StringCleaner

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
        'default': DefaultHandler(),
        'title': TitleHandler(),
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
    def process_children(cls, node, namespaces):
        """Recursively processes child nodes, applying handlers where applicable."""
        combined_text = []
        combined_metadata = {} 

        # 1. Handle text before any tags
        if node.text:
            combined_text.append(node.text)

        # 2. Iterate through children
        for child in node:
            if not isinstance(child, etree._Element):
                continue

            if child.get("style") == "hidden":
                    # We still want the metadata from hidden tags!
                    _, hidden_meta = cls.process_node(child, namespaces)
                    if isinstance(hidden_meta, dict):
                        combined_metadata.update(hidden_meta)
                    
                    # BUT: We append the tail (text after the hidden tag) and skip its text
                    if child.tail:
                        combined_text.append(child.tail)
                    continue

            tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
            handler = cls._handlers.get(tag, cls._handlers['default'])

            # --- BRANCH A: Specific Handler Found ---
            if handler != cls._handlers['default']:
                res_text, res_meta = cls.process_node(child, namespaces)
                combined_text.append(StringCleaner.normalize_content(res_text))

                if res_meta and isinstance(res_meta, dict):
                    combined_metadata.update(res_meta)

                if child.tail:
                    combined_text.append(StringCleaner.normalize_content(child.tail))

                # Stop processing sibling nodes as per your requirement
                break

            # --- BRANCH B: Generic Recursion ---
            child_text, child_meta = cls.process_node(child, namespaces)
            combined_text.append(child_text)
            
            # Use .update() to keep it a dictionary
            if child_meta and isinstance(child_meta, dict):
                combined_metadata.update(child_meta)

            if child.tail:
                combined_text.append(StringCleaner.normalize_content(child.tail))

        # Join and one last pass to ensure no gaps at the seams
        final_str = "".join(combined_text)
        return StringCleaner.normalize_content(final_str), combined_metadata

    @classmethod
    def process_node(cls, node, namespaces):
        """Dispatcher: Finds a handler or uses the default logic."""
        # Clean the tag name (remove namespace)
        tag = node.tag.split('}')[-1] if '}' in node.tag else node.tag
        
        print(f"DEBUG: tag name: {tag}")
        handler = cls._handlers.get(tag, cls._handlers['default'])
        
        # Pass the cleaner itself as a 'controller' so handlers can report keys
        result_text, updated_stack, metadata = handler.handle(
                node, 
                namespaces, 
                cls._context_stack,
                cls
                )

        if updated_stack is not None:
            cls._context_stack = updated_stack
            # Keep stack lean (max 2 items)
            if len(cls._context_stack) > 2:
                cls._context_stack = cls._context_stack[-2:]

        return result_text, metadata
