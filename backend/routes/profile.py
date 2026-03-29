"""
backend/routes/profile.py - User Profile Analysis Routes
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Optional

from services.github_service import analyze_user_repos
from services.profile_aggregator import aggregate_developer_profile, DeveloperProfile

router = APIRouter(prefix="/profile", tags=["Profile"])
logger = logging.getLogger(__name__)

class ProfileAnalysisRequest(BaseModel):
    username: str
    max_repos: Optional[int] = 10

@router.post("/analyze")
async def analyze_profile(request: ProfileAnalysisRequest):
    """
    Perform a deep analysis across all public repositories for a GitHub user.
    """
    try:
        logger.info("Starting profile analysis for user: %s", request.username)
        # 1. Fetch and analyze individual repos in parallel
        repo_analyses = analyze_user_repos(request.username, max_repos=request.max_repos)
        
        if not repo_analyses:
            raise HTTPException(status_code=404, detail="No public repositories found for this user.")

        # 2. Aggregate into a unified developer profile
        profile = aggregate_developer_profile(request.username, repo_analyses)
        
        return profile.to_dict()

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception("Profile analysis failed")
        raise HTTPException(status_code=500, detail=f"Internal analysis error: {str(e)}")

@router.get("/{username}")
async def get_profile(username: str):
    """
    Get a previously analyzed profile (Stub for now, will use Supabase in Phase 2).
    """
    return {"message": f"Profile fetch for {username} is coming in Phase 2 with Supabase!"}
