"""
routes/chat.py - Chat API Routes
─────────────────────────────────────────────────────────────────────────
Two endpoints, same Gemini service, different use cases:

  POST /chat          — Simple single-prompt endpoint (clean JSON)
  POST /api/chat      — Multi-turn conversation with history support
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, List

from models.schemas import ChatRequest, ChatResponse, ChatMessage
from services.gemini_service import (
    send_message,
    generate_simple_reply,
    GeminiError,
)
from config import settings


# ─── Router ───────────────────────────────────────────────
router = APIRouter(tags=["Chat"])


# ══════════════════════════════════════════════════════════
#  SCHEMA — Simple /chat endpoint (self-contained here)
# ══════════════════════════════════════════════════════════

class SimplePromptRequest(BaseModel):
    """Request body for the clean POST /chat endpoint."""
    prompt: str = Field(
        ...,
        min_length=1,
        max_length=8000,
        description="The user's question or prompt to send to Gemini.",
        examples=["Explain what FastAPI is in simple terms."]
    )


class SimplePromptResponse(BaseModel):
    """Clean JSON response from the POST /chat endpoint."""
    success: bool = Field(default=True, description="Whether the call succeeded.")
    prompt: str   = Field(..., description="The original prompt (echoed back).")
    reply: str    = Field(..., description="Gemini's AI-generated reply.")
    model: str    = Field(..., description="The Gemini model that generated the reply.")


# ══════════════════════════════════════════════════════════
#  ROUTE 1 — Simple Prompt (POST /chat)
#  Single prompt → Gemini → clean JSON response
#  No conversation history, minimal request body.
# ══════════════════════════════════════════════════════════

@router.post(
    "/chat",
    response_model=SimplePromptResponse,
    summary="Simple prompt → Gemini AI response",
    description=(
        "Send a single text prompt to Google Gemini and receive a clean JSON response. "
        "No conversation history is maintained — each request is independent. "
        "For multi-turn conversations see `POST /api/chat`."
    ),
)
async def simple_chat(request: SimplePromptRequest) -> SimplePromptResponse:
    """
    **Simple Gemini Integration**

    Example request:
    ```json
    { "prompt": "What is a REST API?" }
    ```

    Example response:
    ```json
    {
      "success": true,
      "prompt": "What is a REST API?",
      "reply": "A REST API is...",
      "model": "gemini-1.5-flash"
    }
    ```
    """
    try:
        reply = generate_simple_reply(request.prompt)

        return SimplePromptResponse(
            success=True,
            prompt=request.prompt,
            reply=reply,
            model=settings.GEMINI_MODEL,
        )

    except GeminiError as e:
        # Use the HTTP status code our service layer decided on
        raise HTTPException(status_code=e.status_code, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected server error: {e}",
        )


# ══════════════════════════════════════════════════════════
#  ROUTE 2 — Multi-turn Chat (POST /api/chat)
#  Full conversation history support for the React frontend.
# ══════════════════════════════════════════════════════════

router_api = APIRouter(prefix="/api/chat", tags=["Chat"])


@router_api.post(
    "",
    response_model=ChatResponse,
    summary="Multi-turn conversation with Gemini AI",
    description=(
        "Send a message with full conversation history for multi-turn context. "
        "History format: `[{\"role\": \"user\"|\"model\", \"content\": \"...\"}]`"
    ),
)
async def multi_turn_chat(request: ChatRequest) -> ChatResponse:
    """
    **Multi-turn Chat**

    Maintains conversation context by sending the full message history to Gemini.
    Used by the React frontend chat interface.
    """
    try:
        history_dicts = [
            {"role": msg.role, "content": msg.content}
            for msg in (request.history or [])
        ]

        reply = send_message(
            message=request.message,
            history=history_dicts,
        )

        return ChatResponse(reply=reply, model=settings.GEMINI_MODEL)

    except GeminiError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected server error: {e}",
        )
