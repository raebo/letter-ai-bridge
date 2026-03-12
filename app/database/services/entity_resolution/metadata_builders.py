
class MetadataBuilder:
    @classmethod
    def build(cls, prefix: str, data: dict) -> dict:
        dispatch = {
            "PSN": cls._build_person_meta,
            "SGH": cls._build_place_meta,
            "NST": cls._build_place_meta,
            "STM": cls._build_place_meta,
            "CRT": cls._build_creation_meta,
        }
        builder = dispatch.get(prefix)
        return builder(data) if builder else data.get('metadata', {})

    @classmethod
    def _build_person_meta(cls, data: dict) -> dict:
        # print the data dict
        # print("Person data for metadata:", data.get("source"))

        return {
                "last_updated": cls._serialize_value(data.get('last_updated_at')),
                "background": data.get('background'),
                "description": data.get('description'),
                "source": data.get('source'),
                "relation": data.get('relation'),
            }

    @classmethod
    def _build_place_meta(cls, data: dict) -> dict:
        # print("Sight data for metadata:", data)

        return {
            "last_updated": cls._serialize_value(data.get('last_updated_at')),
            "notes": data.get('info'),
            }

    @classmethod
    def _build_creation_meta(cls, data: dict) -> dict:
        return {
            "last_updated": cls._serialize_value(data.get('last_updated_at')),
            "notes": data.get('notes'),
            "authors": data.get('authors'),
        }    


    @classmethod
    def _serialize_value(cls, val):
        """
        Private helper to ensure database objects (like datetime) 
        are JSON serializable.
        """
        if val is None:
            return None
            
        # Handle datetime / date objects
        if hasattr(val, 'isoformat'):
            return val.isoformat()
            
        # Fallback for anything else unusual
        return str(val) if not isinstance(val, (str, int, float, bool, dict, list)) else val

