from lxml import etree
from app.indexer.tei_cleaner import TEICleaner
from app.utils.string_cleaner import StringCleaner
from app.utils.letter_helper import LetterHelper

import logging
logger = logging.getLogger(__name__)

class TEIChunker:
    def __init__(self, xml_content):
        """
        Initializes the chunker with XML content from the database.
        :param xml_content: String containing the TEI XML data.
        """

        if isinstance(xml_content, str):
            self.xml_data = xml_content.encode('utf-8')
        else:
            self.xml_data = xml_content
            
        self.namespaces = {'tei': 'http://www.tei-c.org/ns/1.0'}
        
        self.tree = etree.fromstring(self.xml_data)

    def parse_to_chunks(self, sentences_per_chunk=3):
        """
        Parses the XML and splits the body text into semantic chunks (paragraphs).
        :return: A list of dictionaries containing cleaned text and metadata.
        """
        
        # Extract the creation date for metadata
        date_node = self.tree.xpath('//tei:profileDesc/tei:creation/tei:date/@when', namespaces=self.namespaces)
        
        letter_year = date_node[0][:4] if date_node else "Unknown"
        
        # Locate all <p> tags within the <body> section
        paragraphs = self.tree.xpath('//tei:text/tei:body//tei:p', namespaces=self.namespaces)
        
        chunks = []
        for p in paragraphs:
            # Reset context stack for each paragraph to prevent cross-paragraph leakage
            TEICleaner.reset() 
            
            # Iterate through all child nodes (text and elements) of the paragraph
            parts = []
            accumulated_entities = {}

            p_id = p.get('{http://www.w3.org/XML/1998/namespace}id')


            nodes = p.xpath("./node()", namespaces=self.namespaces)

            for node in nodes:
                logger.debug(f"Processing node: ")

                if isinstance(node, etree._Element):
                    logger.debug(f"Node <{node.tag}> is an element. Processing with TEICleaner.")
                    text, meta = TEICleaner.process_node(node, self.namespaces)
                    parts.append(text)
                    if meta:
                        logger.debug(f"Extracted metadata from node <{node.tag}>: {meta}")
                        accumulated_entities.update(meta)
                else:
                    parts.append(str(node))

            # Perform text hygiene
            cleaned_text = TEICleaner.clean_whitespace("".join(parts))
            cleaned_text = TEICleaner.heal_word_breaks(cleaned_text)
            
            if len(cleaned_text.strip()) <= 10:
                continue

            # 3. Delegation Phase (The DRY part)
            base_metadata = {
                "paragraph_id": p_id,
                "type": "letter_body",
                "letter_year": letter_year,
                "entities": accumulated_entities
            }
            
            chunks.extend(self._create_sentence_chunks(cleaned_text, base_metadata))
        
        return chunks


    def _create_sentence_chunks(self, text, base_metadata, window_size=3, step_size=2):
        """
        Splits text into overlapping sentence windows.
        """
        sentences = LetterHelper.split_into_sentences(text)
        chunk_list = []

        # If only one sentence, return immediately
        if len(sentences) <= 1:
            chunk_list.append({
                "content": text,
                "metadata": {**base_metadata, "sentence_range": "0-0"}
            })
            return chunk_list

        # Sliding window logic
        for i in range(0, len(sentences), step_size):
            window = sentences[i : i + window_size]
            
            # Stop if the window doesn't move the context forward significantly
            if not window or (i >= len(sentences)):
                break
                
            chunk_list.append({
                "content": " ".join(window),
                "metadata": {
                    **base_metadata, 
                    "sentence_range": f"{i}-{i+len(window)-1}"
                }
            })
        
        return chunk_list
