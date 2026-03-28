"""Generate summaries and narrative descriptions for verdicts."""

from anthropic import Anthropic

client = Anthropic()

def summarize_verdict(verdict_dict: dict, lang: str = "en") -> str:
    """Generate a journalist-friendly summary of a claim verdict."""
    
    try:
        prompt = f"""Summarize this climate claim verdict for a journalist in {lang}:

Verdict: {verdict_dict['verdict']}
Confidence: {verdict_dict['confidence']:.0%}
Region: {verdict_dict['region']}
Variable: {verdict_dict['variable']}
Time period: {verdict_dict['year_start']}-{verdict_dict['year_end']}
Accurate finding: {verdict_dict['accurate_finding']}

Write 1-2 sentences explaining the verdict and its implications for journalism."""
        
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return message.content[0].text
    except:
        return f"The satellite data shows {verdict_dict['data_direction']} {verdict_dict['variable']} in the {verdict_dict['region']}."

def summarize_query_response(response_data: dict, lang: str = "en") -> str:
    """Generate narrative summary of query response."""
    
    try:
        summary_text = """Based on satellite data from {region} ({year_start}-{year_end}), 
the dominant trend in {variable} is {direction}. Key statistics: {key_fact}.
This reflects broader Alpine climate patterns driven by regional and global warming.""".format(**response_data)
        
        return summary_text
    except:
        return "Unable to generate summary at this time."
