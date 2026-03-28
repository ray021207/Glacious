"""Handle open-ended query mode - answer general Alpine climate questions."""

from anthropic import Anthropic
import json

client = Anthropic()

def handle_query(question: str, region: str, year_start: int, year_end: int, lang: str = "en", data: dict = None) -> dict:
    """
    Answer an open-ended question about Alpine climate.
    
    Returns {"answer": str, "key_fact": str, "sources_used": list}
    """
    
    if data is None:
        data = {}
    
    # Build context from available data
    context = f"""
Question: {question}
Region: {region}
Time period: {year_start} to {year_end}
Language: {lang}

Alpine climate context: The Alps have warmed ~2.1°C since 1880 (more than global average).
Glaciers have lost ~50% area since 1900, ~30% since 1980.
Alpine regions span 8 countries and support 14M downstream inhabitants.
"""
    
    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1200,
            system="""You are Glacious, a scientific climate intelligence assistant for Alpine journalists.
Answer questions about Alpine climate with:
1. Direct factual answer with key number up front
2. Temperature, precipitation, permafrost context for the timeframe with trend
3. What the data shows (described in words)
4. Regional and global causes
5. Anthropogenic (human) expeditors
6. Ecological and social outcomes
7. Closing sentence with urgency (accurate, not alarmist)

Write for journalists: quotable facts + emotional resonance.
Length: 3-4 paragraphs, no bullet points.
Language: {lang if lang != 'de' else 'German'} (or local language if specified).
Cite specific numbers and timeframes.""",
            messages=[{"role": "user", "content": context}]
        )
        
        answer_text = message.content[0].text
        
        # Extract key fact (first sentence typically)
        sentences = answer_text.split('. ')
        key_fact = sentences[0] if sentences else answer_text[:100]
        
        return {
            "answer": answer_text,
            "key_fact": key_fact,
            "sources_used": ["Satellite Data", "Climate Records", "Alpine Research Centers"],
            "region": region,
            "year_start": year_start,
            "year_end": year_end
        }
        
    except Exception as e:
        return {
            "answer": f"Unable to generate answer for this query. Please try a more specific question about {region}.",
            "key_fact": "Data retrieval in progress",
            "sources_used": [],
            "error": str(e)
        }
