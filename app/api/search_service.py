from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from psycopg2.extras import RealDictCursor

from app.database.connection import DBConnection

app = FastAPI(title="Mendelssohn AI Search API")

# 1. Modell beim Start laden (RTX 3080)
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2', device="cuda")

class QueryRequest(BaseModel):
    query: str
    limit: int = 5

@app.post("/search")
def search_letters(request: QueryRequest):
    # Plain (sync) endpoint: FastAPI runs it in a threadpool, so the blocking
    # model inference and DB call below don't stall the event loop.
    try:
        # A. Frage vektorisieren
        query_vector = model.encode(request.query).tolist()

        # B. Vektor-Suche in Postgres
        conn = DBConnection.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Wir nutzen den Cosine Distance Operator <=> von pgvector
                search_sql = """
                    SELECT content, metadata, (embedding <=> %s) as distance
                    FROM letter_embeddings
                    ORDER BY distance ASC
                    LIMIT %s;
                """
                cur.execute(search_sql, (str(query_vector), request.limit))
                results = cur.fetchall()
        finally:
            conn.close()

        return {"results": results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
