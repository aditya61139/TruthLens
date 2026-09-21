import os
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.config import settings

router = APIRouter(prefix="/config", tags=["Configuration"])

class SetKeyRequest(BaseModel):
    google_api_key: str

@router.get("/status")
def get_api_keys_status():
    has_google_key = bool(settings.GOOGLE_API_KEY or settings.GEMINI_API_KEY)
    has_custom_search = bool((settings.GOOGLE_SEARCH_API_KEY or settings.GOOGLE_API_KEY) and settings.GOOGLE_SEARCH_ENGINE_ID)
    
    return {
        "status": "online",
        "model": settings.GEMINI_MODEL,
        "keys": {
            "google_api_key": has_google_key,
            "gemini_api_key": bool(settings.GEMINI_API_KEY or settings.GOOGLE_API_KEY),
            "factcheck_api_key": bool(settings.GOOGLE_FACTCHECK_API_KEY or settings.GOOGLE_API_KEY),
            "google_search_key": has_custom_search,
            "news_api_key": bool(settings.NEWS_API_KEY)
        },
        "capabilities": {
            "google_search_grounding": has_google_key,
            "gemini_fact_synthesis": has_google_key,
            "google_factcheck_tools_api": has_google_key,
            "google_custom_search": has_custom_search,
            "settled_knowledge_engine": True,
            "news_consensus_engine": True,
            "misinformation_pattern_nlp": True,
            "fuzzy_deduplication_cache": True
        }
    }

@router.post("/set-key")
def update_google_api_key(req: SetKeyRequest):
    key = req.google_api_key.strip()
    if not key:
        raise HTTPException(status_code=400, detail="API Key cannot be empty.")

    # Update runtime settings
    settings.GOOGLE_API_KEY = key
    settings.GEMINI_API_KEY = key
    settings.GOOGLE_FACTCHECK_API_KEY = key
    os.environ["GOOGLE_API_KEY"] = key
    os.environ["GEMINI_API_KEY"] = key
    os.environ["GOOGLE_FACTCHECK_API_KEY"] = key

    # Write to .env
    env_path = settings.BASE_DIR / ".env"
    try:
        lines = []
        if env_path.exists():
            with open(env_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        
        updated = False
        new_lines = []
        for line in lines:
            if line.startswith("GOOGLE_API_KEY="):
                new_lines.append(f"GOOGLE_API_KEY={key}\n")
                updated = True
            else:
                new_lines.append(line)

        if not updated:
            new_lines.append(f"GOOGLE_API_KEY={key}\n")

        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
    except Exception:
        pass

    return {
        "status": "success",
        "message": "Google API Key configured successfully! Live Google Search Grounding and Gemini Synthesis are now active.",
        "capabilities": {
            "google_search_grounding": True,
            "gemini_fact_synthesis": True,
            "google_factcheck_tools_api": True
        }
    }
