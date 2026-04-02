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

    @classmethod
    def search_letters(cls, query_vector: list, limit: int = 3):
        conn = DBConnection.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT content FROM letter_embeddings 
                    ORDER BY embedding <=> %s::vector LIMIT %s
                """, (query_vector, limit))
                rows = cur.fetchall()
                return [{"content": r[0]} for r in rows]
        except Exception as e:
            logger.error(f"Error searching letters: {e}")
            return []
        finally:
            conn.close()

    @classmethod
    def search_by_type(cls, query_vector: list, e_type: str = 'summary', limit: int = 3, min_score: float = 0.35):
        """
        Sucht Vektoren basierend auf einem spezifischen Typ (z.B. 'summary' oder 'annotation').
        Nutzt den Kosinus-Ähnlichkeits-Operator (<=> für Distanz, daher 1 - distanz = score).
        """
        conn = DBConnection.get_connection()
        try:
            # Wir nutzen RealDictCursor, damit der ChatController direkt mit Keys arbeiten kann
            from psycopg2.extras import RealDictCursor
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = """
                    SELECT 
                        letter_id, 
                        content, 
                        (1 - (embedding <=> %s::vector)) as score
                    FROM letter_embeddings
                    WHERE embedding_type = %s
                      AND (1 - (embedding <=> %s::vector)) > %s
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                """
                # Parameter-Reihenfolge: vector, type, vector, min_score, vector, limit
                cur.execute(query, (query_vector, e_type, query_vector, min_score, query_vector, limit))
                return cur.fetchall()
        except Exception as e:
            logger.error(f"Fehler bei search_by_type ({e_type}): {e}")
            return []
        finally:
            conn.close()
            

    @classmethod
    def upsert_summary(cls, letter_id: int, summary_text: str, vector: list):
        """
        Speichert oder aktualisiert die Zusammenfassung basierend auf der letter_id.
        """
        conn = DBConnection.get_connection()
        try:
            with conn.cursor() as cur:
                # WICHTIG: Die Reihenfolge der Parameter muss exakt zum SQL passen
                # letter_id muss ein Integer sein (bigint)
                params = (
                    int(letter_id), # letter_id
                    summary_text,   # content
                    vector,         # embedding -> wird zu ::vector(384)
                    'summary'       # embedding_type
                )

                query = """
                    INSERT INTO letter_embeddings 
                    (letter_id, content, embedding, embedding_type, created_at, updated_at, metadata)
                    VALUES (%s, %s, %s::vector, %s, NOW(), NOW(), '{}'::jsonb)
                    ON CONFLICT (letter_id) WHERE (embedding_type = 'summary')
                    DO UPDATE SET 
                        content = EXCLUDED.content,
                        embedding = EXCLUDED.embedding,
                        updated_at = NOW();
                """
                
                cur.execute(query, params)
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Datenbankfehler beim Upsert für Letter ID {letter_id}: {e}")
            conn.rollback()
            raise e 
        finally:
            conn.close()
