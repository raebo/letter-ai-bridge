import psycopg2
from psycopg2.extras import Json
import json

class ChunkIngester:
    def __init__(self, db_params):
        """
        db_params: dict mit host, database, user, password
        """
        self.conn = psycopg2.connect(**db_params)
        self.table_name = "letter_embeddings"

    def upload_chunks(self, chunks):
        """
        chunks: Liste von Dicts [{'content': '...', 'metadata': {...}, 'vector': [...]}]
        """
        if not chunks:
            print("Keine Chunks zum Hochladen gefunden.")
            return

        sql = f"""
            INSERT INTO {self.table_name} (content, metadata, embedding, created_at, updated_at)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """

        try:
            with self.conn.cursor() as cur:
                # Wir bereiten die Daten für das Batch-Verfahren vor
                data_list = [
                    (
                        c['content'], 
                        Json(c['metadata']), 
                        # pgvector erwartet das Format '[1.2, 3.4, ...]' als String
                        str(c['vector']) 
                    ) for c in chunks
                ]
                
                cur.executemany(sql, data_list)
                self.conn.commit()
                print(f"Erfolgreich {len(chunks)} Chunks in die Datenbank '{self.table_name}' geschrieben.")
        except Exception as e:
            self.conn.rollback()
            print(f"Fehler beim Datenbank-Upload: {e}")

    def close(self):
        self.conn.close()

# --- BEISPIEL FÜR DIE ANWENDUNG ---
if __name__ == "__main__":
    # Deine Docker-Zugangsdaten aus dem docker-compose File
    db_config = {
        "host": "localhost",
        "database": "letter_ai_dev", # Name aus deiner init.sql / rails config
        "user": "postgres",
        "password": "password",
        "port": 5432
    }

    # Test-Daten (Normalerweise kommen die aus deinem TEIChunker)
    test_chunks = [
        {
            "content": "Mendelssohn schrieb an seine Schwester.",
            "metadata": {"source": "letter_01.xml", "author": "Mendelssohn"},
            "vector": [0.12, -0.05, 0.44] + [0.0] * 381 # Simulierter 384er Vektor
        }
    ]

    ingester = ChunkIngester(db_config)
    ingester.upload_chunks(test_chunks)
    ingester.close()
