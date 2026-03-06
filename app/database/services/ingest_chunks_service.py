import psycopg2
from ..connection import DBConnection
from psycopg2.extras import Json
import json

class IngestChunksService:
    def __init__(self):
        self.conn = DBConnection.get_connection()
        self.table_name = "letter_embeddings"

    def upload_chunks(self, chunks):
        """
        chunks: Liste von Dicts [{'content': '...', 'metadata': {...}, 'vector': [...]}]
        """
        if not chunks:
            print("Keine Chunks zum Hochladen gefunden.")
            return

        sql = f"""
            INSERT INTO {self.table_name} (letter_id, content, metadata, embedding, created_at, updated_at)
            VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """

        try:  
            with self.conn.cursor() as cur:
                # Prepare data for bulk insert
                data_list = [
                        (
                            c['letter_id'],
                            c['content'], 
                            Json(c['metadata']), 
                            # pgvector expecting the forma '[1.2, 3.4, ...]' as string
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
