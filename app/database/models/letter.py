from ..connection import DBConnection
from psycopg2.extras import DictCursor, RealDictCursor
from app.utils.letter_helper import LetterHelper


import logging
logger = logging.getLogger(__name__)

class Letter:
    def __init__(self, record):
        self.id = record['id']
        self.xml_content = record['content']
        self.name = record['name']
        # Hier kannst du weitere Felder mappen, falls nötig


    @classmethod
    def get_batch_metadata(cls, letter_ids):
        if not letter_ids:
            return {}


        format_strings = ','.join(['%s'] * len(letter_ids))
        query = f"SELECT id, name FROM letters WHERE id IN ({format_strings})"
        
        conn = DBConnection.get_connection()
        try:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute(query, tuple(letter_ids))
                
                rows = cur.fetchall()
                
                return { row['id']: {"name": row['name']} for row in rows }
        finally:
            conn.close()


    @classmethod
    def find_by_name(cls, letter_name):
        conn = DBConnection.get_connection()
        try:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("SELECT id, name, content FROM letters WHERE name = %s", (letter_name,))
                record = cur.fetchone()
                if record:
                    return cls(record)
                else:
                    return None
        finally:
            conn.close()

    @classmethod
    def find_all_missing_embeddings(cls, batch_size=100):
        """
        Gibt alle Briefe zurück, die noch keinen Eintrag in der 
        Tabelle letter_embeddings haben.
        """
        conn = DBConnection.get_connection()
        try:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                # SQL Query: Finde Briefe, die NICHT in letter_embeddings existieren
                sql = """
                    SELECT l.id, l.name, l.content 
                    FROM letters l
                    LEFT JOIN letter_embeddings le ON l.id = le.letter_id
                    WHERE le.letter_id IS NULL 
                      AND l.content IS NOT NULL
                    ORDER BY l.name
                """
                cur.execute(sql)

                while True:
                    rows = cur.fetchmany(batch_size)
                    if not rows:
                        break
                    yield [cls(row) for row in rows]
        finally:
            conn.close()

    @classmethod
    def find_all_with_xml(cls, batch_size=100):
        """Generator, der Letter-Objekte in Batches zurückgibt."""
        conn = DBConnection.get_connection()
        try:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                # Wir holen nur die IDs und das XML
                #cur.execute("SELECT id, name, content FROM letters WHERE content IS NOT NULL order by name limit 100")
                cur.execute("SELECT id, name, content FROM letters WHERE content IS NOT NULL order by name")

                while True:
                    rows = cur.fetchmany(batch_size)
                    if not rows:
                        break
                    yield [cls(row) for row in rows]
        finally:
            conn.close()


    @classmethod
    def entity_profile(cls, key: str) -> dict:
        conn = DBConnection.get_connection()
        try:
            logger.debug(f"Fetching entity profile for letter with key: {key}")
            with conn.cursor(cursor_factory=DictCursor) as cur:
                sql = """
                SELECT 
                    l.id, 
                    l.name,
                    l.state,
                    -- Authors subquery: Coalesce handles missing names/keys to avoid NULL results
                    (SELECT array_agg(
                        TRIM(COALESCE(p.first_name, '') || ' ' || COALESCE(p.last_name, '')) || 
                        ' (' || COALESCE(p.key, 'no-key') || ')'
                     )
                     FROM people p 
                     JOIN letter_corresps lc ON p.id = lc.person_id 
                     WHERE lc.letter_id = l.id AND lc.sender = TRUE) as authors,

                    -- Receivers subquery
                    (SELECT array_agg(
                        TRIM(COALESCE(p.first_name, '') || ' ' || COALESCE(p.last_name, '')) || 
                        ' (' || COALESCE(p.key, 'no-key') || ')'
                     )
                     FROM people p 
                     JOIN letter_corresps lc ON p.id = lc.person_id 
                     WHERE lc.letter_id = l.id AND lc.sender = FALSE) as receivers,

                    -- Sending places subquery
                    (SELECT array_agg(
                        COALESCE(pl.name, 'Unknown Place') || ' (' || COALESCE(pl.key, 'no-key') || ')'
                     ) 
                     FROM places pl JOIN letter_corresp_places lcp ON pl.id = lcp.place_id 
                     WHERE lcp.letter_id = l.id AND lcp.sender = TRUE) as send_places,

                    -- Receiving places subquery 
                    (SELECT array_agg(
                        COALESCE(pl.name, 'Unknown Place') || ' (' || COALESCE(pl.key, 'no-key') || ')'
                     ) 
                     FROM places pl JOIN letter_corresp_places lcp ON pl.id = lcp.place_id 
                     WHERE lcp.letter_id = l.id AND lcp.sender = FALSE) as recv_places 
                FROM letters l
                WHERE l.name = %s
                """
                cur.execute(sql, (key,))


                record = cur.fetchone()

                if not record:
                    return {}

                date_str = LetterHelper.extract_date_from_key(key)
                author_list = record['authors'] or []
                receiver_list = record['receivers'] or []
                s_place_list = record['send_places'] or []
                r_place_list = record['recv_places'] or []

                auth_str = "; ".join(author_list) if author_list else "Unknown Author"

                rec_str = "; ".join(receiver_list) if receiver_list else "Unknown Receiver"
                s_place_str = f" in {'; '.join(s_place_list)}" if s_place_list else ""
                r_place_str = f" to {'; '.join(r_place_list)}" if r_place_list else ""


                auth_str = "; ".join(author_list) if author_list else "Unknown Author"
                rec_str = "; ".join(receiver_list) if receiver_list else "Unknown Receiver"

                s_place_str = f" in {'; '.join(s_place_list)}" if s_place_list else ""
                r_place_str = f" to {'; '.join(r_place_list)}" if r_place_list else ""

                return {
                    "info": f"Letter from {auth_str}{s_place_str} to {rec_str}{r_place_str} [{date_str}]",
                    "metadata": {
                        "entity_key": key,
                        "entity_type": "letter",
                        "date": date_str,
                        "authors": author_list,
                        "receivers": receiver_list,
                        "sending_places": s_place_list,
                        "receiving_places": r_place_list,
                        "db_id": record.get('id'),
                        "status": record.get('state')
                    }
                }

        except Exception as e:
            logger.error(f"Error getting letter info: {e}")
            raise RuntimeError("Failed to get letter entity_profile") from e
        finally:
            conn.close()


    @classmethod
    def get_raw_letters_batched(cls, batch_size: int = 100):
        conn = DBConnection.get_connection()
        try:
            # Wir nutzen den RealDictCursor auch für den Named Cursor
            with conn.cursor(name='fetch_letters_for_summary', cursor_factory=RealDictCursor) as cur:
                query = "SELECT id, name, default_text_content FROM letters"
                cur.execute(query)
                
                while True:
                    rows = cur.fetchmany(batch_size)
                    if not rows:
                        break
                    
                    yield [
                        {
                            "id": r['id'],
                            "name": r['name'],
                            "content": r['default_text_content']
                        } for r in rows
                    ]
        except Exception as e:
            logger.error(f"Fehler beim Batched-Laden der Briefe: {e}")
            # Wichtig: raise hier, damit du im Orchestrator den echten Fehler siehst
            raise 
        finally:
            conn.close()

    @classmethod
    def get_full_text_by_id(cls, letter_id: int):
        conn = DBConnection.get_connection()
        try:
            with conn.cursor() as cur:
                # Greift auf deine Haupttabelle 'letters' zu
                cur.execute("SELECT default_text_content FROM letters WHERE id = %s", (letter_id,))
                row = cur.fetchone()
                return row[0] if row else None
        finally:
            conn.close()
