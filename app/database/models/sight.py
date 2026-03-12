from app.database.connection import DBConnection

class Sight:
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
                query = """
                    SELECT 
                        s.name, 
                        s.kind,
                        s.notes,
                        p.name, 
                        c.name,
                        s.updated_at,
                        s.info
                    FROM places s
                    LEFT JOIN places p ON s.parent_id = p.id
                    LEFT JOIN countries c ON p.country_id = c.id
                    WHERE s.key = %s AND s.type = 'Sight'
                    LIMIT 1
                """
                cur.execute(query, (key,))
                row = cur.fetchone()

                if row:
                    return {
                        "name": row[0],
                        "kind": row[1],
                        "notes": row[2],
                        "settlement_name": row[3],
                        "country_name": row[4],
                        "last_updated_at": row[5],
                        "info": row[6],
                    }
                return {} 
        except Exception as e:
            print(f"Error fetching place with key {key}: {e}")
            return {}
        finally:
            conn.close()
