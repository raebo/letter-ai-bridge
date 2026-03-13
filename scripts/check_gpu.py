import torch
from lxml import etree
from sentence_transformers import SentenceTransformer

# 1. SETUP: Check if your RTX card is visible
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"--- Using device: {device.upper()} ---")

# 2. LOAD MODEL: A great multilingual model for German
# This will download (~400MB) the first time you run it
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2', device=device)

def process_tei_xml(xml_string):
    # Parse the XML
    root = etree.fromstring(xml_string)
    
    chunks = []
    # Find all paragraphs
    for p in root.xpath('//p'):
        # Extract text and person IDs
        text = "".join(p.xpath(".//text()")).strip()
        person_ids = p.xpath('.//name/@key')
        
        if len(text) > 20:
            # CREATE THE EMBEDDING (The AI Magic)
            # This turns the text into 384 numbers
            vector = model.encode(text)
            
            chunks.append({
                "content": text,
                "entities": person_ids,
                "vector": vector.tolist()
            })
    return chunks

# TEST DATA (Your snippet)
example_xml = """
<p>Der Vagabunde <persName xml:id="p1">Heinrich Conrad Schleinitz
<name key="PSN0114567">Schleinitz</name></persName> wurde festgenommen.</p>
"""

results = process_tei_xml(example_xml.encode('utf-8'))
print(f"Successfully created {len(results)} chunk(s).")
print(f"First 5 numbers of the vector: {results[0]['vector'][:5]}")
