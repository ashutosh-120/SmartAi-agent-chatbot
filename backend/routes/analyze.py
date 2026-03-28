"""
routes/analyze.py — Main Integration Pipeline Endpoint
────────────────────────────────────────────────────────
  POST /analyze

Accepts a GitHub URL and optional career goal, runs the full
4-step pipeline, and returns a complete structured analysis.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from services.analyzer_pipeline import run_full_analysis, AnalysisResult

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
    roadmap:          str     = Field(default="",   description="Gemini-generated week-by-week roadmap (markdown).")

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

@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    summary="Full analysis pipeline: GitHub → Skills → Trends → Roadmap",
    description=(
        "**Main integration endpoint.** Runs the complete 4-step pipeline:\n\n"
        "1. 📦 Fetch repo data from GitHub (languages, commits, README, size)\n"
        "2. 🔍 Extract developer skills\n"
        "3. 📊 Match skills against market trends\n"
        "4. 🗺️ Generate a personalized roadmap with Gemini AI\n\n"
        "Returns `skills`, `matched_skills`, `missing_skills`, `career_paths`, `roadmap` + enriched metadata."
    ),
)
async def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    """
    **Complete Skill & Roadmap Analysis**

    Example:
    ```json
    { "repo_url": "https://github.com/owner/repo", "career_goal": "AI / Machine Learning Engineer" }
    ```
    """
    try:
        logger.info(f"Starting full analysis for repo: {request.repo_url}")
        result: AnalysisResult = run_full_analysis(
            repo_url    = request.repo_url,
            career_goal = request.career_goal,
        )
        logger.info(f"Analysis successful for repo: {request.repo_url}")
    except ValueError as e:
        logger.warning(f"Validation error for {request.repo_url}: {e}")
        code = (
            status.HTTP_404_NOT_FOUND
            if "not found" in str(e).lower()
            else status.HTTP_422_UNPROCESSABLE_ENTITY
        )
        raise HTTPException(status_code=code, detail=str(e))
    except PermissionError as e:
        logger.error(f"Permission error for {request.repo_url}: {e}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected pipeline error for {request.repo_url}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Analysis pipeline error: {e}"
        )

    data = result.to_dict()
    return AnalyzeResponse(**data)
