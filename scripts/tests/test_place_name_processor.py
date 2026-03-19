import sys
import os
from lxml import etree

# 1. Add the project root to sys.path so we can import app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.indexer.tei_chunker import TEIChunker

def test_node_processor():

    xml_snippet = """
    <TEI xmlns="http://www.tei-c.org/ns/1.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:schemaLocation="http://www.tei-c.org/ns/1.0 ../../../fmbc_framework/xsd/fmb-c.xsd"
        xml:id="gb-1841-07-02-01" xml:space="default">
        <teiHeader xml:lang="de">
        </teiHeader>
        <text>
        <body>
        <div type="letter">
            <p style="paragraph_without_indent">
            Am Abende nach der Aufführung des Paulus in
            <placeName xml:id="placeName_158347e8-6585-4996-89ab-90996531c636">
                Dresden
            <settlement key="STM0100142" style="hidden" type="locality">Dresden</settlement>
            <country style="hidden">Deutschland</country>
            </placeName>
            die anderen
            <placeName xml:id="placeName_f8ecad0d-4f9f-4316-98e0-9d2d8f481c56" class="entity_hl">
                Concertanfang
                <name key="NST0100353" style="hidden" subtype="Komitee" type="institution">Verein zur Beförderung der Tonkunst (seit September 1834: Verein für Tonkunst)</name>
                <settlement key="STM0100109" style="hidden" type="locality">Düsseldorf</settlement>
                <country style="hidden">Deutschland</country>
            </placeName>
            und sie errichten mir ein
            <placeName xml:id="placeName_79f6ea30-7ae0-401c-9d09-6abcb759d395" class="entity_hl">
                Schillschen Denkmals
                <name key="SGH0105500" style="hidden" subtype="" type="sight">Schill-Denkmal</name>
                <settlement key="STM0100373" style="hidden" type="locality">Braunschweig</settlement>
                <country style="hidden">Deutschland</country>
            </placeName>
            welches sich in
            <placeName xml:id="placeName_44b4ca70-a21f-4db9-9e97-00595f66e305">
                Frankreich
                <settlement key="STM0104840" style="hidden" type="country">Frankreich</settlement>
                <country style="hidden">Frankreich</country>
            </placeName>
            befindet.
        </p>
        </div>
        </body>
        </text>
        </TEI>
    """

    try:
        # Parse the XML
        # etree.fromstring requires the string to be bytes or correctly encoded
        root = etree.fromstring(xml_snippet.strip())

        chunker = TEIChunker(xml_snippet.strip()) 

        raw_chunks = chunker.parse_to_chunks(sentences_per_chunk=3)

        # Print the resulting chunks and metadata for verification
        for idx, chunk in enumerate(raw_chunks):
            print(f"\n[CHUNK {idx+1}]")
            print("-" * 20)
            print("Content:")
            print(chunk['content'])
            print("\nMetadata Keys:")
            print(list(chunk['metadata'].keys()))
            print("-" * 20)

    except Exception as e:
        print(f"CRITICAL ERROR during test: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_node_processor()
