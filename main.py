import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Form, HTTPException, Response, Request, status, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from twilio.twiml.messaging_response import MessagingResponse

from knowledge_base import load_knowledge_base
from personality_engine import get_persona
from llm_service import LLMService
from session_manager import (
    get_chat_history,
    save_turn,
    get_session_state,
    set_session_state,
    save_agent_message,
    close_redis,
)
from c2_router import router as c2_router

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Trigger keywords for HITL handoff and carrier opt-out
HUMAN_KEYWORDS = {"agent", "human", "representative", "operator", "support agent"}
OPTOUT_KEYWORDS = {"stop", "unsubscribe", "cancel", "quit", "end"}

class SMSResponse(BaseModel):
    sender: str
    recipient: str
    persona: str
    reply: str
    state: str

class AgentReplyRequest(BaseModel):
    customer_number: str
    message: str

# Application state container
app_state = {
    "docs_dir": "docs",
    "llm_service": None
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Autonomous Communication & C2 Engine...")
    app_state["llm_service"] = LLMService()
    yield
    logger.info("Closing Redis connections...")
    await close_redis()

app = FastAPI(
    title="Autonomous Communication & C2 Engine",
    description="FastAPI backend for SMS customer service chatbot with C2 dashboard engine, payment bypass calendar override, Redis session persistence, and HITL handoff.",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(c2_router)

@app.get("/")
def root():
    return {"status": "running", "engine": "Autonomous SMS & C2 Control Panel"}

@app.post("/webhook/sms")
async def handle_sms_webhook(
    request: Request,
    From: str = Form(...),
    To: str = Form(...),
    Body: str = Form(...)
):
    """
    Webhook endpoint to process incoming SMS payloads.
    - Supports TwiML XML response or JSON based on Accept header.
    - Handles carrier opt-out keywords (STOP, UNSUBSCRIBE).
    - Detects human escalation requests and updates session state (HITL).
    - Maintains windowed conversation history in Redis.
    """
    body_text = Body.strip()
    if not body_text:
        raise HTTPException(status_code=400, detail="SMS Body cannot be empty.")

    body_lower = body_text.lower()

    # Check for carrier opt-out keywords
    if body_lower in OPTOUT_KEYWORDS:
        await set_session_state(From, "OPTED_OUT")
        optout_msg = "You have been unsubscribed and will no longer receive messages. Text START to resubscribe."
        return format_sms_response(request, From, To, "System", optout_msg, "OPTED_OUT")

    # Retrieve current session state
    current_state = await get_session_state(From)
    if current_state == "OPTED_OUT":
        if body_lower == "start":
            await set_session_state(From, "BOT_ACTIVE")
            resub_msg = "You have resubscribed to customer support SMS."
            return format_sms_response(request, From, To, "System", resub_msg, "BOT_ACTIVE")
        return format_sms_response(request, From, To, "System", "Number is opted out.", "OPTED_OUT")

    # Check if user requested a human agent or if already connected to a human agent
    if any(keyword in body_lower for keyword in HUMAN_KEYWORDS):
        await set_session_state(From, "HUMAN_REQUESTED")
        handoff_msg = "I have transferred your request to a human support agent. An agent will be with you shortly."
        return format_sms_response(request, From, To, "System", handoff_msg, "HUMAN_REQUESTED")

    if current_state in ("HUMAN_REQUESTED", "AGENT_CONNECTED"):
        ack_msg = "Your message has been routed to a human support agent. Please wait for their reply."
        return format_sms_response(request, From, To, "System", ack_msg, current_state)

    # Bot Active flow: Get persona and initiative-specific knowledge context
    persona_name, persona_instructions = get_persona(phone_number=To)
    docs_dir = app_state.get("docs_dir", "docs")
    knowledge_context = load_knowledge_base(docs_dir=docs_dir, phone_number=To)

    # Fetch last 5-10 turns of conversation history from Redis/Session Store
    chat_history = await get_chat_history(From)

    llm_service: LLMService = app_state["llm_service"] or LLMService()

    try:
        reply = await llm_service.generate_response(
            user_message=body_text,
            persona_instructions=persona_instructions,
            knowledge_context=knowledge_context,
            chat_history=chat_history
        )
    except Exception as e:
        logger.error(f"Error generating LLM response: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate response.")

    # Save turn (user message & bot reply) asynchronously to Redis/Session Store
    await save_turn(customer_number=From, user_message=body_text, bot_reply=reply)

    return format_sms_response(request, From, To, persona_name, reply, "BOT_ACTIVE")


@app.post("/agent/reply")
async def handle_agent_reply(req: AgentReplyRequest):
    """
    Endpoint allowing human support agents to reply directly to customers.
    Updates session state to AGENT_CONNECTED and appends reply to history.
    """
    await set_session_state(req.customer_number, "AGENT_CONNECTED")
    await save_agent_message(req.customer_number, req.message)

    return {
        "status": "success",
        "customer_number": req.customer_number,
        "state": "AGENT_CONNECTED",
        "agent_message": req.message
    }


def format_sms_response(
    request: Request,
    sender: str,
    recipient: str,
    persona: str,
    reply: str,
    state: str
):
    """
    Formats the response as TwiML XML if requested by header/query or client,
    or JSON by default.
    """
    accept_header = request.headers.get("accept", "")
    if "application/xml" in accept_header or "text/xml" in accept_header:
        twiml = MessagingResponse()
        twiml.message(reply)
        return Response(content=str(twiml), media_type="application/xml")

    return SMSResponse(
        sender=sender,
        recipient=recipient,
        persona=persona,
        reply=reply,
        state=state
    )
