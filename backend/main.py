"""
main.py - FastAPI Application Entry Point
Configures CORS, registers all routes, and starts the server.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from routes import github
from routes.chat import router as chat_router, router_api as chat_api_router
from routes.skills import router as skills_router
from routes.analyze import router as analyze_router

# ──────────────────────────────────────────
#  Create the FastAPI application instance
# ──────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "A full-stack AI chatbot backend powered by Google Gemini. "
        "Supports multi-turn conversations and GitHub repository analysis."
    ),
    version="1.0.0",
    docs_url="/docs",       # Swagger UI at http://localhost:8000/docs
    redoc_url="/redoc",     # ReDoc UI at http://localhost:8000/redoc
)

# ──────────────────────────────────────────
#  CORS Middleware
#  Reads ALLOWED_ORIGINS from env for deployment flexibility
# ──────────────────────────────────────────
_default_origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
]
# In production, set ALLOWED_ORIGINS=https://your-app.vercel.app
_env_origins = [
    o.strip() for o in settings.ALLOWED_ORIGINS.split(",")
] if hasattr(settings, "ALLOWED_ORIGINS") and settings.ALLOWED_ORIGINS else []

# Auto-allow any .onrender.com domain for easier deployment
_render_origin_regex = r"https://.*\.onrender\.com"

app.add_middleware(
    CORSMiddleware,
    allow_origins=_default_origins + _env_origins,
    allow_origin_regex=_render_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────────────────────────────────────────
#  Register Routers
# ──────────────────────────────────────────
app.include_router(chat_router)      # POST /chat
app.include_router(chat_api_router)  # POST /api/chat
app.include_router(github.router)    # POST /api/github/*
app.include_router(skills_router)    # POST /api/github/skills
app.include_router(analyze_router)   # POST /analyze  ← main pipeline


# ──────────────────────────────────────────
#  Health Check Endpoint
# ──────────────────────────────────────────
@app.get("/", tags=["Health"], summary="Root health check")
async def root():
    """Returns a simple status message to confirm the server is running."""
    return JSONResponse(content={
        "status": "running",
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "simple_chat":      "POST /chat              — single prompt → Gemini reply",
            "multi_turn_chat":  "POST /api/chat          — full conversation history",
            "github_analyze":   "POST /api/github/analyze — AI-powered repo analysis",
        }
    })


@app.get("/health", tags=["Health"], summary="Detailed health check")
async def health():
    """Returns health status including API key configuration."""
    return JSONResponse(content={
        "status": "healthy",
        "gemini_configured": bool(settings.GEMINI_API_KEY),
        "github_token_configured": bool(settings.GITHUB_TOKEN),
        "model": settings.GEMINI_MODEL,
    })


# ──────────────────────────────────────────
#  Run with: uvicorn main:app --reload --port 8000
# ──────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
