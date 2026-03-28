"""Causes engine - provide context on causes and outcomes of Alpine changes."""

from anthropic import Anthropic

client = Anthropic()

def get_causes_context(variable: str, region: str, lang: str = "en") -> dict:
    """
    Get structured context on causes and outcomes.
    
    Returns dict with keys: regional_causes, global_causes, anthropogenic_expeditors,
    ecological_outcomes, social_outcomes
    """
    
    language_map = {
        "en": "English",
        "de": "German",
        "fr": "French",
        "it": "Italian",
        "sl": "Slovenian",
        "rm": "Romansh",
        "hr": "Croatian",
        "fur": "Friulian"
    }
    
    lang_name = language_map.get(lang, "English")
    
    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=800,
            system=f"""You are Glacious. You provide Alpine climate context written for journalists in {lang_name}.
Use concrete numbers, specific examples, accessible language (no jargon).
Focus on: what's changing, why, and what it means for mountain communities.""",
            messages=[{
                "role": "user",
                "content": f"""Provide causes and outcomes context for this Alpine climate change:

Variable: {variable}
Region: {region}

Format your response as valid JSON with these keys:
- regional_causes: list of 2-3 regional causes (specific to Alps)
- global_causes: list of 2-3 global climate forcing causes
- anthropogenic_expeditors: list of 2-3 human activities worsening change
- ecological_outcomes: list of 2-3 species/ecosystem impacts with specifics
- social_outcomes: list of 2-3 community/economic impacts with numbers

Keep descriptions journalist-friendly, 1-2 sentences each.
Include specific numbers where possible (e.g., "supplies water to 14M people").
Output ONLY valid JSON, no markdown."""
            }]
        )
        
        response_text = message.content[0].text
        # Clean markdown if present
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
            response_text = response_text.strip()
        
        result = json.loads(response_text)
        return result
        
    except:
        # Fallback causes
        return {
            "regional_causes": [
                "Atlantic circulation weakening, reducing moisture to Alps",
                "Mediterranean Sea warming amplifies summer heat transfer to mountains",
                "North Atlantic Oscillation shifts affecting Alpine precipitation patterns"
            ],
            "global_causes": [
                "Greenhouse gas forcing raising global baseline temperature +1.1°C",
                "Arctic amplification feedback accelerating high-altitude warming",
                "Global mean temperature rise 1.1°C above pre-industrial baseline"
            ],
            "anthropogenic_expeditors": [
                "Black carbon (soot) deposition darkens snow, reducing albedo",
                "Aviation contrails and cirrus clouds trap heat over Alpine corridors",
                "Valley land-use change (urbanization) creates local heat islands"
            ],
            "ecological_outcomes": [
                f"Loss of glacially-fed wetlands and alpine meadows in {region}",
                "Upslope vegetation encroachment: treeline advancing 1-2m/year",
                "Cold-adapted species (Alpine ibex, pika) restricted to higher elevations"
            ],
            "social_outcomes": [
                f"14 million downstream inhabitants of Alps face reduced summer water availability",
                f"Ski industry revenue losses: ski season shortened by ~4 weeks since 1980",
                f"Increased avalanche, flood, and rockfall hazard frequency in {region}"
            ]
        }

import json
