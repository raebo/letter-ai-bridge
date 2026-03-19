import sys
import os
from lxml import etree

# 1. Add the project root to sys.path so we can import app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.indexer.tei_cleaner import TEICleaner

def test_node_processor():
    # The XML snippet provided
    # Note: I added the TEI namespace to the root <p> to match a real document
    xml_snippet = """
    <p xmlns="http://www.tei-c.org/ns/1.0" style="paragraph_without_indent">
        Am Abende nach der Aufführung des „
        <hi rend="latintype">
          <title xml:id="title_82a2bc84">Paulus
            <list style="hidden" type="fmb_works_directory"> 
              <item n="1" sortKey="musical_works" style="hidden"/> 
            </list>
            <name key="PSN0000001" style="hidden" type="author">Mendelssohn Bartholdy (1809-1847)</name>
            <name key="PRC0100114" style="hidden">Paulus / St. Paul, Oratorium...
              <idno type="MWV">A 14</idno>
              <idno type="op">36</idno>
            </name>
          </title>
        </hi>.“
        <note resp="FMBC" style="hidden" type="single_place_comment">
          der Aufführung des „Paulus.“ – Gemeint ist möglicher Weise...
        </note>
        „Es sind Stellen im „<hi rend="latintype">Paulus</hi>“, bei welchen das Herz jedes Fühlenden überfließen muß...“
    </p>
    """

    # Define the namespaces exactly as they appear in your handlers/cleaner
    namespaces = {
        'tei': 'http://www.tei-c.org/ns/1.0',
        'xml': 'http://www.w3.org/XML/1998/namespace'
    }

    try:
        # Parse the XML
        # etree.fromstring requires the string to be bytes or correctly encoded
        root = etree.fromstring(xml_snippet.strip())

        print("--- Testing TEICleaner.process_node ---")
        
        # Execute the specific method
        # This will trigger the TitleHandler, database fetches, and recursion
        content, metadata = TEICleaner.process_node(root, namespaces)

        print("\n[RESULTING CONTENT]")
        print("-" * 20)
        print(content)
        print("-" * 20)

        print("\n[RESULTING METADATA KEYS]")
        print(list(metadata.keys()))

        # Verification Logic
        print("\n[VERIFICATION]")
        
        # 1. Check for "Bleeding"
        if "Jacob Ludwig Felix" in content:
            print("❌ FAIL: Hidden text (biography) found in content.")
        else:
            print("✅ PASS: Hidden text correctly excluded from content.")

        # 2. Check for Metadata
        if "PSN0000001" in metadata and "PRC0100114" in metadata:
            print("✅ PASS: Metadata keys successfully fetched and merged.")
        else:
            print(f"❌ FAIL: Expected keys missing. Found: {list(metadata.keys())}")

    except Exception as e:
        print(f"CRITICAL ERROR during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_node_processor()
