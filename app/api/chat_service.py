import re
import ollama
import logging
from fastapi import FastAPI, HTTPException
from sentence_transformers import SentenceTransformer
from pydantic import BaseModel

from app.database.models.letter import Letter
from app.database.models.letter_embedding import LetterEmbedding
from app.database.models.entity_embedding import EntityEmbedding
from app.api.logic.information_retriever import InformationRetriever

logger = logging.getLogger(__name__)
app = FastAPI(title="Mendelssohn AI Search API")

# Initialisierung des Embedding-Modells auf der GPU (RTX 3080)
# Dies geschieht einmalig beim Start des Servers
embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2', device="cuda")

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat_with_mendelssohn(request: ChatRequest):
    try:
        # 1. Schritt: User-Frage vektorisieren
        # Das Embedding-Model sollte als Klassen-Attribut oder global verfügbar sein
        query_vector = embedding_model.encode(request.message).tolist()
        
        # Initialisierung der Container
        location_facts = []
        bio_facts = []
        summaries = []
        letter_context_blocks = []
        source_keys = []
        system_instruction = "Du bist ein historischer Experte für Felix Mendelssohn Bartholdy. Beantworte die Frage basierend auf den bereitgestellten Kontextinformationen."

        # --- 2. Schritt: DATEN-RETRIVAL (Multimodal) ---
        
        try:
            # A) Ortssuche via InformationRetriever (Re-Ranking & Boosting)
            location_facts = InformationRetriever.get_relevant_locations(
                query_text=request.message,
                query_vector=query_vector,
                limit=60,
                top_n=5
            )
            
            # B) Biografische Fakten (Allgemeines Wissen aus 'biography')
            # Hier nutzen wir das normale Model direkt
            bio_facts = EntityEmbedding.search_knowledge(
                query_vector, 
                e_type='biography', 
                limit=3, 
                min_score=0.35
            )
            
            # C) Brief-Zusammenfassungen für den Volltext-Zugriff
            summaries = LetterEmbedding.search_by_type(
                query_vector, 
                e_type='summary', 
                limit=2
            )
            
        except Exception as e:
            logger.error(f"Fehler beim Retrieval der Daten: {e}")

        # --- 3. Schritt: KONTEXT-AUFBEREITUNG ---

        # Orts-Kontext formatieren
        if location_facts:
            location_context = "\n".join([f"  * {loc['content']}" for loc in location_facts])
        else:
            location_context = "  * Keine spezifischen Aufenthaltsorte in den Reisedaten gefunden."

        # Biografischer Kontext formatieren
        if bio_facts:
            fact_context = "\n".join([f"  - {f['content']}" for f in bio_facts])
        else:
            fact_context = "  - Keine ergänzenden biografischen Fakten gefunden."

        all_letter_ids = [s.get('letter_id') for s in summaries if s.get('letter_id')]
        letter_metadata_map = {}
        if all_letter_ids:
            # 2. Schritt: Alle Metadaten in EINER Abfrage holen
            letter_metadata_map = Letter.get_batch_metadata(all_letter_ids)

        # Brief-Volltexte laden
        for s in summaries:
            l_id = s.get('letter_id')
            # Methode holt den Text direkt aus der DB-Tabelle 'letters'
            full_text = Letter.get_full_text_by_id(l_id) 
            
            if full_text:
                # Wir begrenzen den Text auf ca. 2500 Zeichen pro Brief für das Kontext-Fenster
                block = (
                    f"--- BRIEF (ID: {l_id}) ---\n"
                    f"Inhaltliche Zusammenfassung: {s['content']}\n"
                    f"Originaltext: {full_text[:2500]}..."
                )
                letter_context_blocks.append(block)
                source_keys.append(l_id)

        letter_context_str = "\n\n".join(letter_context_blocks) if letter_context_blocks else "Keine Brieftexte im Original verfügbar."

        # --- 4. Schritt: PROMPT-CONSTRUCTION ---

        system_prompt = f"""
        Du bist ein historischer Experte für den Komponisten Felix Mendelssohn Bartholdy. 
        Deine Aufgabe ist es, die Frage des Nutzers präzise und ausschließlich auf Basis der unten genannten Quellen zu beantworten.
        Antworte höflich und im Stil eines Historikers.

        ### GEOGRAFISCHE DATEN (Wo hielt er sich auf?):
        {location_context}

        ### BIOGRAFISCHE FAKTEN:
        {fact_context}

        ### RELEVANTE BRIEF-QUELLEN (O-Ton):
        {letter_context_str}

        FRAGE: {request.message}
        
        WICHTIG: Beziehe dich in deiner Antwort immer auf die Briefe. Nutze dabei strikt das Format 'Brief ID: [NUMMER]' oder 'Letter ID: [NUMMER]', 
        damit ich die Quellen zuordnen kann.
        """

        
        # Nur für Debugging/Präsentation:
        #print(f"--- FINAL PROMPT SENT TO LLM ---\n{system_prompt}\n--------------------------------")
        
        # --- 5. Schritt: LLM-AUFRUF (z.B. Ollama) ---
        response = ollama.chat(model='llama3', messages=[
            {'role': 'system', 'content': system_instruction},
            {'role': 'user', 'content': system_prompt}, # Hier steckt alles drin!
        ])

        
        answer = response.get('message', {}).get('content', '') or ""
        if letter_metadata_map:
            for l_id, meta in letter_metadata_map.items():
                l_name = meta['name']
                link = f"https://www.felix-mendelssohn-bartholdy.org/brief/{l_name}"
                
                # Ersetzt verschiedene Schreibweisen der ID durch den Namen mit Link (Markdown)
                # Sucht nach: "16027", "ID 16027", "Brief 16027"
                pattern = rf"(?:(Brief|Letter)\s+|ID[:\s]+)?\b{l_id}\b"
                replacement = f"[{l_name}]({link})"
                answer = re.sub(pattern, replacement, answer)

        return {
            "answer": answer,
            "sources": {
                "letter_ids": list(set(source_keys)), # Doppelte IDs entfernen
                "fact_count": len(bio_facts)          # Achte auf den Variablennamen (vorher bio_facts)
            }
        }

    except Exception as e:
        logger.error(f"Kritischer Fehler in chat_with_mendelssohn: {e}")
        raise HTTPException(status_code=500, detail=str(e))
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
