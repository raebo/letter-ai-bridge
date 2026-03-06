from abc import ABC, abstractmethod
from typing import Tuple, List
import lxml.etree as ET

class TEIElementHandler(ABC):
    @abstractmethod
    def handle(self, node: ET.Element, namespaces: dict, context_stack) -> Tuple[str, List]:
        """
        context_stack: Eine Liste der letzten relevanten Begriffe.
        Gibt zurück: (text_result, updated_stack)
        """
        pass

    def get_clean_text(self, node: ET.Element) -> str:
        # Extrahiert Text und ersetzt alle Whitespace-Sequenzen durch ein Leerzeichen
        raw_text = "".join(node.xpath(".//text()"))
        return " ".join(raw_text.split()).strip()

    def get_direct_text(self, node: ET.Element) -> str:
        """Hilfsmethode: Nur den Text des aktuellen Knotens."""
        return "".join(node.xpath("text()")).strip()
