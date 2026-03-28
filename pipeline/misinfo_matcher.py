"""Match claims against known misinformation database using TF-IDF similarity."""

import json
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def load_misinfo_claims() -> list:
    """Load misinformation claims database."""
    data_path = Path(__file__).parent.parent / "data" / "misinfo_claims.json"
    try:
        with open(data_path, 'r') as f:
            return json.load(f)
    except:
        # Fallback misinformation examples
        return [
            {
                "claim": "Alpine glaciers are not melting significantly",
                "verdict": "False",
                "accurate_info": "Alpine glaciers have lost 30% area since 1980 and continue accelerating",
                "languages": ["en", "de"]
            },
            {
                "claim": "Snow cover in the Alps is stable or increasing",
                "verdict": "False",
                "accurate_info": "Alpine snow cover duration declining ~2.3 days/year on average",
                "languages": ["en", "fr"]
            },
            {
                "claim": "Alpine warming is due to natural cycles, not greenhouse gases",
                "verdict": "Misleading",
                "accurate_info": "Alpine warming (+2.1°C since 1880) is 2x global average and primary driver is anthropogenic forcing",
                "languages": ["en", "de"]
            },
        ]

def load_misinfo_matches(claim_text: str, top_n: int = 3) -> list:
    """
    Find similar claims in misinformation database using TF-IDF.
    Returns list of top_n matches with similarity scores.
    """
    misinfo_claims = load_misinfo_claims()
    
    if not misinfo_claims or not claim_text:
        return []
    
    # Extract claim texts
    claim_texts = [m.get("claim", "") for m in misinfo_claims]
    claim_texts.append(claim_text)  # Add query claim
    
    try:
        # TF-IDF vectorization
        vectorizer = TfidfVectorizer(lowercase=True, stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(claim_texts)
        
        # Cosine similarity of query against all claims
        query_vector = tfidf_matrix[-1]
        similarities = cosine_similarity(query_vector, tfidf_matrix[:-1]).flatten()
        
        # Get top_n matches
        top_indices = np.argsort(similarities)[::-1][:top_n]
        top_matches = []
        
        for idx in top_indices:
            if similarities[idx] > 0.15:  # Minimum similarity threshold
                top_matches.append({
                    "matched_claim": misinfo_claims[idx]["claim"],
                    "similarity_score": float(similarities[idx]),
                    "verdict": misinfo_claims[idx]["verdict"],
                    "accurate_info": misinfo_claims[idx]["accurate_info"],
                    "languages": misinfo_claims[idx].get("languages", ["en"])
                })
        
        return top_matches
        
    except Exception as e:
        return []
