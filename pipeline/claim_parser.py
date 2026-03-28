"""Parse claims to extract region, variable, time frame, and direction."""

import json
from anthropic import Anthropic

client = Anthropic()

ALPINE_REGIONS = [
    "Swiss Alps", "French Alps", "Italian Alps", "Austrian Alps", "Slovenian Alps",
    "Dolomites", "Mont Blanc", "Pennine Alps", "Bernese Alps", "Ötztal Alps",
    "Zillertal Alps", "Hohe Tauern", "Julian Alps", "Maritime Alps", "Cottian Alps",
    "Graian Alps", "Lepontine Alps", "Rhaetian Alps", "Ortler Alps", "Carnic Alps",
    "Karawanks", "Stubai Alps", "Adamello-Presanella", "All Alpine ranges"
]

VARIABLES = [
    "glacier", "glacier area", "snow cover", "snow", "temperature",
    "permafrost", "precipitation", "rainfall", "vegetation", "treeline",
    "biodiversity", "wildlife", "water", "meltwater", "avalanche", "rockfall"
]

def parse_claim(claim_text: str) -> dict:
    """
    Extract region, variable, direction, magnitude, and time frame from a claim.
    Returns dict with keys: region, variable, direction, magnitude, year_start, year_end
    """
    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=400,
            system="""You are AlpineCheck. Extract structured data from a climate claim about the Alps.

Return ONLY valid JSON (no markdown, no code blocks):
{
  "region": "identified Alpine region or 'All Alps'",
  "variable": "main environmental variable (glacier, snow, temperature, permafrost, precipitation, etc.)",
  "direction": "increasing, decreasing, or changing with no clear direction",
  "magnitude": "numeric value if stated, otherwise null",
  "year_start": 2015,
  "year_end": 2024,
  "confidence": 0.0-1.0
}

For year_start/year_end, infer from "past X years" phrasing. Current year is 2026.
""",
            messages=[{"role": "user", "content": f"Parse this claim:\n\n{claim_text}"}]
        )
        
        response_text = message.content[0].text.strip()
        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
            response_text = response_text.strip()
        
        result = json.loads(response_text)
        
        # Ensure required keys exist
        result.setdefault("region", "All Alps")
        result.setdefault("variable", "glacier")
        result.setdefault("direction", "unknown")
        result.setdefault("magnitude", None)
        result.setdefault("year_start", 2000)
        result.setdefault("year_end", 2026)
        result.setdefault("confidence", 0.5)
        
        return result
    except Exception as e:
        # Return default parsed structure
        return {
            "region": "All Alps",
            "variable": "glacier",
            "direction": "unknown",
            "magnitude": None,
            "year_start": 2000,
            "year_end": 2026,
            "confidence": 0.3
        }

