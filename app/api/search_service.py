from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import psycopg2
from psycopg2.extras import RealDictCursor
import yaml

app = FastAPI(title="Mendelssohn AI Search API")

# 1. Modell beim Start laden (RTX 3080)
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2', device="cuda")

def load_db_config():
    with open("config/settings.yml", "r") as f:
        return yaml.safe_load(f)["development"]["database"]

class QueryRequest(BaseModel):
    query: str
    limit: int = 5

@app.post("/search")
async def search_letters(request: QueryRequest):
    try:
        # A. Frage vektorisieren
        query_vector = model.encode(request.query).tolist()

        # B. Vektor-Suche in Postgres
        db_params = load_db_config()
        conn = psycopg2.connect(**db_params, cursor_factory=RealDictCursor)
        
        with conn.cursor() as cur:
            # Wir nutzen den Cosine Distance Operator <=> von pgvector
            search_sql = """
                SELECT content, metadata, (embedding <=> %s) as distance
                FROM letter_embeddings
                ORDER BY distance ASC
                LIMIT %s;
            """
            cur.execute(search_sql, (str(query_vector), request.limit))
            results = cur.fetchall()
        
        conn.close()
        return {"results": results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
