import ollama
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import psycopg2
from psycopg2.extras import RealDictCursor
import yaml


from app.core.config import settings

app = FastAPI()
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2', device="cuda")

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat_with_mendelssohn(request: ChatRequest):
    # 1. Semantic Search
    query_vector = model.encode(request.message).tolist()

    # 2. Use the settings object we set up earlier
    # settings.db_params is already the dict: {'host': '...', 'user': '...', etc.}
    try:
        conn = psycopg2.connect(**settings.db_params, cursor_factory=RealDictCursor)
        with conn.cursor() as cur:
            cur.execute("""
                SELECT content FROM letter_embeddings 
                ORDER BY embedding <=> %s LIMIT 3
            """, (str(query_vector),))
            context_chunks = cur.fetchall()
    except Exception as e:
        logger.error(f"Database connection failed during chat: {e}")
        raise HTTPException(status_code=500, detail="Database connection error")
    finally:
        if 'conn' in locals():
            conn.close()

    # 2. Kontext für das LLM zusammenbauen
    context_text = "\n---\n".join([c['content'] for c in context_chunks])
    
    # 3. Der "System Prompt" (Gibt der KI ihre Identität)
    prompt = f"""
    Du bist ein hilfreicher Assistent für das Mendelssohn-Briefarchiv. 
    Beantworte die Frage des Nutzers NUR basierend auf dem folgenden Kontext aus Originalbriefen.
    Wenn der Kontext die Antwort nicht hergibt, sage das höflich.

    KONTEXT:
    {context_text}

    FRAGE:
    {request.message}
    """

    # 4. Abfrage an das lokale LLM (Ollama nutzt deine RTX 3080)
    response = ollama.chat(model='llama3', messages=[
        {'role': 'user', 'content': prompt},
    ])

    return {
        "answer": response['message']['content'],
        "sources": [c['content'][:100] + "..." for c in context_chunks] # Quellen-Vorschau
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
