from .info_builders import InfoBuilder
from .metadata_builders import MetadataBuilder
from app.database.models.letter import Letter
from app.database.models.person import Person
from app.database.models.sight import Sight
from app.database.models.settlement import Settlement
from app.database.models.institution import Institution
from app.database.models.creation import Creation
from app.database.models.protag_creation import ProtagCreation


class RetrieveInfosService:
    # Map prefixes to the actual Model classes
    _MODEL_MAP = {
        "PSN": Person,
        "SGH": Sight,
        "STM": Settlement,  
        "NST": Institution,
        "CRT": Creation,
        "PRC": ProtagCreation,
        "LET": Letter,
    }

    @classmethod
    def _get_model_for_prefix(cls, prefix: str):
        """
        Returns the appropriate Model class based on the prefix.
        Returns None if the prefix is unknown.
        """
        model = cls._MODEL_MAP.get(prefix)
        
        if not model:
            # Optional: Log a warning so you know you're missing a model
            print(f"Warning: No model found for prefix '{prefix}'")
            
        return model

    @classmethod
    def get_info(cls, prefix: str, key: str) -> dict:
        """The Database-dependent method."""
        model = cls._get_model_for_prefix(prefix)

        print(f"Fetching data for prefix '{prefix}' and key '{key}' using model '{model.__name__ if model else 'None'}'")
        data = model.entity_profile(key)
        print(f"Data fetched for key '{key}'")
        
        if not data:
            return {"info": "", "metadata": {}}

        # Delegate to the pure logic method
        return cls.assemble_entity_package(prefix, key, data)

    @classmethod
    def assemble_entity_package(cls, prefix: str, key: str, data: dict) -> dict:
        return {
            "info": InfoBuilder.build(prefix, data),
            "metadata": MetadataBuilder.build(prefix, data) | { "key": key }
        }
    
