from app.database.connection import DBConnection

class Settlement:
    """Model for handling Place-Sight-related database operations"""

    @classmethod
    def entity_profile(cls, key: str) -> dict:
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
                    SELECT 
                        p.name, 
                        p.info, 
                        p.notes,
                        p.updated_at,
                        c.name
                    FROM places p
                    LEFT JOIN countries c ON p.country_id = c.id
                    WHERE key = %s AND type = 'Settlement'
                    LIMIT 1
                """
                cur.execute(query, (key,))
                row = cur.fetchone()

                if row:
                    return {
                        "name": row[0],
                        "info": row[1],
                        "notes": row[2],
                        "last_updated_at": row[3],
                        "country_name": row[4]
                    }
                return {} 
        except Exception as e:
            print(f"Error fetching place with key {key}: {e}")
            return {}
        finally:
            conn.close()
