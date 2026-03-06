import app.utils.string_cleaner as StringCleaner

class RetrieveEntityInfosService:
    # 1. Define the mapping of prefixes to Model classes
    _model_mapping = {
        "PSN": Person,
        "SGH": Sight,
        "CRT": Creation,
    }

    @classmethod
    def call(cls, key: str) -> str:
        """
        Main entry point: Extracts prefix, fetches the model, 
        and returns a formatted string for the embedding.
        """
        if not key or len(key) < 3:
            return ""

        # Extract the first three characters (e.g., "PSN")
        prefix = key[:3].upper()
        
        # Get the corresponding model class
        model_class = cls._model_mapping.get(prefix)
        
        if not model_class:
            return ""

        # Fetch the database object/data
        # We assume every model has a standardized 'find_by_key' method
        entity_data = model_class.find_by_key(key)
        
        if not entity_data:
            return ""

        # Build and return the formatted string
        return cls._build_info_string(prefix, entity_data)

    @classmethod
    def _build_info_string(cls, prefix: str, data: dict) -> str:
        """
        Builds the meta-information string based on the entity type.
        You can customize the format for each prefix here.
        """

        if not data: 
            return ""

        if prefix == "PSN":
            last = StringCleaner.normalize_name(data.get('last_name'))
            first = StringCleaner.normalize_name(data.get('first_name'))

            # Cleanly join names to avoid leading/trailing/double spaces
            full_name = " ".join(filter(None, [first, last])

            # 2. Handle Dates (Ensure we pass None or Int, not empty strings, to the formatter)
            birth = data.get('birth_year')
            death = data.get('death_year')
            date_info = cls._format_life_dates(birth, death)

            aliases = StringCleaner._process_letter_name(data.get('letter_name', ""))
            alias_str = f" [aka: {aliases}]" if aliases else ""

            return f"{full_name}{date_info}{alias_str}".strip()
       
        
        if prefix in ["PLC", "SET", "CNT"]:
            # Example: "Leipzig, Germany"
            return f"{data.get('name')}, {data.get('country')}"
        
        if prefix == "WRK":
            # Example: "Die Hochzeit des Camacho [MWV L 5]"
            return f"{data.get('title')} [MWV {data.get('mwv_no')}]"
            
        if prefix == "SGH":
            # Example: "Brandenburger Tor (Berlin)"
            return f"{data.get('name')} ({data.get('location')})"

        # Default fallback: just the name
        return data.get('name', "")


    @classmethod
    def _format_life_dates(cls, birth: int, death: int) -> str:
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
