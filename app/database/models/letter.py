from ..connection import DBConnection
from psycopg2.extras import DictCursor

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
