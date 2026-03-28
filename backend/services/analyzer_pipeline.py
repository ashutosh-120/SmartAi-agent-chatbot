"""
services/analyzer_pipeline.py — Full Analysis Orchestration Pipeline
──────────────────────────────────────────────────────────────────────
Connects all services into a single end-to-end pipeline.

Pipeline steps:
  1. analyze_repository(url)    → RepoAnalysis   (github_service)
  2. extract_skills_from_data() → SkillProfile   (skill_extractor)
  3. match_trends(skills)       → TrendMatch     (trend_matcher)
  4. generate_roadmap(...)      → str            (gemini_service)

Public API:
  run_full_analysis(repo_url, career_goal) → AnalysisResult
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

from services.github_service  import analyze_repository
from services.skill_extractor import extract_skills_from_data
from services.trend_matcher   import match_trends, get_all_trend_names
from services.gemini_service  import generate_roadmap, GeminiError

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════
#  Result Dataclass
# ══════════════════════════════════════════════════════════════

@dataclass
class AnalysisResult:
    """Complete analysis result combining all pipeline stages."""

    # ── Core response fields ────────────────────────────────
    skills:           list[str] = field(default_factory=list)
    matched_skills:   list[str] = field(default_factory=list)
    missing_skills:   list[str] = field(default_factory=list)
    career_paths:     list[str] = field(default_factory=list)
    roadmap:          str       = ""

    # ── Extended fields ─────────────────────────────────────
    skill_score:      int       = 0
    confidence_score: float     = 0.0
    skill_level:      str       = "beginner"
    skill_categories: dict      = field(default_factory=dict)
    suggested_paths:  list[dict]= field(default_factory=list)
    frameworks:       list[str] = field(default_factory=list)
    languages:        list[str] = field(default_factory=list)
    project_type:     str       = "Unknown"
    complexity:       str       = "Unknown"
    repo_name:        str       = ""
    repo_url:         str       = ""

    # ── Error tracking ──────────────────────────────────────
    roadmap_error:    Optional[str] = None   # Non-fatal: roadmap generation failed

    def to_dict(self) -> dict:
        """Clean JSON-serializable output matching the spec."""
        return {
            # ── Primary requested fields ──
            "skills":           self.skills,
            "matched_skills":   self.matched_skills,
            "missing_skills":   self.missing_skills,
            "career_paths":     self.career_paths,
            "roadmap":          self.roadmap,

            # ── Scoring ──────────────────
            "skill_score":      self.skill_score,
            "confidence_score": round(self.confidence_score, 2),
            "skill_level":      self.skill_level,

            # ── Enriched data ─────────────
            "skill_categories": self.skill_categories,
            "suggested_paths":  self.suggested_paths,
            "frameworks":       self.frameworks,
            "languages":        self.languages,
            "project_type":     self.project_type,
            "complexity":       self.complexity,
            "repo_name":        self.repo_name,
            "repo_url":         self.repo_url,

            # Pipeline metadata
            "roadmap_error":    self.roadmap_error,
        }


# ══════════════════════════════════════════════════════════════
#  Pipeline Orchestrator
# ══════════════════════════════════════════════════════════════

def run_full_analysis(
    repo_url: str,
    career_goal: Optional[str] = None,
) -> AnalysisResult:
    """
    Execute the complete analysis pipeline end-to-end.

    Steps:
      1. Fetch & analyze GitHub repository (languages, commits, README, etc.)
      2. Extract developer skills from repo data
      3. Match skills against market trends
      4. Generate a personalized roadmap with Gemini AI

    Args:
        repo_url:    GitHub repository URL.
        career_goal: Optional target career (e.g. "AI Engineer").
                     If not provided, uses the best trend match.

    Returns:
        AnalysisResult with all fields populated.

    Raises:
        ValueError:      Invalid URL or repo not found.
        PermissionError: GitHub token access denied.
        Exception:       Other GitHub API failures.
    """
    logger.info("Pipeline starting | url=%s | goal=%s", repo_url, career_goal)

    # ── Step 1: Analyze GitHub repository ──────────────────
    repo = analyze_repository(repo_url)
    logger.info("Step 1 done | repo=%s | langs=%d", repo.full_name, len(repo.languages))

    # ── Step 2: Extract skills from repo data ───────────────
    profile = extract_skills_from_data(
        languages    = repo.languages,
        tech_stack   = repo.tech_stack,
        project_type = repo.project_type,
        commit_count = repo.commit_count,
        stars        = repo.stars,
        forks        = repo.forks,
        repo_size_kb = repo.repo_size_kb,
        complexity   = repo.complexity,
        full_name    = repo.full_name,
        url          = repo.url,
    )
    logger.info("Step 2 done | skills=%d | level=%s", len(profile.skills), profile.skill_level)

    # ── Step 3: Match against market trends ─────────────────
    trend = match_trends(profile.skills)
    logger.info(
        "Step 3 done | matched=%d | missing=%d | score=%d",
        len(trend.matched_skills), len(trend.missing_skills), trend.skill_score
    )

    # ── Step 4: Generate roadmap with Gemini ────────────────
    # Use provided career_goal or fall back to best trend match
    effective_goal = career_goal or trend.best_match or "Full Stack Web Developer"
    roadmap_text   = ""
    roadmap_error  = None

    try:
        roadmap_text = generate_roadmap(
            skills        = profile.skills,
            missing_skills= trend.missing_skills,
            career_goal   = effective_goal,
            skill_score   = trend.skill_score,
            project_type  = repo.project_type,
        )
        logger.info("Step 4 done | roadmap_chars=%d", len(roadmap_text))
    except GeminiError as e:
        # Roadmap is non-fatal — return all other data even if Gemini fails
        roadmap_error = f"Roadmap generation failed: {e}"
        logger.warning("Step 4 failed (non-fatal): %s", e)
    except Exception as e:
        roadmap_error = f"Unexpected roadmap error: {e}"
        logger.warning("Step 4 unexpected error (non-fatal): %s", e)

    # ── Build and return AnalysisResult ────────────────────
    return AnalysisResult(
        skills           = profile.skills,
        matched_skills   = trend.matched_skills,
        missing_skills   = trend.missing_skills,
        career_paths     = trend.career_paths,
        roadmap          = roadmap_text,
        skill_score      = trend.skill_score,
        confidence_score = trend.confidence_score,
        skill_level      = profile.skill_level,
        skill_categories = profile.categories,
        suggested_paths  = trend.suggested_paths,
        frameworks       = profile.frameworks,
        languages        = repo.languages,
        project_type     = repo.project_type,
        complexity       = repo.complexity,
        repo_name        = repo.full_name,
        repo_url         = repo.url,
        roadmap_error    = roadmap_error,
    )
