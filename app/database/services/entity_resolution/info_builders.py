from os import stat
from app.utils.string_cleaner import StringCleaner
from app.core.config import settings

class InfoBuilder:

    @classmethod
    def build(cls, prefix: str, data: dict) -> str:
        # Dictionary-based dispatch for speed and clarity
        dispatch = {
                "PSN": cls._build_person_info,
                "SGH": cls._build_sight_institution_info,
                "STM": cls._build_settlement_info,
                "NST": cls._build_sight_institution_info,
                "CRT": cls._build_creation_info,
                "PRC": cls._build_protag_creation_info
                }
        builder = dispatch.get(prefix)
        return builder(data) if builder else data.get('name', "")


    @staticmethod
    def _build_person_info(data: dict) -> str:
        last = StringCleaner.normalize_name(data.get('last_name'))
        first = StringCleaner.normalize_name(data.get('first_name'))

        # Cleanly join names to avoid leading/trailing/double spaces
        full_name = " ".join(filter(None, [first, last]))

        # 2. Handle Dates (Ensure we pass None or Int, not empty strings, to the formatter)
        birth = data.get('birth_year')
        death = data.get('death_year')
        date_info = InfoBuilder._format_life_dates(birth, death)

        aliases = StringCleaner._process_letter_name(data.get('letter_name', ""))
        alias_str = f" [aka: {aliases}]" if aliases else ""

        # Add marriage info to the prose
        married_to = data.get("married_to_name")
        marriage_str = f" verh. mit {married_to}" if married_to else ""

        bio_summary = StringCleaner.extract_bio_summary(data.get("notes", ""))

        parts = [f"{full_name} {date_info}", bio_summary + marriage_str, alias_str]

        return " ".join(filter(None, parts)).strip()


    @staticmethod
    def _build_sight_institution_info(data: dict) -> str:
        name = StringCleaner.normalize_name(data.get('name'))
        kind = StringCleaner.normalize_name(data.get('kind'))
        info = StringCleaner.normalize_name(data.get('info'))
        settlement = StringCleaner.normalize_name(data.get('settlement_name'))
        country_name = StringCleaner.normalize_name(data.get('country_name'))

        kind_part = f" ({kind})" if kind else ""
        info_part = f", {info}" if info else ""
        parts = [f"{name}{kind_part}", f"[{settlement}, {country_name}{info_part}]"]

        return " ".join(filter(None, parts)).strip()


    @staticmethod
    def _build_settlement_info(data: dict) -> str:
        name = StringCleaner.normalize_name(data.get('name'))
        info = StringCleaner.normalize_name(data.get('info'))
        country_name = StringCleaner.normalize_name(data.get('country_name'))

        info_part = f", {info}" if info else ""
        parts = [f"{name}", f"[{country_name}{info_part}]"]

        return " ".join(filter(None, parts)).strip()

    @staticmethod
    def _build_institution_info(data: dict) -> str:
        return "TEST"

    @staticmethod
    def _build_creation_info(data: dict) -> str:
        name = StringCleaner.normalize_name(data.get('name'))
        kind = StringCleaner.normalize_name(data.get('kind'))
        info = StringCleaner.normalize_name(data.get('info'))
        authors = data.get('authors', []) # This is your list of dicts/names

        # 1. Name and Kind
        kind_part = f" ({kind})" if kind else ""
        base_name = f"{name}{kind_part}"

        # 2. Author part (Natural language is better for AI)
        author_names = [f"{a['first_name']} {a['last_name']}".strip() for a in authors]
        author_part = f" von {', '.join(author_names)}" if author_names else ""

        # 3. Extra Info (The "Glimpsy" stuff in brackets)
        info_part = f"[{info}]" if info else ""

        parts = [f"{base_name}{author_part}", info_part]

        return " ".join(filter(None, parts)).strip()

    @staticmethod
    def _build_protag_creation_info(data: dict) -> str:
        cats = [c['name'] for c in data.get('categories', [])]
        path_prefix = f"[{' > '.join(cats)}] " if cats else ""
        
        # Identity: Name + Catalogs
        name = data.get('c_name')
        catalogs = filter(None, [
            f"MWV {data.get('c_mwv')}" if data.get('c_mwv') else None,
            f"op. {data.get('c_op')}" if data.get('c_op') else None
        ])
        cat_str = f" ({', '.join(catalogs)})" if catalogs else ""
        
        authors = settings.protag_name
            
        # Hierarchy
        parent = f" (Teil von: {data.get('p_name')})" if data.get('p_name') else ""
        
        return f"{path_prefix}{name}{cat_str} von {authors}{parent}".strip()


    @staticmethod
    def _format_life_dates(birth: int, death: int) -> str:
        """
        Formats dates based on availability:
        - Both: (1809–1847)
        - Birth only: (1809–??)
        - Death only: (??–1847)
        - Neither: ""
        """
        if not birth and not death:
            return ""

        b_str = str(birth) if birth else "??"
        d_str = str(death) if death else "??"

        return f" ({b_str}–{d_str})"
