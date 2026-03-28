"""
services/trend_matcher.py — Market Trend Matching Module
──────────────────────────────────────────────────────────
Compares extracted user skills against current industry trends.

Public API:
  match_trends(skills)          → TrendMatch dataclass
  get_skill_score(skills, matched) → int (0–100)
  get_all_trend_names()         → list[str]

To UPDATE trends: just edit the MARKET_TRENDS dict below.
Each trend entry has: required_skills, bonus_skills, career_paths, description.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import math

# ══════════════════════════════════════════════════════════════
#  MARKET TRENDS — Edit here to add/update/remove trends
#  Format:
#    "Trend Name": {
#        "required": [...] — core skills for this path
#        "bonus":    [...] — extra skills that boost matching
#        "careers":  [...] — job titles in this trend
#        "desc":     str   — short description
#    }
# ══════════════════════════════════════════════════════════════

MARKET_TRENDS: dict[str, dict] = {
    "AI / Machine Learning Engineer": {
        "required": [
            "Python", "Machine Learning", "Deep Learning", "AI/ML",
            "TensorFlow", "PyTorch", "scikit-learn", "Data Science",
        ],
        "bonus": [
            "LangChain", "Hugging Face", "NLP / Transformers",
            "Gemini AI", "OpenAI API", "Prompt Engineering",
            "Data Manipulation", "NumPy", "Pandas",
        ],
        "careers": [
            "ML Engineer", "AI Engineer", "Data Scientist",
            "Research Engineer", "NLP Engineer", "LLM Engineer",
        ],
        "desc": "High demand for AI/ML skills driven by LLMs and automation.",
    },

    "Full Stack Web Developer": {
        "required": [
            "JavaScript", "TypeScript", "React", "Backend Development",
            "Frontend Development", "REST API Development", "Database Design",
        ],
        "bonus": [
            "Next.js", "Node.js", "Express.js", "Vue.js",
            "PostgreSQL", "MongoDB", "Redis", "Docker", "HTML", "CSS",
        ],
        "careers": [
            "Full Stack Developer", "Web Developer",
            "Frontend Developer", "Backend Developer", "Node.js Developer",
        ],
        "desc": "Consistently one of the most in-demand developer roles globally.",
    },

    "Cloud / DevOps Engineer": {
        "required": [
            "Docker", "Kubernetes", "CI/CD", "DevOps",
            "Infrastructure as Code", "Linux / Unix",
        ],
        "bonus": [
            "AWS", "Google Cloud", "Azure", "Terraform / HCL",
            "GitHub Actions", "Shell Scripting", "Ansible",
            "Container Orchestration", "Monitoring / Observability",
        ],
        "careers": [
            "DevOps Engineer", "Cloud Engineer", "Platform Engineer",
            "SRE (Site Reliability Engineer)", "Infrastructure Engineer",
        ],
        "desc": "Cloud-native adoption driving massive demand for DevOps skills.",
    },

    "Mobile App Developer": {
        "required": [
            "Mobile Development", "Flutter", "React Native",
            "Dart", "JavaScript",
        ],
        "bonus": [
            "iOS Development", "Android Development",
            "Swift", "Kotlin", "Cross-Platform Mobile",
        ],
        "careers": [
            "Mobile Developer", "Flutter Developer",
            "React Native Developer", "iOS Developer", "Android Developer",
        ],
        "desc": "Mobile-first world keeps mobile dev in strong demand.",
    },

    "Data Engineer": {
        "required": [
            "Python", "SQL", "Database Design", "Data Science",
            "Data Analysis",
        ],
        "bonus": [
            "PostgreSQL", "MongoDB", "Elasticsearch", "Redis",
            "Pandas", "Data Engineering", "Data Pipelines",
            "Apache Spark", "Airflow",
        ],
        "careers": [
            "Data Engineer", "Analytics Engineer",
            "BI Developer", "Database Administrator",
        ],
        "desc": "Data infrastructure is foundational to every digital business.",
    },

    "Backend / API Developer": {
        "required": [
            "Python", "Backend Development", "REST API Development",
            "API Design", "Database Design",
        ],
        "bonus": [
            "FastAPI", "Django", "Flask", "Go (Golang)", "Java",
            "Node.js", "PostgreSQL", "Redis", "Docker",
            "Async Programming", "HTTP / REST",
        ],
        "careers": [
            "Backend Developer", "API Developer",
            "Python Developer", "Software Engineer", "Go Developer",
        ],
        "desc": "Every product needs a scalable backend — always in demand.",
    },

    "Web3 / Blockchain Developer": {
        "required": [
            "Solidity", "Web3 / Blockchain", "Smart Contracts",
        ],
        "bonus": [
            "JavaScript", "TypeScript", "Python",
            "Cryptography", "DeFi", "NFT",
        ],
        "careers": [
            "Blockchain Developer", "Smart Contract Engineer",
            "Web3 Developer", "DeFi Developer",
        ],
        "desc": "Growing niche with high pay and specialized skill requirements.",
    },

    "Game Developer": {
        "required": [
            "Game Development", "C++", "C#",
        ],
        "bonus": [
            ".NET / C#", "Python", "C",
            "Unity", "Unreal Engine", "OpenGL",
        ],
        "careers": [
            "Game Developer", "Unity Developer",
            "Unreal Engine Developer", "Graphics Programmer",
        ],
        "desc": "Gaming is a multi-billion dollar industry with growing indie scene.",
    },
}


# ══════════════════════════════════════════════════════════════
#  Result Dataclass
# ══════════════════════════════════════════════════════════════

@dataclass
class TrendMatch:
    """Result of matching user skills against market trends."""
    # ── Core requested fields ────────────────────────────────
    matched_skills:  list[str] = field(default_factory=list)
    missing_skills:  list[str] = field(default_factory=list)
    career_paths:    list[str] = field(default_factory=list)
    skill_score:     int       = 0      # 0–100
    confidence_score: float   = 0.0    # 0.0–1.0

    # ── Enriched fields ──────────────────────────────────────
    trend_matches:   dict[str, dict] = field(default_factory=dict)
    best_match:      Optional[str]   = None
    suggested_paths: list[dict]      = field(default_factory=list)  # [{name, match_pct, careers}]

    def to_dict(self) -> dict:
        return {
            "matched_skills":   self.matched_skills,
            "missing_skills":   self.missing_skills,
            "career_paths":     self.career_paths,
            "skill_score":      self.skill_score,
            "confidence_score": round(self.confidence_score, 2),
            "best_match":       self.best_match,
            "suggested_paths":  self.suggested_paths,
        }


# ══════════════════════════════════════════════════════════════
#  Core Matching Logic
# ══════════════════════════════════════════════════════════════

def match_trends(skills: list[str]) -> TrendMatch:
    """
    Compare a list of user skills against all market trends.

    Algorithm:
      For each trend:
        - required_hit  = # of required skills the user has
        - bonus_hit     = # of bonus skills the user has
        - match_score   = (required_hit / required_total) * 0.7
                        + min(bonus_hit / max(bonus_total,1), 1.0) * 0.3
      → Sort trends by match_score descending
      → matched_skills = union of all required+bonus skills user has
      → missing_skills = top-priority skills user is missing across top trends

    Args:
        skills: List of skill strings from the skill extractor.

    Returns:
        TrendMatch dataclass with full analysis.
    """
    skills_lower = {s.lower() for s in skills}

    all_matched:  set[str] = set()
    all_missing:  set[str] = set()
    all_careers:  set[str] = set()
    trend_scores: list[tuple[str, float, dict]] = []

    for trend_name, trend_data in MARKET_TRENDS.items():
        required = trend_data["required"]
        bonus    = trend_data["bonus"]

        req_hits   = [s for s in required if s.lower() in skills_lower]
        bonus_hits = [s for s in bonus    if s.lower() in skills_lower]
        req_misses = [s for s in required if s.lower() not in skills_lower]

        # Weighted match: required = 70%, bonus = 30%
        req_ratio   = len(req_hits) / len(required) if required else 0
        bonus_ratio = len(bonus_hits) / len(bonus) if bonus else 0
        match_score = req_ratio * 0.70 + bonus_ratio * 0.30

        trend_scores.append((trend_name, match_score, {
            "match_pct":  round(match_score * 100, 1),
            "matched":    req_hits + bonus_hits,
            "missing":    req_misses,
            "careers":    trend_data["careers"],
            "desc":       trend_data["desc"],
        }))

    # Sort by match score descending
    trend_scores.sort(key=lambda x: x[1], reverse=True)

    suggested_paths = []
    for trend_name, score, detail in trend_scores:
        # Add to matched/missing/careers if there's any match
        all_matched.update(detail["matched"])
        if score > 0:
            all_careers.update(detail["careers"])
        # Top 3 missing skills per trend (avoid repetition)
        for m in detail["missing"][:3]:
            if m.lower() not in skills_lower:
                all_missing.add(m)

        suggested_paths.append({
            "name":      trend_name,
            "match_pct": detail["match_pct"],
            "careers":   detail["careers"],
            "desc":      detail["desc"],
        })

    # Best match = highest-scoring trend
    best_match = trend_scores[0][0] if trend_scores else None
    best_score = trend_scores[0][1] if trend_scores else 0.0

    # Skill score 0–100 based on best match % + total skills breadth
    skill_score = get_skill_score(list(skills), list(all_matched))

    # Confidence = how strong the best match is (not just # of skills)
    confidence = min(best_score + (len(list(all_matched)) / max(len(skills), 1)) * 0.15, 1.0)

    return TrendMatch(
        matched_skills   = sorted(all_matched),
        missing_skills   = sorted(all_missing - all_matched)[:15],  # top 15 gaps
        career_paths     = sorted(all_careers),
        skill_score      = skill_score,
        confidence_score = round(confidence, 2),
        trend_matches    = {t[0]: t[2] for t in trend_scores},
        best_match       = best_match,
        suggested_paths  = suggested_paths[:5],  # top 5 career paths
    )


def get_skill_score(skills: list[str], matched_skills: list[str]) -> int:
    """
    Calculate a 0–100 skill score.

    Formula:
      base   = min(total_skills / 30, 1.0)  * 40  → breadth (max 40 pts)
      match  = (matched / max(total,1))     * 40  → market relevance (max 40 pts)
      bonus  = log2(1 + total) / log2(31)  * 20  → depth bonus (max 20 pts)
    """
    total   = len(skills)
    matched = len(matched_skills)

    base_score  = min(total / 30.0, 1.0) * 40
    match_score = (matched / max(total, 1)) * 40
    depth_bonus = (math.log2(1 + total) / math.log2(31)) * 20

    return min(round(base_score + match_score + depth_bonus), 100)


def get_all_trend_names() -> list[str]:
    """Return all available trend/career goal names."""
    return list(MARKET_TRENDS.keys())
