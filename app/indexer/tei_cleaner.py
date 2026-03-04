import re

class TEICleaner:
    @staticmethod
    def clean_whitespace(text):
        if not text:
            return ""
        return " ".join(text.split())

    @staticmethod
    def heal_word_breaks(text):
        """Löst Worttrennungen auf, z.B. 'Ver- hältniße' -> 'Verhältnisse'"""
        # Entfernt Bindestrich + optionaler Whitespace zwischen Wortteilen
        return re.sub(r'(\w+)-\s*(\w+)', r'\1\2', text)

    @classmethod
    def process_node(cls, node, namespaces):
        """Transformiert einen XML-Knoten in sauberen Text für die KI."""
        tag = node.tag.replace(f'{{{namespaces["tei"]}}}', '') if "{" in node.tag else node.tag
        
        # 1. Namen mit IDs (Context Injection)
        if tag in ['name', 'persName', 'placeName', 'title']:
            key = node.get("key")
            name_text = "".join(node.xpath(".//text()")).strip()
            return f" {name_text} [{key}] " if key else name_text

        # 2. Editorische Anmerkungen (Markierung)
        if tag == 'note':
            note_text = "".join(node.xpath(".//text()")).strip()
            # Wir markieren Anmerkungen, damit die KI den Kontext versteht
            return f" [Anm.: {note_text}] "

        # 3. Meilensteine (Ignorieren)
        if tag in ['pb', 'lb', 'cb', 'fw']:
            return ""

        # 4. Standard: Textinhalt rekursiv extrahieren
        return "".join(node.xpath(".//text()"))
