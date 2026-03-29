"""
services/github_service.py - GitHub Repository Analyzer Module
────────────────────────────────────────────────────────────────
A fully modular, reusable GitHub REST API client.

Public API (import and call these anywhere):
  parse_github_url(url)          → (owner, repo)
  fetch_repo_data(owner, repo)   → raw metadata dict (basic)
  analyze_repository(url)        → RepoAnalysis (full structured result)

analyze_repository() is the main entry point for the analyzer feature.
It calls multiple focused sub-functions internally:
  _fetch_repo_meta()    → core repo metadata
  _fetch_languages()    → language bytes breakdown
  _fetch_commit_count() → total commit count via contributor stats
  _fetch_readme()       → decoded README text
  _detect_tech_stack()  → list of frameworks/tools from language + topics + README
  _classify_project()   → project_type from metadata signals
  _score_complexity()   → "Low" / "Medium" / "High" / "Very High"
"""

from __future__ import annotations

import base64
import logging
import re
import concurrent.futures
from dataclasses import dataclass, field
from typing import Optional, List

import httpx

from config import settings

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────
#  Constants
# ──────────────────────────────────────────────────────────────

_GITHUB_API = settings.GITHUB_API_BASE  # "https://api.github.com"

# Tech-stack keyword map: {keyword → framework/tool label}
# Checked against: primary language, topics, README text (lowercased)
_TECH_KEYWORDS: dict[str, str] = {
    # Python ecosystem
    "fastapi": "FastAPI", "flask": "Flask", "django": "Django",
    "sqlalchemy": "SQLAlchemy", "celery": "Celery", "pydantic": "Pydantic",
    "pytest": "pytest", "uvicorn": "Uvicorn",
    # JS/TS ecosystem
    "react": "React", "next.js": "Next.js", "nextjs": "Next.js",
    "vue": "Vue.js", "nuxt": "Nuxt.js", "angular": "Angular",
    "svelte": "Svelte", "express": "Express.js", "nestjs": "NestJS",
    "typescript": "TypeScript", "vite": "Vite", "webpack": "Webpack",
    "tailwind": "Tailwind CSS", "graphql": "GraphQL",
    # Mobile
    "flutter": "Flutter", "react native": "React Native",
    "react-native": "React Native", "kotlin": "Kotlin", "swift": "Swift",
    # Databases
    "postgresql": "PostgreSQL", "postgres": "PostgreSQL",
    "mongodb": "MongoDB", "redis": "Redis", "mysql": "MySQL",
    "sqlite": "SQLite", "elasticsearch": "Elasticsearch",
    # DevOps / infra
    "docker": "Docker", "kubernetes": "Kubernetes", "k8s": "Kubernetes",
    "terraform": "Terraform", "ansible": "Ansible", "nginx": "Nginx",
    "github actions": "GitHub Actions", "ci/cd": "CI/CD",
    # AI / ML
    "tensorflow": "TensorFlow", "pytorch": "PyTorch", "keras": "Keras",
    "scikit-learn": "scikit-learn", "sklearn": "scikit-learn",
    "langchain": "LangChain", "openai": "OpenAI", "gemini": "Gemini AI",
    "huggingface": "Hugging Face", "transformers": "Transformers",
    # Cloud
    "aws": "AWS", "azure": "Azure", "gcp": "Google Cloud",
}

# Project-type signals
_PROJECT_TYPE_RULES: list[tuple[list[str], str]] = [
    # (keywords to check in topics + description + readme, project_type label)
    (["api", "rest", "restful", "fastapi", "flask", "express", "backend"], "REST API / Backend"),
    (["fullstack", "full-stack", "full stack", "frontend + backend"],        "Full-Stack Web App"),
    (["react", "vue", "angular", "svelte", "next.js", "frontend", "ui"],    "Frontend / Web UI"),
    (["mobile", "android", "ios", "flutter", "react native", "swift"],      "Mobile App"),
    (["machine learning", "deep learning", "ml", "ai", "neural", "llm"],    "AI / Machine Learning"),
    (["data", "analytics", "notebook", "jupyter", "pandas", "visualization"],"Data Science / Analytics"),
    (["cli", "command-line", "terminal", "script", "tool", "utility"],       "CLI Tool / Utility"),
    (["library", "package", "sdk", "framework", "plugin"],                  "Library / Package"),
    (["discord", "telegram", "slack", "bot", "chatbot"],                    "Bot / Automation"),
    (["infra", "devops", "docker", "kubernetes", "terraform", "deploy"],    "DevOps / Infrastructure"),
    (["game", "gaming", "unity", "pygame", "phaser"],                       "Game"),
    (["docs", "documentation", "wiki", "tutorial", "guide"],                "Documentation / Tutorial"),
]


# ──────────────────────────────────────────────────────────────
#  Data Class — the final structured result
# ──────────────────────────────────────────────────────────────

@dataclass
class RepoAnalysis:
    """
    Fully structured result from analyze_repository().
    All fields map directly to the JSON response shape.
    """
    # Core identifiers
    name:           str = ""
    full_name:      str = ""
    url:            str = ""
    description:    Optional[str] = None

    # Requested structured fields
    languages:      list[str] = field(default_factory=list)   # e.g. ["Python", "JavaScript"]
    tech_stack:     list[str] = field(default_factory=list)   # e.g. ["FastAPI", "React", "Docker"]
    complexity:     str       = "Unknown"                     # "Low" | "Medium" | "High" | "Very High"
    project_type:   str       = "Unknown"                     # e.g. "REST API / Backend"

    # Language details (bytes per language)
    language_bytes: dict[str, int] = field(default_factory=dict)

    # Extra metadata
    stars:          int           = 0
    forks:          int           = 0
    open_issues:    int           = 0
    commit_count:   int           = 0
    repo_size_kb:   int           = 0   # size in KB (from GitHub API)
    topics:         list[str]     = field(default_factory=list)
    license:        Optional[str] = None
    default_branch: str           = "main"
    readme:         Optional[str] = None   # full README text

    def to_dict(self) -> dict:
        """Convert to the clean JSON response dictionary."""
        return {
            # ── Primary requested fields ──
            "languages":    self.languages,
            "tech_stack":   self.tech_stack,
            "complexity":   self.complexity,
            "project_type": self.project_type,

            # ── Repository metadata ────────
            "name":           self.name,
            "full_name":      self.full_name,
            "url":            self.url,
            "description":    self.description,
            "stars":          self.stars,
            "forks":          self.forks,
            "open_issues":    self.open_issues,
            "commit_count":   self.commit_count,
            "repo_size_kb":   self.repo_size_kb,
            "topics":         self.topics,
            "license":        self.license,
            "default_branch": self.default_branch,

            # ── Language detail ──────────
            "language_bytes": self.language_bytes,

            # ── README (truncated for API response) ──
            "readme_preview": (self.readme or "")[:800] + ("..." if self.readme and len(self.readme) > 800 else ""),
        }


# ──────────────────────────────────────────────────────────────
#  Multi-Repo Analysis (User Profile)
# ──────────────────────────────────────────────────────────────

def analyze_user_repos(username: str, max_repos: int = 10) -> List[RepoAnalysis]:
    """
    Fetch and analyze all public repositories for a GitHub username.
    Uses parallel processing to speed up analysis of multiple repos.

    Args:
        username: GitHub username (e.g., "ashutosh-120")
        max_repos: Maximum number of original repositories to analyze.

    Returns:
        A list of RepoAnalysis objects.
    """
    logger.info("Analyzing user profile: %s", username)
    
    with httpx.Client(timeout=30.0) as client:
        # ── 1. Fetch user's repositories ────────────────────
        url = f"{_GITHUB_API}/users/{username}/repos"
        resp = client.get(url, headers=_headers(), params={"sort": "updated", "per_page": 60})
        
        if resp.status_code == 404:
            raise ValueError(f"GitHub user '{username}' not found.")
        resp.raise_for_status()
        
        repos_data = resp.json()
        
        # Filter: Original repos only (optional), sorted by size/stars for maximum intelligence
        # We focus on non-forks to see the user's actual work
        original_repos = [r for r in repos_data if not r.get("fork")]
        # If no original repos, fall back to anything they have
        target_repos = original_repos if original_repos else repos_data
        # Take the top N most significant repos
        target_repos = target_repos[:max_repos]
        
    logger.info("Found %d repos for user %s. Starting parallel analysis...", len(target_repos), username)
    
    # ── 2. Parallel analysis ─────────────────────────────
    results: List[RepoAnalysis] = []
    
    # Use a ThreadPoolExecutor for I/O bound GitHub API calls
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        # Create a mapping of future to repo name for error tracking
        future_to_url = {
            executor.submit(analyze_repository, r["html_url"]): r["html_url"] 
            for r in target_repos
        }
        
        for future in concurrent.futures.as_completed(future_to_url):
            repo_url = future_to_url[future]
            try:
                analysis = future.result()
                results.append(analysis)
            except Exception as e:
                logger.error("Failed to analyze repo %s: %s", repo_url, e)
                
    return results


# ──────────────────────────────────────────────────────────────
#  Shared HTTP helpers
# ──────────────────────────────────────────────────────────────

def _headers() -> dict:
    """Build GitHub API authorization headers."""
    h = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if settings.GITHUB_TOKEN:
        h["Authorization"] = f"Bearer {settings.GITHUB_TOKEN}"
    return h


# ──────────────────────────────────────────────────────────────
#  URL Parser (public, reusable)
# ──────────────────────────────────────────────────────────────

def parse_github_url(url: str) -> tuple[str, str]:
    """
    Parse any GitHub URL variant into (owner, repo).

    Accepts:
      https://github.com/owner/repo
      https://github.com/owner/repo.git
      github.com/owner/repo
      owner/repo  (shorthand)
    """
    url = url.strip().rstrip("/").replace(".git", "")
    if "://" in url:
        url = url.split("://", 1)[1]

    parts = [p for p in url.split("/") if p]

    if "github.com" in parts[0]:
        if len(parts) < 3:
            # It's likely a profile URL like github.com/owner
            raise ValueError(
                f"The URL '{url}' appears to be a GitHub profile. "
                "Please provide a specific REPOSITORY URL (e.g., https://github.com/owner/repo) "
                "so we can analyze the code."
            )
        return parts[1], parts[2]

    # Shorthand: "owner/repo"
    if len(parts) == 2:
        return parts[0], parts[1]

    raise ValueError(
        f"Invalid GitHub URL format: '{url}'. "
        "Please use the standard format: https://github.com/owner/repo"
    )


# ──────────────────────────────────────────────────────────────
#  Sub-fetchers (each does one focused API call)
# ──────────────────────────────────────────────────────────────

def _fetch_repo_meta(client: httpx.Client, owner: str, repo: str) -> dict:
    """Fetch core repository metadata from GET /repos/{owner}/{repo}."""
    resp = client.get(f"{_GITHUB_API}/repos/{owner}/{repo}", headers=_headers())
    if resp.status_code == 404:
        raise ValueError(
            f"Repository '{owner}/{repo}' not found. "
            "Make sure the URL is correct and the repository is public."
        )
    if resp.status_code == 403:
        raise PermissionError(
            "GitHub API access denied. Check your GITHUB_TOKEN in .env."
        )
    resp.raise_for_status()
    return resp.json()


def _fetch_languages(client: httpx.Client, owner: str, repo: str) -> dict[str, int]:
    """
    Fetch programming language breakdown from GET /repos/{owner}/{repo}/languages.
    Returns {language_name: bytes_of_code} e.g. {"Python": 34251, "JavaScript": 9823}
    """
    resp = client.get(
        f"{_GITHUB_API}/repos/{owner}/{repo}/languages", headers=_headers()
    )
    if resp.status_code == 200:
        return resp.json()
    return {}


def _fetch_commit_count(client: httpx.Client, owner: str, repo: str) -> int:
    """
    Estimate total commit count using the contributor stats endpoint.
    Falls back to a per-page HEAD request trick if stats aren't ready.
    Returns 0 if the count cannot be determined.
    """
    # Strategy 1: Sum contributor total commits
    stats_resp = client.get(
        f"{_GITHUB_API}/repos/{owner}/{repo}/contributors",
        headers=_headers(),
        params={"per_page": 1, "anon": "true"},
    )
    if stats_resp.status_code == 200:
        # GitHub returns Link header with last page number = contributor count
        link = stats_resp.headers.get("Link", "")
        # Try to get total commit count via commits endpoint pagination
        commits_resp = client.get(
            f"{_GITHUB_API}/repos/{owner}/{repo}/commits",
            headers=_headers(),
            params={"per_page": 1},
        )
        if commits_resp.status_code == 200:
            link_header = commits_resp.headers.get("Link", "")
            # The `last` rel gives us the total pages (each = 1 commit)
            match = re.search(r'page=(\d+)>;\s*rel="last"', link_header)
            if match:
                return int(match.group(1))

    # Strategy 2: Use the participation stats if available
    participation = client.get(
        f"{_GITHUB_API}/repos/{owner}/{repo}/stats/participation",
        headers=_headers(),
    )
    if participation.status_code == 200:
        data = participation.json()
        # 'all' is 52 weekly counts; sum them as approximate
        return sum(data.get("all", []))

    return 0


def _fetch_readme(client: httpx.Client, owner: str, repo: str) -> Optional[str]:
    """
    Fetch and decode the repository README from GET /repos/{owner}/{repo}/readme.
    Returns decoded UTF-8 text or None if no README exists.
    """
    resp = client.get(
        f"{_GITHUB_API}/repos/{owner}/{repo}/readme", headers=_headers()
    )
    if resp.status_code != 200:
        return None
    data = resp.json()
    encoded = data.get("content", "")
    if not encoded:
        return None
    return base64.b64decode(encoded).decode("utf-8", errors="replace")


# ──────────────────────────────────────────────────────────────
#  Intelligence layer (pure functions, no HTTP)
# ──────────────────────────────────────────────────────────────

def _detect_tech_stack(
    primary_language: Optional[str],
    topics: list[str],
    readme: Optional[str],
    language_bytes: dict[str, int],
) -> list[str]:
    """
    Detect frameworks, tools, and technologies from available signals:
      1. Primary language AND all languages in the repo
      2. GitHub topics
      3. README text (first 3000 chars)

    Returns a deduplicated, sorted list of detected tech names.
    """
    detected: set[str] = set()
    search_corpus = ""

    # Build a unified lowercase search corpus
    if primary_language:
        search_corpus += f" {primary_language.lower()}"
    for lang in language_bytes:
        search_corpus += f" {lang.lower()}"
    for topic in topics:
        search_corpus += f" {topic.lower()}"
    if readme:
        search_corpus += f" {readme[:3000].lower()}"

    for keyword, label in _TECH_KEYWORDS.items():
        if keyword in search_corpus:
            detected.add(label)

    # Always include the primary language itself in tech_stack
    if primary_language and primary_language not in detected:
        detected.add(primary_language)
    for lang in language_bytes:
        if lang not in detected:
            detected.add(lang)

    return sorted(detected)


def _classify_project(
    description: Optional[str],
    topics: list[str],
    readme: Optional[str],
    languages: list[str],
) -> str:
    """
    Classify the project type based on metadata signals.
    Checks description, topics, and README against known rule patterns.
    Returns a human-readable project type string.
    """
    corpus = " ".join(filter(None, [
        (description or "").lower(),
        " ".join(topics).lower(),
        (readme or "")[:2000].lower(),
        " ".join(languages).lower(),
    ]))

    for keywords, project_type in _PROJECT_TYPE_RULES:
        if any(kw in corpus for kw in keywords):
            return project_type

    return "General Software Project"


def _score_complexity(
    repo_size_kb: int,
    commit_count: int,
    language_count: int,
    open_issues: int,
    forks: int,
    stars: int,
) -> str:
    """
    Score the repository complexity as Low / Medium / High / Very High.

    Scoring model (additive points):
      • Repo size  → 0-3 pts
      • Commits    → 0-3 pts
      • Languages  → 0-2 pts
      • Issues     → 0-1 pt
      • Community  → 0-1 pt (forks + stars)
    """
    score = 0

    # Repository size (KB)
    if repo_size_kb > 50_000:   score += 3   # > 50 MB
    elif repo_size_kb > 10_000: score += 2   # > 10 MB
    elif repo_size_kb > 1_000:  score += 1   # > 1 MB

    # Commit history depth
    if commit_count > 2_000:   score += 3
    elif commit_count > 500:   score += 2
    elif commit_count > 50:    score += 1

    # Number of programming languages used
    if language_count >= 5:    score += 2
    elif language_count >= 3:  score += 1

    # Open issues as proxy for active, complex project
    if open_issues > 100:      score += 1

    # Community engagement
    if (stars + forks) > 1_000: score += 1

    # Map score → label
    if score >= 8:   return "Very High"
    if score >= 5:   return "High"
    if score >= 2:   return "Medium"
    return "Low"


# ──────────────────────────────────────────────────────────────
#  Main Public Entrypoint
# ──────────────────────────────────────────────────────────────

def analyze_repository(repo_url: str) -> RepoAnalysis:
    """
    Full GitHub repository analysis.

    Fetches all available data from the GitHub REST API and derives
    structured intelligence fields (tech_stack, complexity, project_type).

    Args:
        repo_url: Any GitHub repository URL (see parse_github_url for formats).

    Returns:
        RepoAnalysis dataclass with all fields populated.
        Call .to_dict() to get the clean JSON-serializable dictionary.

    Raises:
        ValueError:       If the URL is invalid or the repo is not found.
        PermissionError:  If the GitHub token lacks access.
        httpx.HTTPError:  On network failures.
    """
    owner, repo_name = parse_github_url(repo_url)
    logger.info("Analyzing repository: %s/%s", owner, repo_name)

    with httpx.Client(timeout=40.0) as client:
        # ── 1. Core metadata (required) ────────────────────
        meta = _fetch_repo_meta(client, owner, repo_name)

        # ── 2. Languages breakdown ──────────────────────────
        language_bytes = _fetch_languages(client, owner, repo_name)

        # ── 3. Commit count ────────────────────────────────
        commit_count = _fetch_commit_count(client, owner, repo_name)

        # ── 4. README ──────────────────────────────────────
        readme = _fetch_readme(client, owner, repo_name)

    # ── Extract clean values from metadata ─────────────────
    license_name: Optional[str] = None
    if meta.get("license"):
        license_name = (
            meta["license"].get("spdx_id") or meta["license"].get("name")
        )

    topics:         list[str] = meta.get("topics", [])
    primary_lang:   Optional[str] = meta.get("language")
    stars:          int = meta.get("stargazers_count", 0)
    forks:          int = meta.get("forks_count", 0)
    open_issues:    int = meta.get("open_issues_count", 0)
    repo_size_kb:   int = meta.get("size", 0)      # GitHub reports in KB
    description:    Optional[str] = meta.get("description")

    # Ordered list of languages by usage (most bytes first)
    languages: list[str] = [
        lang for lang, _ in sorted(language_bytes.items(), key=lambda x: x[1], reverse=True)
    ]

    # ── Run intelligence functions ──────────────────────────
    tech_stack   = _detect_tech_stack(primary_lang, topics, readme, language_bytes)
    project_type = _classify_project(description, topics, readme, languages)
    complexity   = _score_complexity(
        repo_size_kb=repo_size_kb,
        commit_count=commit_count,
        language_count=len(languages),
        open_issues=open_issues,
        forks=forks,
        stars=stars,
    )

    logger.info(
        "Analysis complete | %s/%s | langs=%d | commits=%d | complexity=%s | type=%s",
        owner, repo_name, len(languages), commit_count, complexity, project_type,
    )

    return RepoAnalysis(
        name=meta.get("name", repo_name),
        full_name=meta.get("full_name", f"{owner}/{repo_name}"),
        url=meta.get("html_url", repo_url),
        description=description,
        languages=languages,
        tech_stack=tech_stack,
        complexity=complexity,
        project_type=project_type,
        language_bytes=language_bytes,
        stars=stars,
        forks=forks,
        open_issues=open_issues,
        commit_count=commit_count,
        repo_size_kb=repo_size_kb,
        topics=topics,
        license=license_name,
        default_branch=meta.get("default_branch", "main"),
        readme=readme,
    )


# ──────────────────────────────────────────────────────────────
#  Legacy helper (kept for backward compatibility with routes/github.py)
# ──────────────────────────────────────────────────────────────

def fetch_repo_data(owner: str, repo: str) -> dict:
    """
    Backward-compatible wrapper used by routes/github.py AI analysis endpoint.
    Returns a plain dict (not RepoAnalysis) for the Gemini analyze_repo() call.
    """
    with httpx.Client(timeout=30.0) as client:
        meta = _fetch_repo_meta(client, owner, repo)
        readme = _fetch_readme(client, owner, repo)

        license_name = None
        if meta.get("license"):
            license_name = meta["license"].get("spdx_id") or meta["license"].get("name")

        return {
            "name":           meta.get("name"),
            "full_name":      meta.get("full_name"),
            "description":    meta.get("description"),
            "language":       meta.get("language"),
            "stars":          meta.get("stargazers_count", 0),
            "forks":          meta.get("forks_count", 0),
            "open_issues":    meta.get("open_issues_count", 0),
            "topics":         meta.get("topics", []),
            "license":        license_name,
            "url":            meta.get("html_url"),
            "default_branch": meta.get("default_branch", "main"),
            "readme":         readme,
        }
