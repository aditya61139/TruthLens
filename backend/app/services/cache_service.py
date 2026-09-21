import hashlib
import json
import re
import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from rapidfuzz import fuzz
from app.db.models import QueryCache
from app.core.config import settings

class CacheService:
    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalizes text for hash and fuzzy comparison."""
        cleaned = text.lower().strip()
        cleaned = re.sub(r"[^\w\s]", "", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned)
        return cleaned

    @staticmethod
    def compute_hash(normalized_text: str) -> str:
        return hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()

    @classmethod
    def get_cached_result(cls, db: Session, raw_input: str) -> Optional[Dict[str, Any]]:
        """
        Looks up cache by exact hash first, then by fuzzy token similarity.
        """
        normalized = cls.normalize_text(raw_input)
        q_hash = cls.compute_hash(normalized)
        now = datetime.datetime.now(datetime.timezone.utc)

        # 1. Exact hash lookup
        exact_entry = db.query(QueryCache).filter(
            QueryCache.query_hash == q_hash,
            QueryCache.expires_at > now
        ).first()

        if exact_entry:
            exact_entry.access_count += 1
            db.commit()
            return cls._deserialize_entry(exact_entry, is_fuzzy_match=False, similarity_score=100.0)

        # 2. Fuzzy match against recent unexpired cache entries
        active_entries = db.query(QueryCache).filter(QueryCache.expires_at > now).all()
        best_match = None
        highest_score = 0.0

        for entry in active_entries:
            score = fuzz.token_set_ratio(normalized, entry.normalized_query)
            if score > highest_score and score >= settings.FUZZY_MATCH_THRESHOLD:
                highest_score = score
                best_match = entry

        if best_match:
            best_match.access_count += 1
            db.commit()
            return cls._deserialize_entry(best_match, is_fuzzy_match=True, similarity_score=round(highest_score, 1))

        return None

    @classmethod
    def set_cached_result(
        cls,
        db: Session,
        raw_input: str,
        extracted_claim: str,
        verdict: str,
        confidence: float,
        category: str,
        sources: list,
        red_flags: dict,
        explanation: dict,
        credibility: dict,
        summary: str = "",
        confidence_factors: list = None
    ) -> None:
        """Saves a verification result into the cache with TTL."""
        normalized = cls.normalize_text(raw_input)
        q_hash = cls.compute_hash(normalized)
        now = datetime.datetime.now(datetime.timezone.utc)
        expires = now + datetime.timedelta(hours=settings.CACHE_TTL_HOURS)

        # Include summary and confidence factors in explanation payload
        payload_explanation = dict(explanation)
        payload_explanation["_summary"] = summary
        payload_explanation["_confidence_factors"] = confidence_factors or []

        existing = db.query(QueryCache).filter(QueryCache.query_hash == q_hash).first()
        if existing:
            existing.extracted_claim = extracted_claim
            existing.verdict = verdict
            existing.confidence = confidence
            existing.category = category
            existing.sources_json = json.dumps(sources)
            existing.red_flags_json = json.dumps(red_flags)
            existing.explanation_json = json.dumps(payload_explanation)
            existing.credibility_json = json.dumps(credibility)
            existing.expires_at = expires
            existing.access_count += 1
        else:
            new_cache = QueryCache(
                query_hash=q_hash,
                normalized_query=normalized,
                input_text=raw_input,
                extracted_claim=extracted_claim,
                verdict=verdict,
                confidence=confidence,
                category=category,
                sources_json=json.dumps(sources),
                red_flags_json=json.dumps(red_flags),
                explanation_json=json.dumps(payload_explanation),
                credibility_json=json.dumps(credibility),
                expires_at=expires
            )
            db.add(new_cache)

        db.commit()

    @staticmethod
    def _deserialize_entry(entry: QueryCache, is_fuzzy_match: bool, similarity_score: float) -> Dict[str, Any]:
        exp = json.loads(entry.explanation_json or "{}")
        summary = exp.get("_summary") or (exp.get("why_bullets") and exp["why_bullets"][0]) or f"This claim was evaluated as {entry.verdict} with {round(entry.confidence)}% confidence."
        confidence_factors = exp.get("_confidence_factors") or ["Retrieved from verified local cache."]

        # Clean private fields from returned explanation
        clean_exp = {k: v for k, v in exp.items() if not k.startswith("_")}

        return {
            "cached": True,
            "is_fuzzy_match": is_fuzzy_match,
            "fuzzy_similarity": similarity_score,
            "query_hash": entry.query_hash,
            "input_text": entry.input_text,
            "extracted_claim": entry.extracted_claim,
            "verdict": entry.verdict,
            "confidence": entry.confidence,
            "confidence_factors": confidence_factors,
            "category": entry.category,
            "summary": summary,
            "sources": json.loads(entry.sources_json or "[]"),
            "red_flags": json.loads(entry.red_flags_json or "{}"),
            "explanation": clean_exp,
            "credibility": json.loads(entry.credibility_json or "{}"),
            "cached_at": entry.created_at.isoformat() if entry.created_at else None,
            "access_count": entry.access_count
        }
