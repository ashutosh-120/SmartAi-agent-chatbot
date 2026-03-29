"""
services/gemini_service.py - Google Gemini AI Integration
──────────────────────────────────────────────────────────
Uses the new `google.genai` SDK (google-genai package).
"""

from __future__ import annotations

import logging
import json
from typing import List, Dict, Optional

from google import genai
from google.genai import types
from google.genai.errors import ClientError, ServerError

from config import settings

# ── Logging ───────────────────────────────────────────────
logger = logging.getLogger(__name__)

# ── Gemini Client ─────────────────────────────────────────
_client = genai.Client(api_key=settings.GEMINI_API_KEY)


class GeminiError(Exception):
    """Wraps Gemini errors with HTTP status codes."""
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.status_code = status_code


# ── System Prompts ────────────────────────────────────────
_CHAT_SYSTEM_PROMPT = (
    "You are SmartAI, a highly capable AI assistant helping developers."
)

_REPO_SYSTEM_PROMPT = (
    "You are a senior software architect analyzing GitHub repositories."
)


def call_gemini(
    prompt: str,
    *,
    system_instruction: Optional[str] = None,
    history: Optional[List[Dict]] = None,
    model_name: Optional[str] = None,
    response_mime_type: Optional[str] = None,
) -> str:
    """Low-level reusable function to call Gemini."""
    target_model = model_name or settings.GEMINI_MODEL

    try:
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type=response_mime_type,
        )

        if history:
            chat_session = _client.chats.create(
                model=target_model,
                config=config,
                history=history,
            )
            response = chat_session.send_message(prompt)
        else:
            response = _client.models.generate_content(
                model=target_model,
                contents=prompt,
                config=config,
            )

        reply_text = response.text
        if not reply_text:
            raise GeminiError("Empty response from Gemini.", status_code=422)

        return reply_text

    except (ClientError, ServerError) as e:
        logger.error("Gemini API error: %s", e)
        raise GeminiError(str(e), status_code=502)
    except Exception as e:
        logger.exception("Unexpected Gemini error")
        raise GeminiError(f"Unexpected error: {e}")


def _build_gemini_history(history: List[Dict]) -> List[types.Content]:
    """Convert history dicts to Gemini Content objects."""
    result = []
    for msg in history:
        role = msg.get("role")
        text = msg.get("content", "")
        if role in ("user", "model") and text:
            result.append(types.Content(role=role, parts=[types.Part(text=text)]))
    return result


def send_message(message: str, history: List[Dict]) -> str:
    """Send a message in a multi-turn conversation."""
    gemini_history = _build_gemini_history(history)
    return call_gemini(
        prompt=message,
        system_instruction=_CHAT_SYSTEM_PROMPT,
        history=gemini_history if gemini_history else None,
    )


def generate_simple_reply(prompt: str) -> str:
    """Single-turn conversation reply."""
    return call_gemini(prompt=prompt, system_instruction=_CHAT_SYSTEM_PROMPT)


def analyze_repo(repo_data: dict, question: str) -> str:
    """Analyze a repository's metadata."""
    context = (
        f"Repo: {repo_data.get('full_name')}\n"
        f"Desc: {repo_data.get('description')}\n"
        f"README: {repo_data.get('readme', '')[:2000]}"
    )
    prompt = f"{context}\n\nQuestion: {question}"
    return call_gemini(prompt=prompt, system_instruction=_REPO_SYSTEM_PROMPT)


def generate_roadmap(
    skills: list,
    missing_skills: list,
    career_goal: str,
    skill_score: int = 50,
) -> str:
    """Generate a structured JSON learning roadmap."""
    current_level = "beginner" if skill_score < 35 else "intermediate" if skill_score < 70 else "advanced"
    
    prompt = f"""Create a JSON learning roadmap for a {current_level} developer aiming to be a {career_goal}.
    - Mastered: {", ".join(skills[:10])}
    - Gaps: {", ".join(missing_skills[:10])}

    Required JSON structure:
    {{
        "title": "{career_goal} Roadmap",
        "overview": "Summary",
        "goals": [],
        "weeks": [
            {{ "week": 1, "topic": "Name", "focus": "Task", "learn": [], "project": "Work", "resources": [] }}
        ],
        "tools": [],
        "capstone_project": "Description",
        "success_metrics": []
    }}
    """
    return call_gemini(
        prompt=prompt,
        system_instruction="You are a JSON-only curriculum generator.",
        response_mime_type="application/json"
    )


def analyze_code_quality(code_samples: Dict[str, str]) -> str:
    """Analyze code quality and return JSON."""
    samples_str = "\n".join([f"FILE: {p}\n{c[:1000]}" for p, c in code_samples.items()])
    prompt = f"""Analyze code quality:\n{samples_str}\n
    Return JSON:
    {{
        "modularity": 0-100,
        "best_practices": 0-100,
        "strengths": [],
        "weaknesses": [],
        "improvements": []
    }}
    """
    return call_gemini(
        prompt=prompt,
        system_instruction="You are a senior architect. Output JSON only.",
        response_mime_type="application/json"
    )
