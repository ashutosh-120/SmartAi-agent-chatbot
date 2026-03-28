"""
models/schemas.py - Pydantic request & response schemas
Defines the shape of all API request bodies and responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, List


# ──────────────────────────────────────────
#  Chat Schemas
# ──────────────────────────────────────────

class ChatMessage(BaseModel):
    """A single message in the conversation history."""
    role: str = Field(..., description="Either 'user' or 'model'")
    content: str = Field(..., description="The message text")


class ChatRequest(BaseModel):
    """Request body for the /api/chat endpoint."""
    message: str = Field(..., min_length=1, description="The user's message")
    history: Optional[List[ChatMessage]] = Field(
        default=[],
        description="Previous conversation turns for multi-turn context"
    )


class ChatResponse(BaseModel):
    """Response from the /api/chat endpoint."""
    reply: str = Field(..., description="The AI-generated reply")
    model: str = Field(..., description="The Gemini model used")


# ──────────────────────────────────────────
#  GitHub Analysis Schemas
# ──────────────────────────────────────────

class GitHubRequest(BaseModel):
    """Request body for the /api/github/analyze endpoint."""
    repo_url: str = Field(
        ...,
        description="Full GitHub repo URL, e.g. https://github.com/owner/repo"
    )
    question: Optional[str] = Field(
        default="Give me a comprehensive summary of this repository.",
        description="Custom question to ask about the repository"
    )


class GitHubRepoInfo(BaseModel):
    """Metadata fetched from the GitHub API."""
    name: str
    full_name: str
    description: Optional[str]
    language: Optional[str]
    stars: int
    forks: int
    open_issues: int
    topics: List[str]
    license: Optional[str]
    url: str
    default_branch: str


class GitHubResponse(BaseModel):
    """Response from the /api/github/analyze endpoint."""
    repo_info: GitHubRepoInfo
    ai_analysis: str = Field(..., description="Gemini's analysis of the repository")
    readme_preview: Optional[str] = Field(
        default=None,
        description="First 500 characters of the README"
    )


# ──────────────────────────────────────────
#  GitHub Repo Analyzer Schemas (Prompt-3)
# ──────────────────────────────────────────

class RepoAnalysisRequest(BaseModel):
    """Request body for the POST /api/github/repo-analysis endpoint."""
    repo_url: str = Field(
        ...,
        description="Full GitHub repository URL.",
        examples=["https://github.com/tiangolo/fastapi"]
    )


class RepoAnalysisResponse(BaseModel):
    """
    Structured analysis result from the GitHub Repo Analyzer.
    Contains all extracted and derived intelligence fields.
    """
    # ── Core requested fields ──────────────────
    languages:    List[str] = Field(..., description="Programming languages detected, ordered by usage.")
    tech_stack:   List[str] = Field(..., description="Frameworks, tools, and technologies detected.")
    complexity:   str       = Field(..., description="Estimated complexity: Low | Medium | High | Very High.")
    project_type: str       = Field(..., description="Inferred project category (e.g. REST API / Backend).")

    # ── Repository identity ─────────────────────
    name:           str           = Field(..., description="Repository name.")
    full_name:      str           = Field(..., description="owner/repo slugged name.")
    url:            str           = Field(..., description="GitHub URL.")
    description:    Optional[str] = Field(default=None)

    # ── Stats ───────────────────────────────────
    stars:          int = Field(default=0, description="Star count.")
    forks:          int = Field(default=0, description="Fork count.")
    open_issues:    int = Field(default=0, description="Open issues count.")
    commit_count:   int = Field(default=0, description="Estimated total commit count.")
    repo_size_kb:   int = Field(default=0, description="Repository size in kilobytes.")

    # ── Details ─────────────────────────────────
    topics:         List[str]     = Field(default_factory=list, description="GitHub topics/tags.")
    license:        Optional[str] = Field(default=None, description="SPDX license identifier.")
    default_branch: str           = Field(default="main")
    language_bytes: dict          = Field(default_factory=dict, description="Language → bytes of code.")
    readme_preview: Optional[str] = Field(default=None, description="First 800 chars of README.")


# ──────────────────────────────────────────
#  Skill Extraction Schemas (Prompt-4)
# ──────────────────────────────────────────

class SkillExtractionRequest(BaseModel):
    """Request body for POST /api/github/skills."""
    repo_url: str = Field(
        ...,
        description="Full GitHub repository URL.",
        examples=["https://github.com/tiangolo/fastapi"]
    )


class SkillExtractionResponse(BaseModel):
    """
    Skill profile derived from a GitHub repository.
    Core fields: skills list and skill_level string.
    """
    # ── Core requested fields ──────────────────────────
    skills:       List[str] = Field(..., description="All detected skills, sorted alphabetically.")
    skill_level:  str       = Field(..., description="beginner | intermediate | advanced")

    # ── Supporting context ──────────────────────────────
    skill_score:  int   = Field(default=0, description="Raw additive score behind skill_level.")
    total_skills: int   = Field(default=0, description="Total number of skills detected.")
    categories:   dict  = Field(default_factory=dict, description="Skills grouped by category.")
    languages:    List[str] = Field(default_factory=list, description="Programming languages detected.")
    frameworks:   List[str] = Field(default_factory=list, description="Frameworks and tools detected.")
    project_type: str   = Field(default="Unknown", description="Inferred project type.")
    complexity:   str   = Field(default="Unknown", description="Repo complexity rating.")
    repo:         str   = Field(default="", description="owner/repo name.")
    url:          str   = Field(default="", description="GitHub URL.")
