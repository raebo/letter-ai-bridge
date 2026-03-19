import unittest
from unittest.mock import MagicMock, patch
from lxml import etree

from app.indexer.handler.title_handler import TitleHandler
# Note: Ensure these paths match your actual project structure
#from app.database.models.protag_creation import ProtagCreation

class TestTitleHandler(unittest.TestCase):
    def setUp(self):
        self.handler = TitleHandler()
        self.ns = {"tei": "http://www.tei-c.org/ns/1.0"}

    def _setup_mock(self, mock_fetch):
        """Helper to define standard mock behavior for all test methods."""
        def side_effect_logic(category, prefix, key):
            if "PRC" in key:
                return {
                    "info": f"Work: {key} Info", 
                    "metadata": {"key": key, "type": "work"}
                }
            if "PSN" in key:
                return {
                    "info": f"Person: {key} Info", 
                    "metadata": {"key": key, "type": "person"}
                }
            if "CRT" in key:
                return {
                    "info": f"Creation: {key} Info",
                    "metadata": {"key": key, "type": "creation"}
                }
            if "gb-" in key:
                return {
                    "info": "Letter: Eichhorn an Mendelssohn, 6. Juni 1841",
                    "metadata": {"key": key}
                }
            return {"info": None, "metadata": {}}
        
        mock_fetch.side_effect = side_effect_logic

    @patch('app.indexer.handler.base_handler.TEIElementHandler._get_or_fetch_entity')
    def test_mendelssohn_work_with_author(self, mock_fetch):
        self._setup_mock(mock_fetch)
        xml = """
        <title xmlns="http://www.tei-c.org/ns/1.0">Paulus
            <name key="PSN0000001" style="hidden" type="author">Mendelssohn Bartholdy</name>
            <name key="PRC0100114" style="hidden">Paulus op. 36</name>
        </title>
        """
        node = etree.fromstring(xml)
        content, _, meta = self.handler.handle(node, self.ns, [])

        self.assertIn("Paulus", content)
        self.assertIn("[Work: PRC0100114 Info]", content)
        self.assertIn("[Person: PSN0000001 Info]", content)
        self.assertEqual(len(meta), 2)    
        
    @patch('app.indexer.handler.base_handler.TEIElementHandler._get_or_fetch_entity')
    def test_gb_letter_with_author(self, mock_fetch):
        self._setup_mock(mock_fetch)
        xml = """
        <title xmlns="http://www.tei-c.org/ns/1.0" xml:id='title_123'>
            Schreiben vom 6ten
            <name key="PSN0110854" style="hidden">Eichhorn</name>
            <name key="gb-1841-06-06-02" style="hidden">Letter Details</name>
        </title>
        """
        node_letter = etree.fromstring(xml)
        content, stack, meta = self.handler.handle(node_letter, self.ns, [])
        
        self.assertIn("Schreiben vom 6ten", content)
        self.assertIn("[Letter: Eichhorn an Mendelssohn, 6. Juni 1841]", content)
        self.assertIn("gb-1841-06-06-02", meta)

    @patch('app.indexer.handler.base_handler.TEIElementHandler._get_or_fetch_entity')
    def test_gb_letter_with_author_with_hi(self, mock_fetch):
        self._setup_mock(mock_fetch)
        xml = """
        <title xmlns="http://www.tei-c.org/ns/1.0" xml:id='title_456'>
            Schreiben vom 6<hi rend="superscript">ten</hi>
            <name key="PSN0110854" style="hidden">Eichhorn</name>
            <name key="gb-1841-06-06-02" style="hidden">Letter Details</name>
        </title>
        """
        node_letter = etree.fromstring(xml)
        content, stack, meta = self.handler.handle(node_letter, self.ns, [])
        
        # Test if "6ten" is correctly joined despite the <hi> tag
        self.assertIn("Schreiben vom 6ten", content)
        self.assertIn("gb-1841-06-06-02", meta)

    @patch('app.indexer.handler.base_handler.TEIElementHandler._get_or_fetch_entity')
    def test_creation_with_author(self, mock_fetch):
        self._setup_mock(mock_fetch)
        xml_radziwill = """
        <title xmlns="http://www.tei-c.org/ns/1.0">
            <hi rend="latintype">Radziwill’s</hi> <hi rend="latintype">Faust</hi>
            <name key="PSN0114055" style="hidden" type="author">Radziwill</name>
            <name key="CRT0110373" style="hidden" type="music">Compositionen</name>
        </title>
        """
        node_radziwill = etree.fromstring(xml_radziwill)

        content, stack, meta = self.handler.handle(node_radziwill, self.ns, [])
        
        self.assertIn("Radziwill’s Faust", content)
        self.assertIn("[Creation: CRT0110373 Info]", content)
        self.assertIn("CRT0110373", meta)

    @patch('app.indexer.handler.base_handler.TEIElementHandler._get_or_fetch_entity')
    def test_title_with_multiple_authors(self, mock_fetch):
        self._setup_mock(mock_fetch)
        # Scenario: A title mentioning two people but no specific work key (PRC/CRT)
        xml = """
        <title xmlns="http://www.tei-c.org/ns/1.0">Briefwechsel zwischen
            <name key="PSN0000001">Mendelssohn</name> und 
            <name key="PSN0000002">Devrient</name>
        </title>
        """
        node = etree.fromstring(xml)
        content, _, meta = self.handler.handle(node, self.ns, [])

        # 1. Check that surface text is preserved
        self.assertIn("Briefwechsel zwischen", content)
        
        # 2. Check that BOTH people are resolved and appended
        self.assertIn("[Person: PSN0000001 Info]", content)
        self.assertIn("[Person: PSN0000002 Info]", content)
        
        # 3. Check metadata contains both entries
        self.assertIn("PSN0000001", meta)
        self.assertIn("PSN0000002", meta)
        self.assertEqual(len(meta), 2)

if __name__ == '__main__':
    unittest.main()
