from lxml import etree

def process_complete_letter(xml_file_path):
    # 1. Load the complete XML letter
    tree = etree.parse(xml_file_path)
    root = tree.getroot()
    
    # 2. Define Namespaces (TEI letters almost always use this)
    namespaces = {'tei': 'http://www.tei-c.org/ns/1.0'}
    
    # 3. Extract the teiHeader node
    # Note: .xpath returns a list, so we take the first element [0]
    header_node = root.xpath('./tei:teiHeader', namespaces=namespaces)[0]
    
    # 4. Convert the header node to an XML string
    # encoding='unicode' returns a string instead of bytes
    header_xml_string = etree.tostring(header_node, encoding='unicode', pretty_print=True)
    
    # 5. Initialize your chunker and parse
    chunker = TEIHeaderChunker(namespaces=namespaces)
    header_metadata_text = chunker.parse(header_xml_string)
    
    return header_metadata_text
