from lxml import etree
import re

import logging
logger = logging.getLogger(__name__)

class TEIHeaderChunker:
    # The template the AI will see as the first chunk of a letter
    HEADER_TEMPLATE = """
[LETTER METADATA]
Title: {title}
Date: {date}
Origin: {origin}
Correspondence: {sender} -> {recipient}
Writers: {writers}
Attachments/Material: {attachments}
Summary/Incipit: {incipit}
---
""".strip()

    def __init__(self, namespaces=None):
        self.namespaces = namespaces or {
            'tei': 'http://www.tei-c.org/ns/1.0',
            'xml': 'http://www.w3.org/XML/1998/namespace'
        }

    def _get_text(self, node, xpath_query):
        """Helper to safely extract text from xpath."""
        results = node.xpath(xpath_query, namespaces=self.namespaces)
        if results:
            # Join all text parts and clean whitespace
            full_text = " ".join([str(r.text) if hasattr(r, 'text') else str(r) for r in results if r is not None])
            return re.sub(r'\s+', ' ', full_text).strip()
        return "Not specified"

    def _extract_date(self, root):
        """
        Robustly extracts the date from tei:creation.
        """
        logger.debug("Starting date extraction process.") # Only shows if DEBUG is enabled

        # 1. Try @when
        date_when = root.xpath(".//tei:profileDesc/tei:creation/tei:date/@when", namespaces=self.namespaces)
        if date_when and date_when[0]:
            val = str(date_when[0])
            logger.debug(f"Found machine-readable date: {val}")
            return val

        # 2. Try <date> text
        date_text = root.xpath(".//tei:profileDesc/tei:creation/tei:date/text()", namespaces=self.namespaces)
        if date_text:
            val = " ".join([str(t).strip() for t in date_text if t]).strip()
            logger.debug(f"Found tag-based date text: {val}")
            return val

        # 3. Fallback (The Westmorland fix)
        creation_text = root.xpath(".//tei:profileDesc/tei:creation//text()", namespaces=self.namespaces)
        if creation_text:
            val = " ".join([str(t).strip() for t in creation_text if t]).strip()
            if val:
                logger.warning(f"No <date> tag found. Falling back to raw <creation> text: {val}")
                return val

        logger.error("Could not find any date information in tei:creation!")
        return "Not specified"

    def parse(self, header_xml_string):
        """Parses the TEI Header and returns a formatted string chunk."""
        if isinstance(header_xml_string, str):
            root = etree.fromstring(header_xml_string.encode('utf-8'))
        else:
            root = header_xml_string

        # 1. Title Statement
        title = self._get_text(root, ".//tei:titleStmt/tei:title[@xml:id][1]")

        # 2. Normalized Date
        date = self._extract_date(root)

        logger.debug(f"Extracted date: {date}") # Only shows if DEBUG is enabled

        # 3. Origin (Writing Place)
        origin = self._get_text(root, ".//tei:correspAction[@type='sent']/tei:placeName//text()")


        logger.debug(f"Extracted origin: {origin}") # Only shows if DEBUG is enabled

        # 4. Sender & Recipient
        sender = self._get_text(root, ".//tei:correspAction[@type='sent']/tei:persName[@resp='author']//text()")

        logger.debug(f"Extracted sender: {sender}") # Only shows if DEBUG is enabled

        recipient = self._get_text(root, ".//tei:correspAction[@type='received']/tei:persName//text()")

        logger.debug(f"Extracted recipient: {recipient}") # Only shows if DEBUG is enabled

        # 5. Writers (Handled separately as requested)
        writers = self._get_text(root, ".//tei:titleStmt/tei:respStmt/tei:persName[@resp='writer']//text()")

        logger.debug(f"Extracted writers: {writers}") # Only shows if DEBUG is enabled

        # 6. Attachments (accMat)
        # Pulls the descriptions of accompanying materials
        attachments_list = root.xpath(".//tei:physDesc/tei:accMat//tei:bibl/text()", namespaces=self.namespaces)
        attachments = " | ".join([a.strip() for a in attachments_list]) if attachments_list else "None"

        logger.debug(f"Extracted attachments: {attachments}") # Only shows if DEBUG is enabled

        # 7. Incipit (Useful for AI to have a preview of the content)
        incipit = self._get_text(root, ".//tei:msContents//tei:incipit//text()")

        logger.debug(f"Extracted incipit: {incipit}") # Only shows if DEBUG is enabled

        # Fill the template
        formatted_header = self.HEADER_TEMPLATE.format(
            title=title,
            date=date,
            origin=origin,
            sender=sender,
            recipient=recipient,
            writers=writers,
            attachments=attachments,
            incipit=incipit
        )

        return formatted_header

# Example Usage:
# chunker = TEIHeaderChunker()
# header_chunk = chunker.parse(xml_data)
