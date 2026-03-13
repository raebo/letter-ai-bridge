import psycopg2
from psycopg2.extras import DictCursor

class DBConnection:
    _params = None

    @classmethod
    def set_config(cls, db_params):
        cls._params = db_params

    @classmethod
    def get_connection(cls):
        if not cls._params:
            # Instead of just raising an error, we could try to 
            # auto-initialize from settings if not already set.
            from app.core.config import settings
            cls.set_config(settings.db_params)
            
        return psycopg2.connect(**cls._params)
