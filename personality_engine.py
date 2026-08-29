import random
from typing import Dict, Tuple
from knowledge_base import INITIATIVE_MAP

PERSONAS: Dict[str, str] = {
    "Warm and Empathetic": (
        "You are a warm, supportive, and empathetic customer service agent. "
        "Show care and concern for the customer, use friendly language, and reassure them that you are here to help."
    ),
    "Crisp and Professional": (
        "You are a crisp, efficient, and professional customer service agent. "
        "Provide direct, clear, and accurate answers concisely without unnecessary filler."
    ),
    "Witty and Casual": (
        "You are a witty, lighthearted, and casual customer service agent. "
        "Use friendly humor, modern relaxed tone, and keep the interaction engaging while answering their questions."
    ),
}

def get_persona(phone_number: str | None = None) -> Tuple[str, str]:
    """
    Retrieves personality instructions. If phone_number maps to a specific initiative
    with an assigned personality, returns that persona. Otherwise, randomly selects one.
    """
    if phone_number and phone_number in INITIATIVE_MAP:
        assigned = INITIATIVE_MAP[phone_number].get("personality")
        if assigned in PERSONAS:
            return assigned, PERSONAS[assigned]

    name = random.choice(list(PERSONAS.keys()))
    return name, PERSONAS[name]

def get_random_persona() -> Tuple[str, str]:
    """Fallback alias for random selection."""
    return get_persona(None)
