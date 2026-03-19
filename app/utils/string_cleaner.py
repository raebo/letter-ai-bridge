import re

class StringCleaner:

    @staticmethod
    def normalize_content(text: str) -> str:
        if not text:
            return ""

        # 1. Squash all newlines, tabs, and multiple spaces into one single space
        # This fixes the XML "pretty print" indentation issue
        clean = re.sub(r'\s+', ' ', text)

        # 2. Handle specific artifacts if needed (like the arrows)
        clean = clean.replace('[→]', '').strip()

        # 3. Final collapse of any double spaces created by replacements
        clean = re.sub(r'\s+', ' ', clean).strip()

        return clean

    @staticmethod
    def normalize_name(text: str) -> str:
        if not text:
            return ""

        # 1. Replace newlines, carriage returns, and tabs with a space
        # This handles the \r\n found in your "G1833" notes
        clean = text.replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')

        # 2. Handle arrows: Replace '→ → →' with a space
        clean = re.sub(r'→+', ' ', clean)

        # 3. Remove specific markers and brackets
        # Removes: (Pseud.), [MSB irrt.], etc.
        clean = re.sub(r'\(Pseud\.\)', '', clean)
        clean = re.sub(r'\[.*?\]', '', clean) 

        # 4. Clean up whitespace (Collapse multiple spaces into one)
        clean = re.sub(r'\s+', ' ', clean).strip()

        return clean


    @staticmethod
    def _process_letter_name(raw_val: str) -> str:
        if not raw_val: return ""
        
        # 1. Remove parenthetical descriptions like (Eigenbezeichnung...)
        # We look for long descriptions inside parens and cut them
        clean = re.sub(r'\([^)]+ [^)]+\)', '', raw_val)
        
        # 2. Handle dated nicknames: Ralph (1829) -> Ralph
        clean = re.sub(r'\((\d{4})\)', '', clean)
        
        # 3. Clean up the commas and whitespace
        parts = [p.strip() for p in clean.split(',') if len(p.strip()) > 1]
        
        # 4. Limit the number of aliases to avoid "diluting" the vector
        # We take the first 4 most important aliases
        return ", ".join(parts[:4])


    @staticmethod
    def extract_bio_summary(raw_notes: str) -> str:
        """
        Extracts the first descriptive sentence for AI context.
        Removes research noise like bibliographical codes or internal markers.
        """
        if not raw_notes: return ""

        # 1. Take first sentence
        first_part = re.split(r'\.\s|\n', raw_notes)[0]

        # 2. Clean noise (MSB Bd. 12, etc.)
        clean = re.sub(r'^[A-Z]{2,3}\s(Bd\.|Vol\.)\s?\d+:\s?', '', first_part)
        
        # 3. Remove leading name repetition (e.g., "Mialle, Simon (1786-1840), ")
        # This looks for a string of text followed by dates in parens and a comma
        clean = re.sub(r'^.*?\(.*?\),?\s?', '', clean)

        return clean.strip()

