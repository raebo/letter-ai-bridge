from lxml import etree
from app.indexer.tei_cleaner import TEICleaner # Dein Cleaner

class TEIChunker:
    def __init__(self, xml_path):
        self.xml_path = xml_path
        self.cleaner = TEICleaner()
        # Der TEI Namespace
        self.namespaces = {'tei': 'http://www.tei-c.org/ns/1.0'}

    def parse_to_chunks(self, sentences_per_chunk=3):
        tree = etree.parse(self.xml_path)
        date_node = tree.xpath('//tei:profileDesc/tei:creation/tei:date/@when', namespaces=self.namespaces)
        letter_year = date_node[0][:4] if date_node else "Unknown"
        
        # Wir suchen nach allen <p> Tags innerhalb von <body>
        # Das 'tei:' Präfix ist entscheidend!
        paragraphs = tree.xpath('//tei:text/tei:body//tei:p', namespaces=self.namespaces)
        
        chunks = []
        for p in paragraphs:
            # 1. Text extrahieren (inkl. Text in Unterelementen wie <persName>)
            raw_text = TEICleaner.process_node(p, self.namespaces)
            
            # 2. Deinen Cleaner drüberlaufen lassen
            cleaned_text = TEICleaner.clean_whitespace(raw_text)
            cleaned_text = TEICleaner.heal_word_breaks(cleaned_text)
            
            if len(cleaned_text.strip()) > 10: # Leere/kurze Tags ignorieren
                # Metadaten extrahieren (optional: z.B. die xml:id des Absatzes)
                p_id = p.get('{http://www.w3.org/XML/1998/namespace}id')
                
                chunks.append({
                    "content": cleaned_text,
                    "metadata": {
                        "paragraph_id": p_id,
                        "type": "letter_body",
                        "letter_year": letter_year
                    }
                })
        
        return chunks
