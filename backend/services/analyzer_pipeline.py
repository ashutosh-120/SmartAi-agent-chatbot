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
import json
import time
from dataclasses import dataclass, field
from typing import Optional, Any, List, Dict
from pydantic import BaseModel, Field

from services.github_service  import analyze_repository
from services.skill_extractor import extract_skills_from_data
from services.trend_matcher   import match_trends, get_all_trend_names
from services.gemini_service  import generate_roadmap, GeminiError
from database import get_db

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
    roadmap:          Any       = field(default_factory=dict) # Now JSON object

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
    Runs the complete 4-step analysis pipeline with Caching and Resilience.
    1. 📦 Fetch Data → 2. 🔍 Extract Skills → 3. 📊 Match Trends → 4. 🗺️ Create Roadmap
    """
    logger.info("Pipeline starting | url=%s | goal=%s", repo_url, career_goal)
    
    # ── Step 0: Check Cache (Supabase) ─────────────────────
    # Use provided goal or a generic one for matching
    effective_goal = career_goal or "Full Stack Web Developer"
    
    try:
        db = get_db()
        # Look for the last successful analysis for this repo URL 
        # (Normalization: strip and lowercase)
        norm_url = repo_url.strip().lower()
        cache_query = db.table("analyses")\
            .select("*")\
            .eq("repo_url", norm_url)\
            .order("created_at", desc=True)\
            .limit(1)\
            .execute()
        
        if cache_query.data:
            cached = cache_query.data[0]
            logger.info("Step 0 done | returning cached analysis for %s", repo_url)
            return AnalysisResult(
                skills           = cached.get("skills", []),
                matched_skills   = cached.get("skills", []), # Approximation
                missing_skills   = [],
                career_paths     = [cached.get("career_goal")] if cached.get("career_goal") else [],
                roadmap          = cached.get("roadmap_json", {}),
                skill_score      = cached.get("skill_score", 0),
                skill_level      = cached.get("skill_level", "beginner"),
                repo_name        = cached.get("repo_name", "Unknown"),
                repo_url         = cached.get("repo_url", repo_url),
                languages        = cached.get("languages", []),
                project_type     = "Cached Analysis",
                complexity       = "Previously Analyzed"
            )
    except Exception as e:
        logger.warning("Cache check failed (non-fatal): %s", e)

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
    # Resilience: Try up to 3 times with backoff if rate limited
    roadmap_data  = {}
    roadmap_error = None
    max_retries   = 3
    
    for attempt in range(max_retries):
        try:
            raw_roadmap = generate_roadmap(
                skills        = profile.skills,
                missing_skills= trend.missing_skills,
                career_goal   = effective_goal,
                skill_score   = trend.skill_score,
            )
            try:
                roadmap_data = json.loads(raw_roadmap)
                logger.info("Step 4 done | roadmap parsed successfully (attempt %d)", attempt + 1)
                break 
            except json.JSONDecodeError:
                logger.warning("Gemini returned invalid JSON for roadmap. Using raw string.")
                roadmap_data = {"raw_content": raw_roadmap, "error": "JSON parse failed"}
                break
        except GeminiError as e:
            if "429" in str(e) and attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2 
                logger.warning("Step 4 rate limited (429). Retrying in %ds...", wait_time)
                time.sleep(wait_time)
                continue
            
            roadmap_error = f"Roadmap generation failed: {e}"
            logger.warning("Step 4 failed (non-fatal): %s", e)
            break
        except Exception as e:
            roadmap_error = f"Unexpected roadmap error: {e}"
            logger.warning("Step 4 unexpected error (non-fatal): %s", e)
            break

    # ── Build and return AnalysisResult ────────────────────
    return AnalysisResult(
        skills           = profile.skills,
        matched_skills   = trend.matched_skills,
        missing_skills   = trend.missing_skills,
        career_paths     = trend.career_paths,
        roadmap          = roadmap_data,
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
