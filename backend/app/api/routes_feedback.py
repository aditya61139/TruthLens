import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.database import get_db
from app.db.models import UserFeedback, ClaimHistory, QueryCache, PublisherCredibility

router = APIRouter(tags=["Feedback & Stats"])

class FeedbackRequest(BaseModel):
    claim_id: Optional[str] = Field(None, max_length=128)
    claim_text: str = Field(..., min_length=1, max_length=5000)
    given_verdict: str = Field(..., max_length=64)
    feedback_type: str = Field(..., max_length=32) # 'helpful' or 'incorrect'
    suggested_verdict: Optional[str] = Field(None, max_length=64)
    comments: Optional[str] = Field(None, max_length=2000)

@router.post("/feedback")
def submit_feedback(req: FeedbackRequest, db: Session = Depends(get_db)):
    if req.feedback_type not in ["helpful", "incorrect"]:
        raise HTTPException(status_code=400, detail="feedback_type must be 'helpful' or 'incorrect'")

    feedback = UserFeedback(
        claim_id=req.claim_id,
        claim_text=req.claim_text,
        given_verdict=req.given_verdict,
        feedback_type=req.feedback_type,
        suggested_verdict=req.suggested_verdict,
        comments=req.comments,
        created_at=datetime.datetime.now(datetime.timezone.utc)
    )
    db.add(feedback)
    db.commit()

    return {
        "status": "success",
        "message": "Thank you for helping improve TruthLens verification accuracy!"
    }

@router.get("/stats")
def get_system_stats(db: Session = Depends(get_db)):
    total_queries = db.query(ClaimHistory).count()
    cache_entries = db.query(QueryCache).count()
    cached_hits = db.query(func.sum(QueryCache.access_count)).scalar() or 0
    total_publishers = db.query(PublisherCredibility).count()
    
    # Feedback stats
    helpful_count = db.query(UserFeedback).filter(UserFeedback.feedback_type == "helpful").count()
    incorrect_count = db.query(UserFeedback).filter(UserFeedback.feedback_type == "incorrect").count()
    total_feedback = helpful_count + incorrect_count
    user_satisfaction_rate = round((helpful_count / total_feedback * 100.0), 1) if total_feedback > 0 else None

    # Verdict distribution
    history_verdicts = db.query(ClaimHistory.verdict, func.count(ClaimHistory.id)).group_by(ClaimHistory.verdict).all()
    verdict_dist = {v: count for v, count in history_verdicts}

    # Category distribution
    cat_counts = db.query(ClaimHistory.category, func.count(ClaimHistory.id)).group_by(ClaimHistory.category).all()
    category_dist = {c: count for c, count in cat_counts if c}

    return {
        "total_verifications": total_queries,
        "cache_entries": cache_entries,
        "total_cache_hits": int(cached_hits),
        "total_publishers_tracked": total_publishers,
        "total_feedback": total_feedback,
        "user_satisfaction_rate": user_satisfaction_rate,
        "feedback_counts": {
            "helpful": helpful_count,
            "incorrect": incorrect_count
        },
        "verdict_distribution": verdict_dist,
        "category_distribution": category_dist
    }
