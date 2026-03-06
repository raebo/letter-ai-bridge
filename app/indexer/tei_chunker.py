from lxml import etree
from app.indexer.tei_cleaner import TEICleaner

class TEIChunker:
    def __init__(self, xml_content):
        """
        Initializes the chunker with XML content from the database.
        :param xml_content: String containing the TEI XML data.
        """
        # lxml prefers byte strings when an encoding declaration is present
        if isinstance(xml_content, str):
            self.xml_data = xml_content.encode('utf-8')
        else:
            self.xml_data = xml_content
            
        self.namespaces = {'tei': 'http://www.tei-c.org/ns/1.0'}

    def parse_to_chunks(self, sentences_per_chunk=3):
        """
        Parses the XML and splits the body text into semantic chunks (paragraphs).
        :return: A list of dictionaries containing cleaned text and metadata.
        """
        # Use fromstring for XML data already loaded into memory
        tree = etree.fromstring(self.xml_data)
        
        # Extract the creation date for metadata
        date_node = tree.xpath('//tei:profileDesc/tei:creation/tei:date/@when', namespaces=self.namespaces)
        letter_year = date_node[0][:4] if date_node else "Unknown"
        
        # Locate all <p> tags within the <body> section
        paragraphs = tree.xpath('//tei:text/tei:body//tei:p', namespaces=self.namespaces)
        
        chunks = []
        for p in paragraphs:
            # Reset context stack for each paragraph to prevent cross-paragraph leakage
            TEICleaner.reset() 
            
            # Iterate through all child nodes (text and elements) of the paragraph
            parts = []
            for node in p.xpath("./node()", namespaces=self.namespaces):
                if isinstance(node, etree._Element):
                    # Process elements (persName, placeName, etc.) via the Handler system
                    parts.append(TEICleaner.process_node(node, self.namespaces))
                else:
                    # Directly append raw text nodes
                    parts.append(str(node))
            
            raw_text = "".join(parts)
            
            # Perform text hygiene
            cleaned_text = TEICleaner.clean_whitespace(raw_text)
            cleaned_text = TEICleaner.heal_word_breaks(cleaned_text)
            
            # Ignore empty tags or very short fragments
            if len(cleaned_text.strip()) > 10:
                # Extract the XML ID of the paragraph for traceability
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
