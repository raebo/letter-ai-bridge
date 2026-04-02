import ollama
import logging
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class SummaryService:
    def __init__(self, model_name="llama3"):
        self.model_name = model_name
        self.embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2', device="cuda")

    async def generate_summary(self, content: str):
        system_prompt = """
            Du bist ein spezialisierter Historiker für das Mendelssohn-Archiv. 
            Deine Aufgabe ist es, Briefe aus dem 19. Jahrhundert sachlich zusammenzufassen.

            WICHTIGE ZEITREGEL:
            - Alle Zeit- und Jahresangaben beziehen sich AUSSCHLIESSLICH auf das 19. Jahrhundert (1800-1899).
            - Eine Angabe wie "23" bedeutet immer "1823".

            INHALTLICHE REGELN:
            1. Bleibe streng sachlich. Interpretiere KEINE romantischen Beziehungen hinein.
            2. "Liebe Madame" oder "Verehrteste" sind rein höfliche Anreden der Zeit, keine Liebeserklärungen.
            3. Erfasse: Absender, Empfänger, Ort, Datum (falls vorhanden) und Kernbotschaft.
            4. Korrigiere Encoding-Fehler (z.B. "Kiéné" statt "Kin").
            
            Länge: Max. 3 Sätze.
        """

        user_prompt = f"Fasse diesen Brief von Felix Mendelssohn Bartholdy sachlich zusammen:\n\n{content}"

        response = ollama.chat(model='llama3', messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt},
            ],
            options={
                'temperature': 0.2,  # Niedrige Temperatur für sachliche Antworten
                'num_predict': 250,    # Das ist das "max_tokens" Äquivalent in Ollama
                'num_ctx': 4096
            }
                               )
        return response['message']['content']


    def create_vector(self, text: str):
        """Erzeugt den Vektor für die Zusammenfassung."""
        if not text:
            return None
        return self.embedding_model.encode(text).tolist()
