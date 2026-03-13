import yaml
import os
from pathlib import Path

class Config:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            
            # Locate the config file relative to this file
            root_dir = Path(__file__).parent.parent.parent
            config_path = root_dir / "config" / "settings.yml"
            
            # Determine environment (default to development)
            env = os.getenv("APP_ENV", "development")
            
            with open(config_path, "r") as f:
                full_config = yaml.safe_load(f)
                cls._instance.data = full_config.get(env, {})
        return cls._instance

    @property
    def protag_name(self):
        return self.data.get("protag", {}).get("name", "Unknown Protag")

    @property
    def protag_key(self):
        return self.data.get("protag", {}).get("key", "Unknown Protag")

    @property
    def db_params(self):
        return self.data.get("database", {})

# Global access point
settings = Config()
