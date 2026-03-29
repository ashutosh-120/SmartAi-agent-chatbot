"""
routes/analyze.py — Main Integration Pipeline Endpoint
────────────────────────────────────────────────────────
  POST /analyze

Accepts a GitHub URL and optional career goal, runs the full
4-step pipeline, and returns a complete structured analysis.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, status, Header
from pydantic import BaseModel, Field
from typing import Optional, List, Any

from services.analyzer_pipeline import run_full_analysis, AnalysisResult
from database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Analysis Pipeline"])


# ── Request / Response Models ──────────────────────────────────

class AnalyzeRequest(BaseModel):
    """Request body for the main POST /analyze endpoint."""
    repo_url: str = Field(
        ...,
        description="GitHub repository URL to analyze.",
        examples=["https://github.com/tiangolo/fastapi"]
    )
    career_goal: Optional[str] = Field(
        default=None,
        description=(
            "Target career goal for the roadmap. "
            "If omitted, the best-matching trend is used automatically. "
            "Options: 'AI / Machine Learning Engineer', 'Full Stack Web Developer', "
            "'Cloud / DevOps Engineer', 'Mobile App Developer', "
            "'Data Engineer', 'Backend / API Developer'"
        ),
        examples=["Full Stack Web Developer"]
    )


class AnalyzeResponse(BaseModel):
    """
    Complete analysis result from the full pipeline.
    All 7 core fields + enriched metadata.
    """
    # ── Core requested fields ─────────────────────────────
    skills:           list    = Field(...,           description="All extracted skills.")
    matched_skills:   list    = Field(...,           description="Skills matching market trends.")
    missing_skills:   list    = Field(...,           description="Skills needed for the career goal.")
    career_paths:     list    = Field(...,           description="Relevant job titles.")
    roadmap:          Any     = Field(default_factory=dict, description="Gemini-generated structured roadmap (JSON).")

    # ── Scoring ───────────────────────────────────────────
    skill_score:      int     = Field(default=0,    description="0–100 skill strength score.")
    confidence_score: float   = Field(default=0.0,  description="0.0–1.0 analysis confidence.")
    skill_level:      str     = Field(default="",   description="beginner | intermediate | advanced")

    # ── Enriched data ─────────────────────────────────────
    skill_categories: dict    = Field(default_factory=dict, description="Skills grouped by category.")
    suggested_paths:  list    = Field(default_factory=list, description="Top 5 career path suggestions with match %.")
    frameworks:       list    = Field(default_factory=list, description="Detected frameworks/tools.")
    languages:        list    = Field(default_factory=list, description="Programming languages used.")
    project_type:     str     = Field(default="",   description="Inferred project type.")
    complexity:       str     = Field(default="",   description="Repo complexity.")
    repo_name:        str     = Field(default="",   description="owner/repo slug.")
    repo_url:         str     = Field(default="",   description="GitHub URL.")
    roadmap_error:    Optional[str] = Field(default=None, description="Set if roadmap generation failed.")


# ── Route ─────────────────────────────────────────────────────

async def get_current_user_id(authorization: Optional[str] = Header(None)) -> Optional[str]:
    """Helper to extract user_id from Supabase JWT if present."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    try:
        token = authorization.split(" ")[1]
        db = get_db()
        # Use supabase-py to verify the session/user from the token
        user_resp = db.auth.get_user(token)
        if user_resp and user_resp.user:
            return user_resp.user.id
    except Exception as e:
        logger.warning(f"Failed to extract user from token: {e}")
    return None

@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    summary="Full analysis pipeline: GitHub → Skills → Trends → Roadmap",
)
async def analyze(
    request: AnalyzeRequest, 
    authorization: Optional[str] = Header(None)
) -> AnalyzeResponse:
    """**Complete Skill & Roadmap Analysis**"""
    user_id = await get_current_user_id(authorization)
    
    try:
        logger.info(f"Starting full analysis for repo: {request.repo_url} | user: {user_id}")
        # Pass user_id to the pipeline for smarter caching if needed
        result: AnalysisResult = run_full_analysis(
            repo_url    = request.repo_url,
            career_goal = request.career_goal,
        )
    except ValueError as e:
        logger.warning(f"Validation error for {request.repo_url}: {e}")
        code = status.HTTP_404_NOT_FOUND if "not found" in str(e).lower() else status.HTTP_422_UNPROCESSABLE_ENTITY
        raise HTTPException(status_code=code, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected pipeline error for {request.repo_url}")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Analysis pipeline error: {e}")

    data = result.to_dict()
    
    # ── Step 5: Save to Supabase ─────────────────────────────
    try:
        db = get_db()
        db_data = {
            "user_id":       user_id,
            "repo_url":      data["repo_url"],
            "repo_name":     data["repo_name"],
            "skill_score":   data["skill_score"],
            "skill_level":   data["skill_level"],
            "career_goal":   request.career_goal or data.get("career_paths", ["Full Stack Web Developer"])[0],
            "languages":     data["languages"],
            "skills":        data["skills"],
            "roadmap_json":  data["roadmap"],
        }
        db.table("analyses").insert(db_data).execute()
        logger.info(f"Saved analysis result for user {user_id} successfully.")
    except Exception as e:
        logger.warning(f"Failed to save to Supabase (non-fatal): {e}")

    return AnalyzeResponse(**data)

@router.get("/history", response_model=List[AnalyzeResponse])
async def get_history(
    limit: int = 10, 
    authorization: Optional[str] = Header(None)
):
    """Fetch the user's personal analysis results."""
    user_id = await get_current_user_id(authorization)
    if not user_id:
        return [] # Return empty if guest/not logged in
        
    try:
        db = get_db()
        resp = db.table("analyses")\
            .select("*")\
            .eq("user_id", user_id)\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()
        
        history = []
        for row in resp.data:
            history.append(AnalyzeResponse(
                repo_url=row["repo_url"],
                repo_name=row["repo_name"],
                skill_score=row["skill_score"],
                skill_level=row["skill_level"],
                roadmap=row["roadmap_json"],
                skills=row["skills"],
                matched_skills=[],
                missing_skills=[],
                career_paths=[row["career_goal"]],
                skill_categories={}, 
                languages=row.get("languages", [])
            ))
        return history
    except Exception as e:
        logger.error(f"Failed to fetch history for user {user_id}: {e}")
        return []
