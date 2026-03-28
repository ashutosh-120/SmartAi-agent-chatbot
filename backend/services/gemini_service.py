"""
services/gemini_service.py - Google Gemini AI Integration
──────────────────────────────────────────────────────────
Uses the new `google.genai` SDK (google-genai package).

Core design:
  • call_gemini()          — low-level reusable function for any Gemini request
  • send_message()         — multi-turn chat (uses call_gemini internally)
  • generate_simple_reply()— single-shot prompt (for POST /chat route)
  • analyze_repo()         — GitHub repo analysis (uses call_gemini internally)

All errors are caught, classified, and re-raised as GeminiError so that
route handlers only need to catch one exception type.
"""

from __future__ import annotations

import logging
from typing import List, Dict, Optional

from google import genai
from google.genai import types
from google.genai.errors import ClientError, ServerError

from config import settings

# ── Logging ───────────────────────────────────────────────
logger = logging.getLogger(__name__)

# ── Gemini Client — created once at module import ─────────
_client = genai.Client(api_key=settings.GEMINI_API_KEY)


# ══════════════════════════════════════════════════════════
#  Custom Exception
# ══════════════════════════════════════════════════════════

class GeminiError(Exception):
    """
    Wraps all Gemini-related errors with a user-friendly message
    and an HTTP status code hint for the route layer.
    """
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.status_code = status_code


# ══════════════════════════════════════════════════════════
#  System Prompts
# ══════════════════════════════════════════════════════════

_CHAT_SYSTEM_PROMPT = (
    "You are SmartAI, a highly capable and friendly AI assistant. "
    "You help users understand code, repositories, and technical concepts. "
    "Provide clear, concise, and well-structured answers using markdown when helpful. "
    "When analyzing GitHub repositories, highlight key technologies, "
    "architecture patterns, and potential improvements."
)

_REPO_SYSTEM_PROMPT = (
    "You are a senior software architect. Analyze GitHub repositories and deliver "
    "insightful, structured summaries that cover: purpose, tech stack, architecture, "
    "code quality indicators, and actionable recommendations. "
    "Format your response with clear markdown sections."
)


# ══════════════════════════════════════════════════════════
#  CORE REUSABLE FUNCTION
# ══════════════════════════════════════════════════════════

def call_gemini(
    prompt: str,
    *,
    system_instruction: Optional[str] = None,
    history: Optional[List[Dict]] = None,
    model_name: Optional[str] = None,
) -> str:
    """
    Low-level reusable function to send any prompt to the Gemini API.

    This is the single point of contact with the Gemini SDK — every
    other function in this module calls this one. That means you only
    ever need to update error handling or model config in one place.

    Args:
        prompt:             The user prompt / question to send.
        system_instruction: Optional system-level persona for the model.
        history:            Previous conversation turns as a list of
                            Content objects [{role, parts: [text]}, ...].
        model_name:         Override the default model from settings.

    Returns:
        The model's plain-text reply string.

    Raises:
        GeminiError: Translated, user-friendly error with an HTTP status hint.
    """
    target_model = model_name or settings.GEMINI_MODEL

    try:
        # Build config (system instruction is part of GenerateContentConfig)
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
        ) if system_instruction else None

        if history:
            # ── Multi-turn chat using the Chats API ───────
            chat_session = _client.chats.create(
                model=target_model,
                config=config,
                history=history,
            )
            response = chat_session.send_message(prompt)
        else:
            # ── Single-shot generation ────────────────────
            response = _client.models.generate_content(
                model=target_model,
                contents=prompt,
                config=config,
            )

        # Validate we actually got text back
        reply_text = response.text
        if not reply_text:
            raise GeminiError(
                "The model returned an empty response. "
                "This may be due to safety filters. Please rephrase your prompt.",
                status_code=422,
            )

        logger.info(
            "Gemini call succeeded | model=%s | prompt_chars=%d | reply_chars=%d",
            target_model, len(prompt), len(reply_text)
        )
        return reply_text

    # ── Classify errors ────────────────────────────────────
    except ClientError as e:
        logger.warning("Gemini client error (4xx): %s", e)
        code = getattr(e, "status_code", None) or getattr(e, "code", None)
        if code == 403:
            raise GeminiError(
                "Gemini API key is invalid or lacks permission. "
                "Check GEMINI_API_KEY in your .env file.",
                status_code=403,
            ) from e
        if code == 429:
            raise GeminiError(
                "Gemini API rate limit exceeded. Please wait a moment and try again.",
                status_code=429,
            ) from e
        if code == 400:
            raise GeminiError(
                f"Invalid request sent to Gemini: {e}. "
                "Check your message format and try again.",
                status_code=400,
            ) from e
        raise GeminiError(str(e), status_code=502) from e

    except ServerError as e:
        logger.error("Gemini server error (5xx): %s", e)
        raise GeminiError(
            "Google AI service is temporarily unavailable. Please try again shortly.",
            status_code=502,
        ) from e

    except GeminiError:
        raise  # Re-raise our own errors unchanged

    except Exception as e:
        logger.exception("Unexpected error calling Gemini")
        raise GeminiError(
            f"Unexpected AI call error: {e}",
            status_code=500,
        ) from e


# ══════════════════════════════════════════════════════════
#  HIGH-LEVEL HELPERS (build on call_gemini)
# ══════════════════════════════════════════════════════════

def _build_gemini_history(history: List[Dict]) -> List[types.Content]:
    """
    Convert internal [{role, content}] dicts to Gemini Content objects.
    Only includes 'user' and 'model' roles — filters out system/error/github.
    """
    result = []
    for msg in history:
        role = msg.get("role")
        text = msg.get("content", "")
        if role in ("user", "model") and text:
            result.append(
                types.Content(role=role, parts=[types.Part(text=text)])
            )
    return result


def send_message(message: str, history: List[Dict]) -> str:
    """
    Send a user message in a multi-turn conversation and return the reply.

    Args:
        message:  The user's latest message text.
        history:  Previous turns [{role: "user"|"model", content: "..."}].

    Returns:
        The AI's reply as a plain string.

    Raises:
        GeminiError: On any Gemini API failure.
    """
    gemini_history = _build_gemini_history(history)
    return call_gemini(
        prompt=message,
        system_instruction=_CHAT_SYSTEM_PROMPT,
        history=gemini_history if gemini_history else None,
    )


def generate_simple_reply(prompt: str) -> str:
    """
    Send a single prompt to Gemini with no history context.
    Used by the simple POST /chat endpoint.

    Args:
        prompt: The user's prompt text.

    Returns:
        The AI's reply as a plain string.

    Raises:
        GeminiError: On any Gemini API failure.
    """
    return call_gemini(
        prompt=prompt,
        system_instruction=_CHAT_SYSTEM_PROMPT,
    )


def analyze_repo(repo_data: dict, question: str) -> str:
    """
    Use Gemini to analyze a GitHub repository's metadata and README.

    Args:
        repo_data: Dictionary containing repo info and README content.
        question:  The user's specific question about the repo.

    Returns:
        Gemini's analysis as a plain string.

    Raises:
        GeminiError: On any Gemini API failure.
    """
    context = (
        f"Repository: {repo_data.get('full_name', 'Unknown')}\n"
        f"Description: {repo_data.get('description', 'No description')}\n"
        f"Primary Language: {repo_data.get('language', 'Unknown')}\n"
        f"Stars: {repo_data.get('stars', 0):,}\n"
        f"Forks: {repo_data.get('forks', 0):,}\n"
        f"Open Issues: {repo_data.get('open_issues', 0):,}\n"
        f"Topics: {', '.join(repo_data.get('topics', [])) or 'None'}\n"
        f"License: {repo_data.get('license', 'Not specified')}\n"
        f"Default Branch: {repo_data.get('default_branch', 'main')}\n\n"
        f"README Content (excerpt):\n"
        f"{repo_data.get('readme', 'No README available')[:3000]}"
    )

    prompt = f"{context}\n\nUser's Question: {question}"

    return call_gemini(
        prompt=prompt,
        system_instruction=_REPO_SYSTEM_PROMPT,
    )

def generate_roadmap(
    skills: list,
    missing_skills: list,
    career_goal: str,
    skill_score: int = 50,
    project_type: str = "Software Project",
) -> str:
    """
    Generate a personalized 8-12 week roadmap using Gemini.
    Uses strong prompt engineering for structured week-by-week output.
    """
    current_level = (
        "beginner" if skill_score < 35
        else "intermediate" if skill_score < 70
        else "advanced"
    )
    weeks = 12 if current_level == "beginner" else 10 if current_level == "intermediate" else 8
    skills_str  = ", ".join(skills[:20])        or "Not determined"
    missing_str = ", ".join(missing_skills[:15]) or "None identified"

    prompt = f"""You are an expert technical career coach and curriculum designer.

Create a personalized, actionable learning roadmap for a developer with the profile below.

## Developer Profile
- Career Goal: {career_goal}
- Current Level: {current_level} (skill score: {skill_score}/100)
- Project Background: {project_type}
- Skills Already Mastered: {skills_str}
- Key Skills to Learn: {missing_str}

## Your Task
Generate a {weeks}-week structured roadmap to help this developer become a {career_goal}.

## Output Format (follow EXACTLY):

# {career_goal} Roadmap ({current_level.title()} Level)

## Overview
[2-3 sentences describing the plan]

## Learning Goals
- [Goal 1]
- [Goal 2]
- [Goal 3]

---
## Week 1: [Topic]
**Focus:** [brief focus]
**Learn:**
- [concept]
- [concept]
**Project:** [hands-on task]
**Resources:** [2-3 platforms/tools/docs]
---
[continue for each week]
---

## Recommended Tools
| Tool | Purpose |
|------|---------|
| [tool] | [why] |

## Capstone Project
[Portfolio-worthy final project description]

## Success Metrics
- [ ] [milestone]
- [ ] [milestone]

Rules: be specific with real library/tool names, build week on week, skip skills already known, markdown only."""

    _ROADMAP_SYSTEM = (
        "You are a world-class technical career coach specializing in personalized "
        "developer roadmaps. Create structured, practical, week-by-week plans. "
        "Always output clean well-structured markdown with specific actionable items."
    )
    return call_gemini(prompt=prompt, system_instruction=_ROADMAP_SYSTEM)
