import re

class LetterHelper:

    ABBREVIATIONS = [
        # Titles & Formalities
        "A. O.", "v. M", "d. M", "d. J", "geb", "Dr", "Prof", "Frl", "Hr", "Hrn", "Sr",
        "Ew", "Excellenz", "Geh", "Wirkl", 
        "op", "Op", "No", "Nr", "Min", "ca", "resp", "u. s. w", "etc", 
        "d. h", "z. B", "bzw", "u. a", "S",
    ]

    MONTHS = [
        "Jan", "Febr", "Mrz", "Apr", "Mai", "Jun", "Jul", "Aug", "Sept", "Okt", "Nov", "Dez",
        "Januar", "Februar", "März", "April", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"
    ]

    @staticmethod
    def extract_date_from_key(key: str) -> str:
        """Extracts YYYY-MM-DD from the letter key."""
        match = re.search(r'(\d{4})-(\d{2})-(\d{2})', key)
        return match.group(0) if match else "Unknown Date"

    @staticmethod
    def split_into_sentences(text: str) -> list:
        temp_text = text
        placeholder = "___DOT___"

        # 1. Handle Dates: Protect "6. Juni", "6. v. M.", etc.
        # This looks for digits + dot + space + (Month or Abbreviation)
        lookahead_items = LetterHelper.MONTHS + LetterHelper.ABBREVIATIONS
        month_pattern = r'(\d+)\.\s+(?=' + '|'.join(map(re.escape, lookahead_items)) + ')'
        temp_text = re.sub(month_pattern, r'\1' + placeholder + ' ', temp_text)

        # 2. Handle Abbreviations: Protect "Ew.", "Geh.", etc.
        sorted_abbrs = sorted(LetterHelper.ABBREVIATIONS, key=len, reverse=True)
        for abbr in sorted_abbrs:
            # We ensure we only match the abbreviation if it has a dot
            search_pattern = rf"\b{re.escape(abbr)}\."
            temp_text = re.sub(search_pattern, f"{abbr}{placeholder}", temp_text)

        # 3. Split at actual sentence endings
        # pattern: Dot/!/? followed by space and a Capital/Number
        split_pattern = r'(?<=[.!?])\s+(?=[A-Z0-9])'
        segments = re.split(split_pattern, temp_text)

        # 4. Restore the dots
        return [s.replace(placeholder, ".").strip() for s in segments if s.strip()]
