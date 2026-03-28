"""
routes/github.py - GitHub Repository Routes
──────────────────────────────────────────────────────────────────
Two endpoints:

  POST /api/github/analyze        — AI-powered Q&A about a repo (Gemini)
  POST /api/github/repo-analysis  — Structured data extraction (no AI needed)
"""

from fastapi import APIRouter, HTTPException, status
from models.schemas import (
    GitHubRequest, GitHubResponse, GitHubRepoInfo,
    RepoAnalysisRequest, RepoAnalysisResponse,
)
from services import gemini_service
from services.github_service import (
    parse_github_url,
    fetch_repo_data,
    analyze_repository,
)

router = APIRouter(prefix="/api/github", tags=["GitHub"])


# ══════════════════════════════════════════════════════════════
#  ROUTE 1 — AI-powered repo analysis (existing, unchanged)
#  POST /api/github/analyze
# ══════════════════════════════════════════════════════════════

@router.post(
    "/analyze",
    response_model=GitHubResponse,
    summary="Ask Gemini AI about a GitHub repository",
    description=(
        "Fetches repo metadata + README, then uses Gemini to answer a custom question "
        "or provide a comprehensive summary."
    ),
)
async def analyze_github_repo(request: GitHubRequest) -> GitHubResponse:
    """
    Combines GitHub data fetching with Gemini AI analysis.
    Ideal for open-ended Q&A about the repository.
    """
    # ── 1. Parse URL ────────────────────────────────────────
    try:
        owner, repo_name = parse_github_url(request.repo_url)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    # ── 2. Fetch GitHub data ─────────────────────────────────
    try:
        repo_data = fetch_repo_data(owner, repo_name)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"GitHub API error: {e}"
        )

    # ── 3. Run Gemini analysis ──────────────────────────────
    try:
        question = request.question or "Give me a comprehensive summary of this repository."
        ai_analysis = gemini_service.analyze_repo(repo_data, question)
    except gemini_service.GeminiError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI analysis error: {e}"
        )

    # ── 4. Build response ───────────────────────────────────
    repo_info = GitHubRepoInfo(
        name=repo_data["name"],
        full_name=repo_data["full_name"],
        description=repo_data.get("description"),
        language=repo_data.get("language"),
        stars=repo_data.get("stars", 0),
        forks=repo_data.get("forks", 0),
        open_issues=repo_data.get("open_issues", 0),
        topics=repo_data.get("topics", []),
        license=repo_data.get("license"),
        url=repo_data["url"],
        default_branch=repo_data.get("default_branch", "main"),
    )
    readme = repo_data.get("readme", "")
    readme_preview = (readme[:500] + "...") if readme and len(readme) > 500 else readme

    return GitHubResponse(
        repo_info=repo_info,
        ai_analysis=ai_analysis,
        readme_preview=readme_preview,
    )


# ══════════════════════════════════════════════════════════════
#  ROUTE 2 — Structured Repo Analysis (NEW)
#  POST /api/github/repo-analysis
#
#  Returns the structured JSON the user requested:
#  { "languages": [], "tech_stack": [], "complexity": "", "project_type": "" }
#  plus full metadata (commits, size, language bytes, readme preview, etc.)
# ══════════════════════════════════════════════════════════════

@router.post(
    "/repo-analysis",
    response_model=RepoAnalysisResponse,
    summary="Structured GitHub repository analysis",
    description=(
        "Extracts structured intelligence from a GitHub repository without AI: "
        "languages, tech stack, complexity score, project type, commit count, "
        "repo size, and README content. Returns clean JSON."
    ),
)
async def repo_analysis(request: RepoAnalysisRequest) -> RepoAnalysisResponse:
    """
    **GitHub Repository Analyzer**

    Example request:
    ```json
    { "repo_url": "https://github.com/tiangolo/fastapi" }
    ```

    Example response:
    ```json
    {
      "languages": ["Python"],
      "tech_stack": ["FastAPI", "Python", "Pydantic", "pytest"],
      "complexity": "High",
      "project_type": "Library / Package",
      "commit_count": 3800,
      "repo_size_kb": 12400,
      ...
    }
    ```
    """
    # ── 1. Run the full analyzer ─────────────────────────────
    try:
        analysis = analyze_repository(request.repo_url)
    except ValueError as e:
        # Bad URL or 404
        code = status.HTTP_404_NOT_FOUND if "not found" in str(e).lower() else status.HTTP_422_UNPROCESSABLE_ENTITY
        raise HTTPException(status_code=code, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"GitHub API error: {e}"
        )

    # ── 2. Convert dataclass → Pydantic response model ───────
    data = analysis.to_dict()

    return RepoAnalysisResponse(
        languages    = data["languages"],
        tech_stack   = data["tech_stack"],
        complexity   = data["complexity"],
        project_type = data["project_type"],
        name         = data["name"],
        full_name    = data["full_name"],
        url          = data["url"],
        description  = data["description"],
        stars        = data["stars"],
        forks        = data["forks"],
        open_issues  = data["open_issues"],
        commit_count = data["commit_count"],
        repo_size_kb = data["repo_size_kb"],
        topics       = data["topics"],
        license      = data["license"],
        default_branch = data["default_branch"],
        language_bytes = data["language_bytes"],
        readme_preview = data["readme_preview"],
    )
