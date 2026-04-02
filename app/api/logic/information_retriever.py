import re
import logging

logger = logging.getLogger(__name__)

class InformationRetriever:


    @staticmethod
    def get_relevant_locations(query_text, query_vector, limit=60, top_n=3):
        from app.database.models.entity_embedding import EntityEmbedding

        # 1. Grobe Vektorsuche
        candidates = EntityEmbedding.search_knowledge(
            query_vector, e_type='travel_log', limit=limit, min_score=0.15
        )

        if not candidates:
            return []

        # 2. Keywords und Jahre extrahieren
        keywords = re.findall(r'\b[A-Z][a-zäöüß]+\b', query_text)
        years = re.findall(r'\b(18\d{2})\b', query_text)

        # 3. Re-Ranking in EINER Schleife
        ranked_results = []
        for cand in candidates:
            content_lower = cand['content'].lower()
            score_boost = 0.0
            
            # Orts-Boost
            for word in keywords:
                if word.lower() in content_lower:
                    score_boost += 0.6  # Erhöht für klare Ortsmatches
            
            # Jahres-Boost
            if years:
                if any(year in cand['content'] for year in years):
                    score_boost += 0.8  # Hoher Bonus für das richtige Jahr

            combined_priority = cand['score'] + score_boost
            ranked_results.append((combined_priority, cand))

        # 4. Sortieren nach Combined Priority
        ranked_results.sort(key=lambda x: x[0], reverse=True)

        # DEBUG LOG (Korrigierter Zugriff)
        print(f"\n--- DEBUG InformationRetriever SEARCH ---")
        print(f"User-Query: {query_text}")
        for idx, (prio, data) in enumerate(ranked_results[:10]): # Zeige Top 10 im Log
            found_marker = "🎯" if prio > data['score'] else "  "
            print(f"{found_marker} Platz {idx+1}: {data['content']} (Prio: {prio:.4f}, V-Score: {data['score']:.4f})")
        print(f"-----------------------------------------\n")

        return [item[1] for item in ranked_results[:top_n]]
