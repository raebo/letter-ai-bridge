import re

class StringCleaner:
    @staticmethod
    def normalize_name(raw_name: str) -> str:
        if not raw_name:
            return ""

        # 1. Handle arrows: Replace '→ → →' or '→' with a simple space
        # This merges "Johanna" and "Kinkel" into one searchable string
        clean = re.sub(r'→+', ' ', raw_name)

        # 2. Remove specific annotation markers but keep the names
        # Removes: (Pseud.), [MSB irrt.], etc.
        clean = re.sub(r'\(Pseud\.\)', '', clean)
        clean = re.sub(r'\[.*?\]', '', clean) # Removes anything in []

        # 3. Clean up whitespace
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
