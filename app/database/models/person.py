from app.database.connection import DBConnection

class Person:
    """Model for handling Person-related database operations."""

    @classmethod
    def find_by_key(cls, key: str) -> dict:
        """
        Fetches person data from the database by its unique key.
        Returns a dictionary of columns or None if not found.
        """
        # Using a context manager for the connection to ensure it closes properly
        conn = DBConnection.get_connection()
        try:
            with conn.cursor() as cur:
                # We select exactly the columns the Service needs for _build_info_string
                # Adjust 'name' and 'dates' to your actual column names
                query = """
                    SELECT first_name, last_name, index_name, letter_name, birth_year, death_year
                    FROM persons 
                    WHERE key = %s 
                    LIMIT 1
                """
                cur.execute(query, (key,))
                row = cur.fetchone()

                if row:
                    return {
                        "first_name": row[0],
                        "last_name": row[1],
                        "index_name": row[2],
                        "letter_name": row[3],
                        "birth_year": row[4],
                        "death_year": row[5],
                    }
                return {} 
        except Exception as e:
            print(f"Error fetching person with key {key}: {e}")
            return {}
        finally:
            conn.close()
