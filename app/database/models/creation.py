from app.database.connection import DBConnection

class Creation:
    """Model for handling Creation -related database operations"""

    @classmethod
    def entity_profile(cls, key: str) -> dict:
        conn = DBConnection.get_connection()
        try:
            with conn.cursor() as cur:
                # Query 1: Fetch the Creation record
                query = """
                    SELECT 
                        cr.id, 
                        cr.name, 
                        cr.kind, 
                        cr.info, 
                        cr.notes, 
                        cr.updated_at
                    FROM creations cr
                    WHERE cr.key = %s 
                    LIMIT 1
                """
                cur.execute(query, (key,))
                row = cur.fetchone()

                if not row:
                    return {}

                creation_id = row[0]
                data = {
                    "name": row[1],
                    "kind": row[2],
                    "info": row[3],
                    "notes": row[4],
                    "last_updated_at": row[5],
                    "authors": [] 
                }

                # Query 2: Fetch specific columns for all associated People
                author_query = """
                    SELECT 
                        p.last_name, 
                        p.first_name, 
                        p.birth_year, 
                        p.death_year, 
                        p.key
                    FROM people p
                    JOIN creation_authors ca ON p.id = ca.person_id
                    WHERE ca.creation_id = %s
                """
                cur.execute(author_query, (creation_id,))
                author_rows = cur.fetchall()

                # Map each author to a structured dictionary
                for r in author_rows:
                    data["authors"].append({
                        "last_name": r[0],
                        "first_name": r[1],
                        "birth_year": r[2],
                        "death_year": r[3],
                        "key": r[4],
                    })

                return data

        except Exception as e:
            print(f"Error fetching creation with key {key}: {e}")
            return {}
        finally:
            conn.close()
