from app.utils.string_cleaner import StringCleaner
from app.utils.letter_helper import LetterHelper

import logging
logger = logging.getLogger(__name__)

class MetadataBuilder:
    @classmethod
    def build(cls, prefix: str, data: dict) -> dict:
        dispatch = {
            "PSN": cls._build_person_meta,
            "SGH": cls._build_place_meta,
            "NST": cls._build_place_meta,
            "STM": cls._build_place_meta,
            "CRT": cls._build_creation_meta,
            "PRC": cls._build_protag_creation_meta,
            "LET": cls._build_letter_meta,
        }
        builder = dispatch.get(prefix)
        return builder(data) if builder else data.get('metadata', {})

    @classmethod
    def _build_letter_meta(cls, data: dict) -> dict:
        """
        Constructs a structured metadata dictionary for a letter.
        Mirroring the logic of _build_person_meta.
        """
        try:
            return {
                "entity_key": data.get('entity_key'),
                "entity_type": "letter",
                "date": LetterHelper.extract_date_from_key(data.get('entity_key', '')) or "Undated",
                "authors": data.get('authors') or [],
                "receivers": data.get('receivers') or [],
                "sending_places": data.get('send_places') or [],
                "receiving_places": data.get('recv_places') or [],
                "db_id": data.get('id'),
                "last_updated": cls._serialize_value(data.get('updated_at')),
                "is_draft": data.get('status') == 'draft',
                "source_repository": data.get('repository') or "Unknown"
            }
        except Exception as e:
            logger.error(f"Error building letter metadata for key {data.get('entity_key')}: {e}")
            raise RuntimeError(f"Failed to build letter metadata for key {data.get('entity_key')}") from e


    @classmethod
    def _build_person_meta(cls, data: dict) -> dict:
        # print the data dict
        # print("Person data for metadata:", data.get("source"))

        return {
                "last_updated": cls._serialize_value(data.get('last_updated_at')),
                "background": StringCleaner.normalize_name(data.get('background')),
                "description": StringCleaner.normalize_name(data.get('description')),
                "source": data.get('source'),
                "relation": data.get('relation'),
            }

    @classmethod
    def _build_place_meta(cls, data: dict) -> dict:
        # print("Sight data for metadata:", data)

        return {
            "last_updated": cls._serialize_value(data.get('last_updated_at')),
            "notes": StringCleaner.normalize_name(data.get('info')),
            }

    @classmethod
    def _build_creation_meta(cls, data: dict) -> dict:
        return {
            "last_updated": cls._serialize_value(data.get('last_updated_at')),
            "notes": StringCleaner.normalize_name(data.get('notes')),
            "authors": data.get('authors'),
        }    

    @classmethod
    def _build_protag_creation_meta(cls, data: dict) -> dict:
        return {
                "key": data.get('c_key'),
                "parent_key": data.get('p_key'),
                "type": "protag_creation",
                "category_path": [cat['name'] for cat in data.get('categories', [])],
                "catalog": {
                    "mwv": data.get('c_mwv'),
                    "opus": data.get('c_op')
                    },
                "parent_context": {
                    "name": StringCleaner.normalize_name(data.get('p_name')),
                    "mwv": data.get('p_mwv'),
                    "opus": data.get('p_op')
                    } if data.get('p_key') else None,
                "last_updated": cls._serialize_value(data.get('c_last_updated_at')),
                "notes": StringCleaner.normalize_name(data.get('c_notes')),
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

