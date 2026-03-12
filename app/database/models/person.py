from app.database.connection import DBConnection

class Person:
    """Model for handling Person-related database operations."""

    @classmethod
    def entity_profile(cls, key: str) -> dict:
        """
        Fetches person data from the database by its unique key.
        Returns a dictionary of columns or None if not found.
        """
        conn = DBConnection.get_connection()
        try:
            with conn.cursor() as cur:
                query = """
                    SELECT 
                        first_name, 
                        last_name, 
                        index_name, 
                        letter_name, 
                        birth_year, 
                        death_year,
                        updated_at,
                        married_to,
                        background,
                        description,
                        source,
                        relation
                    FROM people
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
                        "death_year": row[5],
                        "last_updated_at": row[6],
                        "married_to_name": row[7],
                        "background": row[8],
                        "description": row[9],
                        "source": row[10],
                        "relation": row[11],
                    }
                return {} 
        except Exception as e:
            print(f"Error fetching person with key {key}: {e}")
            return {}
        finally:
            conn.close()
