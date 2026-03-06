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
            raise Exception("DB-Konfiguration wurde noch nicht gesetzt!")
        return psycopg2.connect(**cls._params)
