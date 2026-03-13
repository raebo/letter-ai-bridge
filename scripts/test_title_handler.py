import sys
import os
from lxml import etree

# Ensure project root is in path for absolute imports
sys.path.append(os.getcwd())

from app.core.config import settings
from app.database.connection import DBConnection
from app.indexer.handler.title_handler import TitleHandler
from app.indexer.tei_cleaner import TEICleaner 

def run_title_test():
    # 1. Setup Database Connection
    print("--- Initializing DB Connection ---")
    DBConnection.set_config(settings.db_params)
    
    # 2. Define Namespaces (Crucial for lxml xpath)
    ns = {"tei": "http://www.tei-c.org/ns/1.0"}
    
    # 3. Test Cases
    test_cases = [
        {
            "name": "PROTAG_CREATION (Paulus)",
            "xml": """<title xmlns="http://www.tei-c.org/ns/1.0">Paulus<list type="fmb_works_directory"> <item n="1" sortKey="musical_works"/></list><name key="PSN0000001" type="author">Mendelssohn...</name><name key="PRC0100114" style="hidden">Paulus...<idno type="MWV">A 14</idno></name></title>"""
        },
        {
            "name": "LETTER (Eichhorn)",
            "xml": """<title xmlns="http://www.tei-c.org/ns/1.0">Schreiben vom 6<hi rend="superscript">ten</hi> v. M.<name key="PSN0110854" type="author">Eichhorn...</name><name key="gb-1841-06-06-02" type="letter">Johann Albrecht...</name></title>"""
        },
        {
            "name": "EXTERNAL_CREATION (Faust/Goethe)",
            "xml": """<title xmlns="http://www.tei-c.org/ns/1.0">Faust<name key="PSN0111422" type="author">Goethe...</name><name key="CRT0108814" type="dramatic_work">Faust I</name></title>"""
        }
    ]

    handler = TitleHandler()
    
    print(f"\n{'TEST CASE':<30} | {'ENHANCED CONTENT'}")
    print("-" * 100)

    for case in test_cases:
        try:
            # Parse the XML string
            node = etree.fromstring(case['xml'])
            
            # Reset the cleaner stack for a clean test
            TEICleaner.reset() 
            
            # Execute Handler logic
            display_text, stack, metadata = handler.handle(node, ns, [])
            
            print(f"{case['name']:<30} | {display_text}")
            if metadata:
                print(f"{'':<30} | Keys Found: {list(metadata.keys())}")
            print("-" * 100)
            
        except Exception as e:
            print(f"Error in {case['name']}: {e}")

if __name__ == "__main__":
    run_title_test()
