"""
routes/skills.py — Skill Extraction API Route
────────────────────────────────────────────────────────────────────
Exposes the skill extraction system as a REST endpoint.

  POST /api/github/skills
    → Accepts a GitHub repo URL
    → Returns { "skills": [...], "skill_level": "..." } + enriched context
"""

from fastapi import APIRouter, HTTPException, status

from models.schemas import SkillExtractionRequest, SkillExtractionResponse
from services.skill_extractor import extract_skills

router = APIRouter(prefix="/api/github", tags=["GitHub"])


@router.post(
    "/skills",
    response_model=SkillExtractionResponse,
    summary="Extract developer skills from a GitHub repository",
    description=(
        "Analyzes a GitHub repository and extracts a structured skill profile: "
        "programming languages, frameworks, tools, and an overall skill level "
        "(beginner / intermediate / advanced) based on repository signals."
    ),
)
async def extract_repo_skills(request: SkillExtractionRequest) -> SkillExtractionResponse:
    """
    **Skill Extraction System**

    Pipeline:
    1. Fetch repo metadata, languages, commit count, README (GitHub REST API)
    2. Map languages → skills  (`Python` → `["Python", "Backend Development"]`)
    3. Detect frameworks/tools → skills  (`FastAPI` → `["FastAPI", "REST API Development"]`)
    4. Infer project type → implied skills  (`REST API` → `["API Design", "HTTP / REST"]`)
    5. Score skill level based on commits, stars, size, breadth, complexity

    Example request:
    ```json
    { "repo_url": "https://github.com/tiangolo/fastapi" }
    ```

    Example response:
    ```json
    {
      "skills": ["API Design", "Backend Development", "FastAPI", "Python", ...],
      "skill_level": "advanced",
      "skill_score": 14,
      "categories": {
        "Languages":   ["Python"],
        "Frameworks":  ["FastAPI", "Pydantic"],
        "Domain":      ["Backend Development", "AI/ML"],
        "Practices":   ["API Design", "REST API Development"],
        "Tools":       ["Docker"]
      },
      "total_skills": 12,
      "frameworks":   ["FastAPI", "Pydantic", "pytest"],
      "project_type": "Library / Package",
      "complexity":   "High"
    }
    ```
    """
    try:
        profile = extract_skills(request.repo_url)
    except ValueError as e:
        code = (
            status.HTTP_404_NOT_FOUND
            if "not found" in str(e).lower()
            else status.HTTP_422_UNPROCESSABLE_ENTITY
        )
        raise HTTPException(status_code=code, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Analysis error: {e}"
        )

    data = profile.to_dict()

    return SkillExtractionResponse(
        skills       = data["skills"],
        skill_level  = data["skill_level"],
        skill_score  = data["skill_score"],
        total_skills = data["total_skills"],
        categories   = data["categories"],
        languages    = data["languages"],
        frameworks   = data["frameworks"],
        project_type = data["project_type"],
        complexity   = data["complexity"],
        repo         = data["repo"],
        url          = data["url"],
    )
