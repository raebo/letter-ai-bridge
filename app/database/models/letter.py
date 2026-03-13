from ..connection import DBConnection
from psycopg2.extras import DictCursor
from app.utils.letter_helper import LetterHelper

class Letter:
    def __init__(self, record):
        self.id = record['id']
        self.xml_content = record['content']
        self.name = record['name']
        # Hier kannst du weitere Felder mappen, falls nötig

    @classmethod
    def find_all_with_xml(cls, batch_size=100):
        """Generator, der Letter-Objekte in Batches zurückgibt."""
        conn = DBConnection.get_connection()
        try:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                # Wir holen nur die IDs und das XML
                cur.execute("SELECT id, name, content FROM letters WHERE content IS NOT NULL order by name limit 100")

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
            with conn.cursor(cursor_factory=DictCursor) as cur:
                sql = """
                    SELECT 
                        l.id, 
                        l.name,
                        -- Authors subquery
                        (SELECT array_agg(p.first_name || ' ' || p.last_name || ' (' || p.key || ')')
                         FROM people p 
                         JOIN letter_corresps lc ON p.id = lc.person_id 
                         WHERE lc.letter_id = l.id AND lc.sender = TRUE) as authors,
                        -- Receivers subquery
                        (SELECT array_agg(p.first_name || ' ' || p.last_name || ' (' || p.key || ')')
                         FROM people p 
                         JOIN letter_corresps lc ON p.id = lc.person_id 
                         WHERE lc.letter_id = l.id AND lc.sender = FALSE) as receivers,
                        -- Sending places subquery
                        (SELECT array_agg(pl.name || ' (' || pl.key || ')') 
                         FROM places pl JOIN letter_corresp_places lcp ON pl.id = lcp.place_id 
                         WHERE lcp.letter_id = l.id AND lcp.sender = TRUE) as send_places,
                        -- Receiving places subquery 
                        (SELECT array_agg(pl.name || ' (' || pl.key || ')') 
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

                # 2. Create the string for the AI 'info' field
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
                            "db_id": record['id']
                            }
                        }
        finally:
            conn.close()
