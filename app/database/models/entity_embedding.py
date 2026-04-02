import logging
from psycopg2.extras import Json, execute_values
from app.database.connection import DBConnection
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

class EntityEmbedding:
    """Model for handling vector-based entity knowledge."""

    @classmethod
    def save_batch(cls, rows: list):
        """
        Saves a batch of embeddings to the database with Upsert-Logic.
        Row: (entity_type, reference_key, content, metadata_json, embedding_list)
        """
        conn = DBConnection.get_connection()
        try:
            with conn.cursor() as cur:
                # Nutze ON CONFLICT, um doppelte Reise-Einträge zu vermeiden
                query = """
                    INSERT INTO entity_embeddings 
                    (entity_type, reference_key, content, metadata, embedding, created_at, updated_at)
                    VALUES %s
                    ON CONFLICT (entity_type, reference_key, content) 
                    DO UPDATE SET updated_at = NOW()
                """
                execute_values(cur, query, rows, template="(%s, %s, %s, %s, %s::vector, NOW(), NOW())")
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving embedding batch: {e}")
            if conn: conn.rollback()
            return False
        finally:
            if conn: conn.close()

    @classmethod
    def search_knowledge(cls, query_vector: list, limit: int = 5, min_score: float = 0.4, e_type: str = None):
        """
        Erweiterte Suche: Filtert optional nach entity_type (z.B. 'travel_log').
        """
        conn = DBConnection.get_connection()
        try:
            with conn.cursor() as cur:
                # Basis-Query
                sql_where = "WHERE (1 - (embedding <=> %s::vector)) > %s"
                params = [query_vector, query_vector, min_score]

                # Optionaler Typ-Filter
                if e_type:
                    sql_where += " AND entity_type = %s"
                    params.append(e_type)

                # Sortierung und Limit anhängen
                params.extend([query_vector, limit])

                query = f"""
                    SELECT 
                        content, metadata, entity_type, reference_key,
                        (1 - (embedding <=> %s::vector)) as score
                    FROM entity_embeddings
                    {sql_where}
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                """
                
                cur.execute(query, tuple(params))
                rows = cur.fetchall()
                
                return [{
                    "content": r[0],
                    "metadata": r[1],
                    "type": r[2],
                    "key": r[3],
                    "score": round(float(r[4]), 4)
                } for r in rows]
        except Exception as e:
            logger.error(f"Error during vector search: {e}")
            return []
        finally:
            conn.close()


    @classmethod
    def get_fmb_letters_with_places(cls):
        """Holt alle FMB-Briefe mit ihren Orten aus der DB."""
        query = """
            SELECT l.id, l.name as letter_name, p.name as place_name
            FROM letters l
            JOIN letter_corresp_places lcp ON l.id = lcp.letter_id
            JOIN places p ON lcp.place_id = p.id
            WHERE l.name LIKE 'fmb-%' and lcp.sender = true
        """
        conn = DBConnection.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query)
                return cur.fetchall()
        finally:
            conn.close()


