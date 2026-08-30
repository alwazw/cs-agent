import json
import os
import logging
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

TTL_SECONDS = 7200  # Automatically expire inactive sessions after 2 hours
MAX_MESSAGES = 10   # Store 10 messages total (5 user + 5 assistant)

# Check if Redis client can be initialized
try:
    import redis.asyncio as redis
    redis_client = redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        db=int(os.getenv("REDIS_DB", 0)),
        decode_responses=True
    )
except Exception as e:
    logger.warning(f"Failed to initialize Redis client: {e}")
    redis_client = None

# In-memory session store fallback for testing/environments without Redis
_in_memory_store: Dict[str, List[str]] = {}
_in_memory_state: Dict[str, str] = {}

def _get_session_key(customer_number: str) -> str:
    return f"chat_session:{customer_number}"

def _get_state_key(customer_number: str) -> str:
    return f"chat_state:{customer_number}"

async def get_session_state(customer_number: str) -> str:
    """Retrieve session state ('BOT_ACTIVE', 'HUMAN_REQUESTED', 'AGENT_CONNECTED', 'OPTED_OUT')."""
    key = _get_state_key(customer_number)
    if redis_client:
        try:
            state = await redis_client.get(key)
            if state:
                return state
        except Exception as e:
            logger.debug(f"Redis get state error, using in-memory fallback: {e}")

    return _in_memory_state.get(key, "BOT_ACTIVE")

async def set_session_state(customer_number: str, state: str) -> None:
    """Set session state."""
    key = _get_state_key(customer_number)
    if redis_client:
        try:
            await redis_client.set(key, state, ex=TTL_SECONDS)
            return
        except Exception as e:
            logger.debug(f"Redis set state error, using in-memory fallback: {e}")

    _in_memory_state[key] = state

async def get_chat_history(customer_number: str) -> List[Dict[str, str]]:
    """Retrieve past messages for a customer formatted for OpenAI context payload."""
    key = _get_session_key(customer_number)
    if redis_client:
        try:
            raw_history = await redis_client.lrange(key, 0, -1)
            return [json.loads(msg) for msg in raw_history]
        except Exception as e:
            logger.debug(f"Redis get_chat_history error, using in-memory fallback: {e}")

    raw_history = _in_memory_store.get(key, [])
    return [json.loads(msg) for msg in raw_history]

async def save_turn(customer_number: str, user_message: str, bot_reply: str) -> None:
    """Atomic write: Push user message & bot reply, trim list to max limit, set TTL."""
    key = _get_session_key(customer_number)

    user_payload = json.dumps({"role": "user", "content": user_message})
    assistant_payload = json.dumps({"role": "assistant", "content": bot_reply})

    if redis_client:
        try:
            async with redis_client.pipeline(transaction=True) as pipe:
                pipe.rpush(key, user_payload, assistant_payload)
                pipe.ltrim(key, -MAX_MESSAGES, -1)
                pipe.expire(key, TTL_SECONDS)
                await pipe.execute()
            return
        except Exception as e:
            logger.debug(f"Redis save_turn error, using in-memory fallback: {e}")

    # Fallback to in-memory store
    if key not in _in_memory_store:
        _in_memory_store[key] = []
    _in_memory_store[key].extend([user_payload, assistant_payload])
    if len(_in_memory_store[key]) > MAX_MESSAGES:
        _in_memory_store[key] = _in_memory_store[key][-MAX_MESSAGES:]

async def save_agent_message(customer_number: str, agent_message: str) -> None:
    """Save a human agent reply to the conversation history."""
    key = _get_session_key(customer_number)
    assistant_payload = json.dumps({"role": "assistant", "content": f"[Human Agent] {agent_message}"})

    if redis_client:
        try:
            async with redis_client.pipeline(transaction=True) as pipe:
                pipe.rpush(key, assistant_payload)
                pipe.ltrim(key, -MAX_MESSAGES, -1)
                pipe.expire(key, TTL_SECONDS)
                await pipe.execute()
            return
        except Exception as e:
            logger.debug(f"Redis save_agent_message error, using in-memory fallback: {e}")

    if key not in _in_memory_store:
        _in_memory_store[key] = []
    _in_memory_store[key].append(assistant_payload)
    if len(_in_memory_store[key]) > MAX_MESSAGES:
        _in_memory_store[key] = _in_memory_store[key][-MAX_MESSAGES:]

async def reset_session(customer_number: str) -> None:
    """Reset session history and state."""
    key = _get_session_key(customer_number)
    state_key = _get_state_key(customer_number)
    if redis_client:
        try:
            await redis_client.delete(key, state_key)
        except Exception as e:
            logger.debug(f"Redis reset_session error: {e}")

    _in_memory_store.pop(key, None)
    _in_memory_state.pop(state_key, None)

async def close_redis() -> None:
    """Close Redis client connection if open."""
    if redis_client:
        try:
            await redis_client.aclose()
        except Exception:
            pass
