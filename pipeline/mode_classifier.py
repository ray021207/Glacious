"""Classify user input as query or validation mode."""

import json
from anthropic import Anthropic

client = Anthropic()

def classify_mode(user_input: str) -> dict:
    """
    Classify whether user input is a question (query mode) or claim (validation mode).
    Returns {"mode": "query" | "validation", "claim": None | str}
    """
    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=300,
            system="""You are Glacious, a scientific climate intelligence assistant. Classify whether the user's input is:
1. A QUESTION (query mode) - asking for information, data, or explanation
2. A CLAIM (validation mode) - making a factual assertion to be verified

Respond with ONLY valid JSON (no markdown, no code blocks):
{"mode": "query" or "validation", "claim": null or the original claim text}

If query mode, claim should be null.
If validation mode, claim should be the exact claim text.
""",
            messages=[{"role": "user", "content": f"Classify this input:\n\n{user_input}"}]
        )
        
        response_text = message.content[0].text.strip()
        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
            response_text = response_text.strip()
        
        result = json.loads(response_text)
        return result
    except Exception as e:
        # Default to query mode if classification fails
        return {"mode": "query", "claim": None}
