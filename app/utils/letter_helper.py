import re
import sys

class LetterHelper:
    @staticmethod
    def extract_date_from_key(key: str) -> str:
        if 're' not in globals():
            return f"DEBUG: re missing. Path: {sys.path}"
        """
        Extracts YYYY-MM-DD from strings like 'fmb-1839-04-23-01'.
        Returns 'Unknown Date' if the pattern doesn't match.
        """
        # Regex looks for 4 digits, 2 digits, 2 digits separated by hyphens
        match = re.search(r'(\d{4})-(\d{2})-(\d{2})', key)
        if match:
            return match.group(0)
        return "Unknown Date"
