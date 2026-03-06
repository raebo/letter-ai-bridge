from ..connection import DBConnection
from psycopg2.extras import DictCursor

class LetterEmbedding:
    _table_name = "letter_embeddings" # Defined as class variable for @classmethod access

    @classmethod
    def truncate_table(cls):
        """
        DANGER: Deletes all rows from the letter_embeddings table.
        Useful for resetting the index during testing or full re-indexing.
        """
        conn = DBConnection.get_connection()
        try:
            with conn.cursor() as cur:
                # Using f-string for table name as it is internal/static
                cur.execute(f"TRUNCATE TABLE {cls._table_name} RESTART IDENTITY CASCADE;")
                conn.commit()
                print(f"--- Table {cls._table_name} truncated ---")
        finally:
            conn.close()

    @classmethod
    def count(cls):
        """Returns the total number of embeddings in the database."""
        conn = DBConnection.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(f"SELECT COUNT(*) FROM {cls._table_name};")
                return cur.fetchone()[0]
        finally:
            conn.close()
