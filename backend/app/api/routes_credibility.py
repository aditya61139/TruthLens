from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import PublisherCredibility
from app.services.credibility_service import PublisherCredibilityService

router = APIRouter(prefix="/sources", tags=["Publisher Credibility"])

@router.get("")
def list_publishers(
    q: Optional[str] = Query(None, description="Search domain or name"),
    category: Optional[str] = Query(None, description="Filter by category (Fact-Checker, Mainstream, Satire, Conspiracy)"),
    bias: Optional[str] = Query(None, description="Filter by bias"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    query = db.query(PublisherCredibility)

    if q:
        search_pattern = f"%{q.strip()}%"
        query = query.filter(
            (PublisherCredibility.domain.ilike(search_pattern)) | 
            (PublisherCredibility.name.ilike(search_pattern)) |
            (PublisherCredibility.notes.ilike(search_pattern))
        )

    if category:
        query = query.filter(PublisherCredibility.category == category)

    if bias:
        query = query.filter(PublisherCredibility.bias_rating == bias)

    publishers = query.order_by(PublisherCredibility.credibility_score.desc()).limit(limit).all()

    return {
        "total": len(publishers),
        "results": [
            {
                "id": p.id,
                "domain": p.domain,
                "name": p.name,
                "category": p.category,
                "bias_rating": p.bias_rating,
                "factual_reporting": p.factual_reporting,
                "credibility_score": p.credibility_score,
                "trust_tier": PublisherCredibilityService._get_trust_tier(p.credibility_score),
                "country": p.country,
                "notes": p.notes
            }
            for p in publishers
        ]
    }

@router.get("/{domain}")
def get_publisher_by_domain(domain: str, db: Session = Depends(get_db)):
    pub_info = PublisherCredibilityService.get_publisher_info(db, domain)
    if not pub_info:
        raise HTTPException(status_code=404, detail="Publisher not found")
    return pub_info
