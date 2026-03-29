"""
services/profile_aggregator.py — Aggregates multiple repository analyses into a single profile.
"""

from collections import Counter
from dataclasses import dataclass, field
from typing import List, Dict

from services.github_service import RepoAnalysis

@dataclass
class DeveloperProfile:
    """Unified developer profile aggregated from multiple repositories."""
    username:           str
    overall_score:      int = 0
    skill_level:        str = "beginner"
    total_repos:        int = 0
    total_stars:        int = 0
    total_commits:      int = 0
    primary_languages:  List[str] = field(default_factory=list)
    top_skills:         List[str] = field(default_factory=list)
    frameworks:         List[str] = field(default_factory=list)
    repo_breakdown:     List[Dict] = field(default_factory=list)
    skill_categories:   Dict[str, List[str]] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "username":          self.username,
            "overall_score":     self.overall_score,
            "skill_level":       self.skill_level,
            "total_repos":       self.total_repos,
            "total_stars":       self.total_stars,
            "total_commits":     self.total_commits,
            "primary_languages": self.primary_languages,
            "top_skills":        self.top_skills,
            "frameworks":        self.frameworks,
            "repo_breakdown":    self.repo_breakdown,
            "skill_categories":  self.skill_categories
        }

def aggregate_developer_profile(username: str, repo_analyses: List[RepoAnalysis]) -> DeveloperProfile:
    """
    Take a list of RepoAnalysis objects and aggregate them into a DeveloperProfile.
    """
    if not repo_analyses:
        return DeveloperProfile(username=username)

    total_stars = sum(r.stars for r in repo_analyses)
    total_commits = sum(r.commit_count for r in repo_analyses)
    total_repos = len(repo_analyses)

    # Aggregate languages (weighted by bytes if possible, but let's do a simple count for now)
    language_counts = Counter()
    for r in repo_analyses:
        for lang in r.languages:
            language_counts[lang] += 1
    
    primary_languages = [lang for lang, _ in language_counts.most_common(5)]

    # Aggregate tech stack (frameworks, tools)
    tech_counts = Counter()
    for r in repo_analyses:
        for tech in r.tech_stack:
            tech_counts[tech] += 1
    
    top_skills = [tech for tech, _ in tech_counts.most_common(10)]
    
    # We'll use a simplified version of the skill_extractor logic here or call it
    # For now, let's compute an overall score based on some weights
    all_scores = []
    # (This is a place-holder for more complex scoring logic)
    # We will refine the overall_score after updating skill_extractor.py
    
    repo_breakdown = [
        {
            "name": r.name,
            "url": r.url,
            "stars": r.stars,
            "languages": r.languages[:3],
            "type": r.project_type,
            "complexity": r.complexity
        } for r in repo_analyses
    ]

    return DeveloperProfile(
        username=username,
        total_repos=total_repos,
        total_stars=total_stars,
        total_commits=total_commits,
        primary_languages=primary_languages,
        top_skills=top_skills,
        repo_breakdown=repo_breakdown
    )
