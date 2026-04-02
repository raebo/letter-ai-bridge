import sys
from pathlib import Path

# Fallback for Python < 3.11
if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

class Config:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            
            # Use Path(__file__) logic to find your pyproject.toml
            # Adjust the .parent count depending on where your config.py lives
            root_dir = Path(__file__).resolve().parent.parent.parent
            toml_path = root_dir / "pyproject.toml"
            
            try:
                with open(toml_path, "rb") as f:
                    full_config = tomllib.load(f)
                    # Access the nested tool.fmb_pipeline section
                    cls._instance.data = full_config.get("tool", {}).get("fmb_pipeline", {})
            except FileNotFoundError:
                print(f"Warning: pyproject.toml not found at {toml_path}")
                cls._instance.data = {}
                
        return cls._instance

    @property
    def protag_name(self):
        return self.data.get("tool.fmb_pipeline.protag_name", "Unbekannter Protagonist")

    @property
    def DEBUG(self):
        return self.data.get("debug", False)

    @property
    def truncate_embeddings_on_start(self):
        return self.data.get("truncate_embeddings_on_start", False)

    @property
    def log_to_file(self):
        return self.data.get("log_to_file", True)

    @property
    def db_params(self):
        return self.data.get("database", {})


    @property
    def api_protag_params(self):
        return self.data.get("api", {})

    @property
    def api_host(self):
        return self.api_protag_params.get("host")

    @property
    def api_token(self):
        return self.api_protag_params.get("auth_key")

# Global access point
settings = Config()
