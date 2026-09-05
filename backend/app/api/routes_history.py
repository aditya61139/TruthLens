from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.db.database import get_db
from app.db.models import ClaimHistory, TrendingClaim

router = APIRouter(tags=["History & Trending"])

@router.get("/history")
def get_claim_history(
    q: Optional[str] = Query(None, description="Search query"),
    verdict: Optional[str] = Query(None, description="Filter by verdict"),
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(30, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(ClaimHistory)

    if q:
        search_pat = f"%{q.strip()}%"
        query = query.filter(
            (ClaimHistory.input_text.ilike(search_pat)) |
            (ClaimHistory.extracted_claim.ilike(search_pat)) |
            (ClaimHistory.explanation_summary.ilike(search_pat))
        )

    if verdict:
        query = query.filter(ClaimHistory.verdict == verdict)

    if category:
        query = query.filter(ClaimHistory.category == category)

    history = query.order_by(desc(ClaimHistory.created_at)).limit(limit).all()

    return {
        "total": len(history),
        "history": [
            {
                "id": h.id,
                "input_text": h.input_text,
                "extracted_claim": h.extracted_claim,
                "verdict": h.verdict,
                "confidence": h.confidence,
                "category": h.category,
                "sources_count": h.sources_count,
                "red_flag_score": h.red_flag_score,
                "summary": h.explanation_summary,
                "created_at": h.created_at.isoformat() if h.created_at else None
            }
            for h in history
        ]
    }

@router.get("/trending")
def get_trending_claims(
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(TrendingClaim)
    if category and category != "All":
        query = query.filter(TrendingClaim.category.ilike(f"%{category}%"))

    trending = query.order_by(desc(TrendingClaim.search_volume)).all()

    # Get topic summary stats
    all_trending = db.query(TrendingClaim).all()
    categories_count = {}
    verdicts_count = {}
    for t in all_trending:
        categories_count[t.category] = categories_count.get(t.category, 0) + 1
        verdicts_count[t.verdict] = verdicts_count.get(t.verdict, 0) + 1

    return {
        "trending": [
            {
                "id": t.id,
                "claim_text": t.claim_text,
                "verdict": t.verdict,
                "confidence": t.confidence,
                "category": t.category,
                "summary": t.summary,
                "source_name": t.source_name,
                "source_url": t.source_url,
                "search_volume": t.search_volume,
                "last_checked": t.last_checked.isoformat() if t.last_checked else None
            }
            for t in trending
        ],
        "stats": {
            "categories": categories_count,
            "verdicts": verdicts_count,
            "total_monitored": len(all_trending)
        }
    }

@router.delete("/history/{history_id}")
def delete_history_item(history_id: int, db: Session = Depends(get_db)):
    item = db.query(ClaimHistory).filter(ClaimHistory.id == history_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="History entry not found")
    db.delete(item)
    db.commit()
    return {"status": "deleted", "id": history_id}
