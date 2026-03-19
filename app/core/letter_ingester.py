from lxml import etree
from app.indexer.tei_chunker import TEIChunker
from app.indexer.tei_header_chunker import TEIHeaderChunker


class LetterIngester:
    def __init__(self, model):
        self.model = model
        self.header_parser = TEIHeaderChunker()
        self.namespaces = {'tei': 'http://www.tei-c.org/ns/1.0'}

    def process_letter(self, letter_record):
        """
        Transforms a database Letter record into a list of vectorized chunks.
        """
        xml_content = letter_record.xml_content
        processed_chunks = []

        # 1. Parse Header
        root = etree.fromstring(xml_content.encode('utf-8'))
        header_node = root.xpath('./tei:teiHeader', namespaces=self.namespaces)[0]
        header_text = self.header_parser.parse(header_node)
        
        # 2. Parse Body
        body_chunker = TEIChunker(xml_content)
        raw_body_chunks = body_chunker.parse_to_chunks(sentences_per_chunk=3)

        # 3. Vectorize everything in one batch (Header + all Body chunks)
        all_texts = [header_text] + [c['content'] for c in raw_body_chunks]
        vectors = self.model.encode(all_texts, convert_to_numpy=True, show_progress_bar=False)

        # 4. Assemble Header Chunk
        processed_chunks.append({
            "letter_id": letter_record.id,
            "content": header_text,
            "metadata": {
                "letter_id": letter_record.id,
                "letter_name": letter_record.name,
                "type": "header"
            },
            "vector": vectors[0].tolist()
        })

        # 5. Assemble Body Chunks
        for i, chunk in enumerate(raw_body_chunks):
            full_metadata = chunk.get('metadata', {})
            full_metadata.update({
                "letter_id": letter_record.id,
                "letter_name": letter_record.name,
                "type": "body"
            })
            
            processed_chunks.append({
                "letter_id": letter_record.id,
                "content": chunk['content'],
                "metadata": full_metadata,
                "vector": vectors[i+1].tolist()
            })

        return processed_chunks
