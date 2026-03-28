"""
services/skill_extractor.py — GitHub Repo Skill Extraction System
──────────────────────────────────────────────────────────────────
Standalone, fully modular system. Import and call from anywhere.

Public API:
  extract_skills(repo_url: str)          → SkillProfile
  extract_skills_from_data(data: dict)   → SkillProfile  (reuse existing data)

SkillProfile:
  .skills       → list[str]   — all detected skills
  .skill_level  → str         — "beginner" | "intermediate" | "advanced"
  .categories   → dict        — skills grouped by category
  .to_dict()    → dict        — clean JSON output

Design principles:
  • Simple rule tables (plain dicts/lists) — easy to extend
  • Each rule table is independent and readable
  • No external dependencies beyond standard library + existing services
  • All scoring is additive and transparent
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

from services.github_service import analyze_repository, RepoAnalysis

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════
#  RULE TABLES  (extend these to add new skills)
# ══════════════════════════════════════════════════════════════

# ── 1. Language → Skill Categories ────────────────────────────
# Format: { language: [skill, skill, ...] }
LANGUAGE_SKILL_MAP: dict[str, list[str]] = {
    # Backend / General
    "Python":     ["Python", "Backend Development", "Scripting"],
    "Java":       ["Java", "Backend Development", "Object-Oriented Programming"],
    "Go":         ["Go (Golang)", "Backend Development", "Systems Programming"],
    "Rust":       ["Rust", "Systems Programming", "Low-Level Programming"],
    "C":          ["C", "Systems Programming", "Low-Level Programming"],
    "C++":        ["C++", "Systems Programming", "Object-Oriented Programming"],
    "C#":         [".NET / C#", "Backend Development", "Object-Oriented Programming"],
    "PHP":        ["PHP", "Backend Development", "Web Development"],
    "Ruby":       ["Ruby", "Backend Development", "Web Development"],
    "Kotlin":     ["Kotlin", "Android Development", "JVM Development"],
    "Swift":      ["Swift", "iOS Development", "Mobile Development"],
    "Scala":      ["Scala", "Functional Programming", "JVM Development"],
    "Haskell":    ["Haskell", "Functional Programming"],
    "Elixir":     ["Elixir", "Backend Development", "Functional Programming"],

    # Frontend / Full-stack
    "JavaScript":  ["JavaScript", "Frontend Development", "Web Development"],
    "TypeScript":  ["TypeScript", "Frontend Development", "Web Development", "Type Systems"],
    "HTML":        ["HTML", "Frontend Development", "Web Development"],
    "CSS":         ["CSS", "Frontend Development", "UI/UX"],
    "Dart":        ["Dart", "Flutter", "Mobile Development"],

    # Data / ML
    "R":           ["R", "Data Science", "Statistical Analysis"],
    "Julia":       ["Julia", "Data Science", "Scientific Computing"],
    "MATLAB":      ["MATLAB", "Scientific Computing", "Data Analysis"],
    "Jupyter Notebook": ["Jupyter Notebooks", "Data Science", "Python"],

    # Infrastructure / DevOps
    "Shell":       ["Shell Scripting", "Linux / Unix", "DevOps"],
    "Bash":        ["Shell Scripting", "Linux / Unix", "DevOps"],
    "PowerShell":  ["PowerShell", "Windows Automation", "Scripting"],
    "HCL":         ["Terraform / HCL", "Infrastructure as Code", "DevOps"],
    "Dockerfile":  ["Docker", "Containerization", "DevOps"],

    # Other
    "SQL":         ["SQL", "Database Design", "Data Engineering"],
    "GraphQL":     ["GraphQL", "API Design"],
    "Solidity":    ["Solidity", "Smart Contracts", "Web3 / Blockchain"],
}

# ── 2. Framework / Tool → Skills ──────────────────────────────
# Matched against tech_stack list (case-insensitive substring match)
FRAMEWORK_SKILL_MAP: dict[str, list[str]] = {
    # Python web
    "FastAPI":     ["FastAPI", "REST API Development", "Async Programming"],
    "Flask":       ["Flask", "REST API Development", "Web Development"],
    "Django":      ["Django", "Full-Stack Web Development", "ORM / Database"],

    # Python ML/AI
    "TensorFlow":  ["TensorFlow", "Deep Learning", "Machine Learning", "AI/ML"],
    "PyTorch":     ["PyTorch",    "Deep Learning", "Machine Learning", "AI/ML"],
    "Keras":       ["Keras",      "Deep Learning", "Neural Networks"],
    "scikit-learn":["scikit-learn","Machine Learning", "Data Science"],
    "Pandas":      ["Pandas",     "Data Manipulation", "Data Science"],
    "NumPy":       ["NumPy",      "Scientific Computing", "Data Science"],
    "LangChain":   ["LangChain",  "LLM Integration", "AI/ML", "Prompt Engineering"],
    "Hugging Face":["Hugging Face","NLP / Transformers", "AI/ML"],

    # JS/TS web
    "React":       ["React",      "Frontend Development", "Component Architecture"],
    "Vue.js":      ["Vue.js",     "Frontend Development", "Component Architecture"],
    "Angular":     ["Angular",    "Frontend Development", "TypeScript"],
    "Next.js":     ["Next.js",    "Full-Stack Web Development", "SSR / SSG"],
    "Nuxt.js":     ["Nuxt.js",    "Full-Stack Web Development", "Vue.js"],
    "Svelte":      ["Svelte",     "Frontend Development"],
    "Express.js":  ["Express.js", "Backend Development", "Node.js"],
    "NestJS":      ["NestJS",     "Backend Development", "TypeScript"],

    # Mobile
    "Flutter":      ["Flutter",       "Cross-Platform Mobile", "Dart"],
    "React Native": ["React Native",  "Cross-Platform Mobile", "JavaScript"],

    # Databases
    "PostgreSQL":    ["PostgreSQL", "Database Design", "SQL"],
    "MongoDB":       ["MongoDB",    "NoSQL Databases", "Database Design"],
    "Redis":         ["Redis",      "Caching", "Database Design"],
    "MySQL":         ["MySQL",      "Database Design", "SQL"],
    "SQLite":        ["SQLite",     "Database Design", "SQL"],
    "Elasticsearch": ["Elasticsearch", "Search Engineering", "Database Design"],

    # DevOps / Cloud
    "Docker":          ["Docker",           "Containerization",      "DevOps"],
    "Kubernetes":      ["Kubernetes",        "Container Orchestration","DevOps"],
    "Terraform":       ["Terraform / HCL",  "Infrastructure as Code","DevOps"],
    "GitHub Actions":  ["GitHub Actions",   "CI/CD",                 "DevOps"],
    "AWS":             ["AWS",              "Cloud Computing",        "DevOps"],
    "Google Cloud":    ["Google Cloud",     "Cloud Computing"],
    "Azure":           ["Azure",            "Cloud Computing"],

    # APIs
    "GraphQL":         ["GraphQL",          "API Design"],
    "Gemini AI":       ["Gemini AI",        "LLM Integration", "AI/ML"],
    "OpenAI":          ["OpenAI API",       "LLM Integration", "AI/ML"],

    # Testing
    "pytest":          ["pytest",           "Unit Testing", "Test-Driven Development"],
    "Pydantic":        ["Pydantic",         "Data Validation", "Python"],
}

# ── 3. Project Type → Implied Skills ──────────────────────────
PROJECT_TYPE_SKILLS: dict[str, list[str]] = {
    "REST API / Backend":          ["API Design", "Backend Development", "HTTP / REST"],
    "Full-Stack Web App":          ["Full-Stack Development", "Web Development"],
    "Frontend / Web UI":           ["UI/UX", "Web Development", "Responsive Design"],
    "Mobile App":                  ["Mobile Development"],
    "AI / Machine Learning":       ["Machine Learning", "AI/ML", "Model Training"],
    "Data Science / Analytics":    ["Data Analysis", "Data Visualization", "Statistics"],
    "CLI Tool / Utility":          ["Command-Line Tools", "Scripting", "Unix/Linux"],
    "Library / Package":           ["Software Design", "API Design", "Open Source"],
    "Bot / Automation":            ["Automation", "Bot Development"],
    "DevOps / Infrastructure":     ["DevOps", "Infrastructure as Code", "CI/CD"],
    "Game":                        ["Game Development"],
    "Documentation / Tutorial":    ["Technical Writing", "Documentation"],
    "General Software Project":    ["Software Development"],
}

# ── 4. Skill → Broader Category (for grouping in output) ───────
SKILL_CATEGORIES: dict[str, str] = {
    # Languages
    "Python": "Languages", "JavaScript": "Languages", "TypeScript": "Languages",
    "Java": "Languages", "Go (Golang)": "Languages", "Rust": "Languages",
    "C": "Languages", "C++": "Languages", ".NET / C#": "Languages",
    "PHP": "Languages", "Ruby": "Languages", "Kotlin": "Languages",
    "Swift": "Languages", "Scala": "Languages", "R": "Languages",
    "Dart": "Languages", "SQL": "Languages", "Shell Scripting": "Languages",

    # Frameworks
    "FastAPI": "Frameworks", "Flask": "Frameworks", "Django": "Frameworks",
    "React": "Frameworks", "Vue.js": "Frameworks", "Angular": "Frameworks",
    "Next.js": "Frameworks", "Express.js": "Frameworks", "NestJS": "Frameworks",
    "Flutter": "Frameworks", "React Native": "Frameworks", "Svelte": "Frameworks",
    "TensorFlow": "Frameworks", "PyTorch": "Frameworks", "Keras": "Frameworks",
    "scikit-learn": "Frameworks", "LangChain": "Frameworks",

    # Domains
    "Backend Development": "Domain", "Frontend Development": "Domain",
    "Full-Stack Development": "Domain", "Full-Stack Web Development": "Domain",
    "Mobile Development": "Domain", "Machine Learning": "Domain",
    "Deep Learning": "Domain", "AI/ML": "Domain", "Data Science": "Domain",
    "DevOps": "Domain", "Cloud Computing": "Domain",
    "Game Development": "Domain", "Web3 / Blockchain": "Domain",

    # Practices
    "REST API Development": "Practices", "API Design": "Practices",
    "Database Design": "Practices", "CI/CD": "Practices",
    "Test-Driven Development": "Practices", "Infrastructure as Code": "Practices",
    "Containerization": "Practices", "HTTP / REST": "Practices",
    "Type Systems": "Practices", "Async Programming": "Practices",
    "Object-Oriented Programming": "Practices", "Functional Programming": "Practices",

    # Tools
    "Docker": "Tools", "Kubernetes": "Tools", "Terraform / HCL": "Tools",
    "GitHub Actions": "Tools", "AWS": "Tools", "Google Cloud": "Tools",
    "Azure": "Tools", "PostgreSQL": "Tools", "MongoDB": "Tools",
    "Redis": "Tools", "Elasticsearch": "Tools",
}


# ══════════════════════════════════════════════════════════════
#  Skill Level Scoring
# ══════════════════════════════════════════════════════════════

def _compute_skill_level(
    commit_count: int,
    stars: int,
    forks: int,
    repo_size_kb: int,
    language_count: int,
    framework_count: int,
    complexity: str,
) -> tuple[str, int]:
    """
    Compute skill level using an additive scoring model.

    Returns (skill_level: str, score: int) so callers can inspect the score.

    Scoring dimensions:
      • Commit history   — depth of involvement
      • Community signal — stars + forks = external validation
      • Repo size        — scope of the project
      • Breadth          — number of languages + frameworks used
      • Complexity       — derived from prompt-3 analysis
    """
    score = 0

    # ── Commit history (development experience) ────────────
    if commit_count >= 500:   score += 4
    elif commit_count >= 100: score += 3
    elif commit_count >= 30:  score += 2
    elif commit_count >= 5:   score += 1

    # ── Community signal (external validation) ─────────────
    community = stars + forks
    if community >= 1000:  score += 4
    elif community >= 100: score += 3
    elif community >= 10:  score += 2
    elif community >= 1:   score += 1

    # ── Repo size (scope / effort) ─────────────────────────
    if repo_size_kb >= 50_000:   score += 3
    elif repo_size_kb >= 10_000: score += 2
    elif repo_size_kb >= 1_000:  score += 1

    # ── Breadth of tech used ────────────────────────────────
    breadth = language_count + framework_count
    if breadth >= 10:  score += 3
    elif breadth >= 6: score += 2
    elif breadth >= 3: score += 1

    # ── Complexity bonus ────────────────────────────────────
    complexity_bonus = {"Low": 0, "Medium": 1, "High": 2, "Very High": 3}
    score += complexity_bonus.get(complexity, 0)

    # ── Map score to level ──────────────────────────────────
    if score >= 11:  level = "advanced"
    elif score >= 5: level = "intermediate"
    else:            level = "beginner"

    return level, score


# ══════════════════════════════════════════════════════════════
#  Core Extraction Function
# ══════════════════════════════════════════════════════════════

def _extract_from_analysis(analysis: RepoAnalysis) -> "SkillProfile":
    """
    Core extraction logic. Takes a RepoAnalysis object and derives a SkillProfile.
    Pure function — no I/O, easy to test.
    """
    skills: set[str] = set()

    # ── Step 1: Map languages → skills ──────────────────────
    for lang in analysis.languages:
        for skill in LANGUAGE_SKILL_MAP.get(lang, [lang]):
            skills.add(skill)

    # ── Step 2: Map frameworks/tools → skills ───────────────
    detected_frameworks: list[str] = []
    for item in analysis.tech_stack:
        for framework_key, framework_skills in FRAMEWORK_SKILL_MAP.items():
            if framework_key.lower() in item.lower():
                for skill in framework_skills:
                    skills.add(skill)
                detected_frameworks.append(framework_key)
                break

    # ── Step 3: Map project type → implied skills ────────────
    for project_skill in PROJECT_TYPE_SKILLS.get(analysis.project_type, []):
        skills.add(project_skill)

    # ── Step 4: Compute skill level ─────────────────────────
    skill_level, score = _compute_skill_level(
        commit_count   = analysis.commit_count,
        stars          = analysis.stars,
        forks          = analysis.forks,
        repo_size_kb   = analysis.repo_size_kb,
        language_count = len(analysis.languages),
        framework_count= len(detected_frameworks),
        complexity     = analysis.complexity,
    )

    # ── Step 5: Categorise skills ─────────────────────────────
    categories: dict[str, list[str]] = {}
    sorted_skills = sorted(skills)
    for skill in sorted_skills:
        cat = SKILL_CATEGORIES.get(skill, "Other")
        categories.setdefault(cat, []).append(skill)

    logger.info(
        "Skill extraction done | repo=%s | skills=%d | level=%s (score=%d)",
        analysis.full_name, len(skills), skill_level, score,
    )

    return SkillProfile(
        skills       = sorted_skills,
        skill_level  = skill_level,
        score        = score,
        categories   = categories,
        languages    = analysis.languages,
        frameworks   = sorted(set(detected_frameworks)),
        project_type = analysis.project_type,
        complexity   = analysis.complexity,
        full_name    = analysis.full_name,
        url          = analysis.url,
    )


# ══════════════════════════════════════════════════════════════
#  Result Dataclass
# ══════════════════════════════════════════════════════════════

@dataclass
class SkillProfile:
    """
    The result of skill extraction.
    Call .to_dict() for the clean JSON output.
    """
    # ── Core output (what the user requested) ────────────────
    skills:       list[str] = field(default_factory=list)
    skill_level:  str       = "beginner"   # beginner | intermediate | advanced

    # ── Enriched output ──────────────────────────────────────
    score:        int                  = 0
    categories:   dict[str, list[str]] = field(default_factory=dict)
    languages:    list[str]            = field(default_factory=list)
    frameworks:   list[str]            = field(default_factory=list)
    project_type: str                  = "Unknown"
    complexity:   str                  = "Unknown"
    full_name:    str                  = ""
    url:          str                  = ""

    def to_dict(self) -> dict:
        """Clean JSON-serializable output."""
        return {
            # ── Primary requested fields ──
            "skills":      self.skills,
            "skill_level": self.skill_level,

            # ── Supporting context ─────────
            "skill_score":  self.score,
            "categories":   self.categories,
            "languages":    self.languages,
            "frameworks":   self.frameworks,
            "project_type": self.project_type,
            "complexity":   self.complexity,
            "repo":         self.full_name,
            "url":          self.url,
            "total_skills": len(self.skills),
        }


# ══════════════════════════════════════════════════════════════
#  Public Entry Points
# ══════════════════════════════════════════════════════════════

def extract_skills(repo_url: str) -> SkillProfile:
    """
    Full pipeline: fetch repo from GitHub → analyze → extract skills.

    Args:
        repo_url: Any GitHub repository URL.

    Returns:
        SkillProfile with .skills list and .skill_level string.

    Raises:
        ValueError:      If the URL is invalid or repo not found.
        PermissionError: If GitHub token lacks access.
    """
    analysis = analyze_repository(repo_url)
    return _extract_from_analysis(analysis)


def extract_skills_from_data(
    languages: list[str],
    tech_stack: list[str],
    project_type: str,
    commit_count: int = 0,
    stars: int = 0,
    forks: int = 0,
    repo_size_kb: int = 0,
    complexity: str = "Medium",
    full_name: str = "",
    url: str = "",
) -> SkillProfile:
    """
    Extract skills from already-fetched data (no GitHub API call needed).
    Use this when you already have a RepoAnalysis or repo-analysis response.

    This makes the extractor reusable without hitting the GitHub API again.
    """
    # Build a minimal RepoAnalysis to reuse the core logic
    analysis = RepoAnalysis(
        languages    = languages,
        tech_stack   = tech_stack,
        project_type = project_type,
        commit_count = commit_count,
        stars        = stars,
        forks        = forks,
        repo_size_kb = repo_size_kb,
        complexity   = complexity,
        full_name    = full_name,
        url          = url,
    )
    return _extract_from_analysis(analysis)
