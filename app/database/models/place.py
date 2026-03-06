from app.database.connection import DBConnection

class Place:
    """Model for handling Place-related database operations (Settlements, Countries, Sights)."""

    @classmethod
    def find_by_key(cls, key: str) -> dict:
        """
        Fetches place data from the database by its unique key.
        Returns a dictionary of columns or None if not found.
        """
        # Using a context manager for the connection to ensure it closes properly
        conn = DBConnection.get_connection()
        try:
            with conn.cursor() as cur:
                # We select exactly the columns the Service needs for _build_info_string
                # Adjust 'name' and 'country_name' to your actual column names
                query = """
                    SELECT name, country_name 
                    FROM places 
                    WHERE key = %s 
                    LIMIT 1
                """
                cur.execute(query, (key,))
                row = cur.fetchone()

                if row:
                    return {
                        "name": row[0],
                        "country": row[1]
                    }
                return {} 
        except Exception as e:
            print(f"Error fetching place with key {key}: {e}")
            return {}
        finally:
            conn.close()
