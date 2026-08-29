from contextlib import asynccontextmanager
from fastapi import FastAPI, Form, HTTPException, status
from pydantic import BaseModel
import logging

from knowledge_base import load_knowledge_base
from personality_engine import get_persona
from llm_service import LLMService

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SMSResponse(BaseModel):
    sender: str
    recipient: str
    persona: str
    reply: str

# Application state container
app_state = {
    "docs_dir": "docs",
    "llm_service": None
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing SMS Chatbot service...")
    app_state["llm_service"] = LLMService()
    yield

app = FastAPI(
    title="SMS Customer Service Chatbot",
    description="FastAPI backend for SMS customer service chatbot with dynamic personality injection, initiative mapping by phone number, and Markdown knowledge base.",
    lifespan=lifespan
)

@app.post("/webhook/sms", response_model=SMSResponse, status_code=status.HTTP_200_OK)
async def handle_sms_webhook(
    From: str = Form(...),
    To: str = Form(...),
    Body: str = Form(...)
):
    """
    Webhook endpoint to process incoming SMS form payload.
    - Accepts Form data: From, To, Body
    - Identifies initiative knowledge base & personality based on recipient phone number ('To')
    - Generates response using LLM service
    """
    if not Body.strip():
        raise HTTPException(status_code=400, detail="SMS Body cannot be empty.")

    # Retrieve persona based on recipient phone number ('To')
    persona_name, persona_instructions = get_persona(phone_number=To)

    # Load initiative-specific knowledge context based on recipient phone number ('To')
    docs_dir = app_state.get("docs_dir", "docs")
    knowledge_context = load_knowledge_base(docs_dir=docs_dir, phone_number=To)

    llm_service: LLMService = app_state["llm_service"] or LLMService()

    try:
        reply = llm_service.generate_response(
            user_message=Body,
            persona_instructions=persona_instructions,
            knowledge_context=knowledge_context
        )
    except Exception as e:
        logger.error(f"Error generating LLM response: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate response.")

    return SMSResponse(
        sender=From,
        recipient=To,
        persona=persona_name,
        reply=reply
    )
