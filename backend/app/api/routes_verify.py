import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import ClaimHistory
from app.services.extractor import ClaimExtractor
from app.services.pattern_analyzer import MisinformationPatternAnalyzer
from app.services.credibility_service import PublisherCredibilityService
from app.services.factcheck_service import FactCheckService
from app.services.google_search_service import GoogleSearchService
from app.services.synthesis_service import SynthesisService
from app.services.cache_service import CacheService

router = APIRouter(prefix="/verify", tags=["Verification"])

class VerifyRequest(BaseModel):
    text: str
    url: Optional[str] = None
    language: Optional[str] = "en"
    bypass_cache: Optional[bool] = False

class ArticleVerifyRequest(BaseModel):
    text: Optional[str] = None
    url: Optional[str] = None
    max_claims: Optional[int] = 6

@router.post("")
async def verify_claim(req: VerifyRequest, db: Session = Depends(get_db)):
    raw_input = req.text.strip()
    if not raw_input and not req.url:
        raise HTTPException(status_code=400, detail="Either text or url must be provided.")

    target_url = req.url
    page_title = ""
    domain_to_check = None

    # 1. Check if input is a URL
    if ClaimExtractor.is_url(raw_input) and not target_url:
        target_url = raw_input

    # 2. Cache Check (if not bypassed)
    if not req.bypass_cache and not target_url:
        cached = CacheService.get_cached_result(db, raw_input)
        if cached:
            return cached

    # 3. Handle URL Extraction if applicable
    if target_url:
        url_data = await ClaimExtractor.extract_from_url(target_url)
        if url_data.get("error"):
            raise HTTPException(status_code=400, detail=f"Failed to fetch webpage content: {url_data['error']}")
        page_title = url_data.get("title", "")
        raw_text = url_data.get("text", "") or page_title
        domain_to_check = url_data.get("domain")
        extracted_claim = ClaimExtractor.extract_core_claim(raw_text if len(raw_text) < 500 else page_title)
    else:
        domain_to_check = PublisherCredibilityService.extract_domain(raw_input)
        extracted_claim = ClaimExtractor.extract_core_claim(raw_input)

    if not extracted_claim:
        extracted_claim = raw_input

    # Detect if claim is time-sensitive / breaking / current event
    is_time_sensitive = ClaimExtractor.is_time_sensitive(raw_input)
    search_query = ClaimExtractor.normalize_search_query(raw_input if not target_url else extracted_claim)

    # 4. Publisher Credibility Lookup
    publisher_info = None
    if domain_to_check:
        publisher_info = PublisherCredibilityService.get_publisher_info(db, domain_to_check)

    # 5. Misinformation Pattern Detection (Red Flags)
    red_flags = MisinformationPatternAnalyzer.analyze(raw_input if not target_url else f"{page_title} {extracted_claim}")

    # 6. Settled Fact / Established Knowledge Tier (Local Catalog - 0 API Calls)
    settled_fact = FactCheckService.check_settled_fact(extracted_claim)

    evidence_list = []
    web_search_meta = {
        "attempted": False,
        "query_used": search_query,
        "provider": "None",
        "results_count": 0
    }
    
    if not settled_fact:
        if is_time_sensitive:
            # 7a. For time-sensitive claims, execute live web search
            web_search_meta["attempted"] = True
            search_res = await GoogleSearchService.search_live_web(extracted_claim, search_query)
            if search_res and search_res.get("evidence"):
                evidence_list.extend(search_res["evidence"])
                web_search_meta["provider"] = search_res.get("metadata", {}).get("provider", "Live Web Search")
                web_search_meta["results_count"] = len(search_res["evidence"])

            # Also check fact check database
            fc_results = await FactCheckService.verify_claim_evidence(extracted_claim, req.language or "en")
            if fc_results:
                evidence_list.extend(fc_results)

        else:
            # 7b. Primary Fact-Check Search (Google Fact Check Tools + Curated Repository)
            evidence_list = await FactCheckService.verify_claim_evidence(extracted_claim, req.language or "en")

            # 8. Web Search fallback if no fact checks found
            if not evidence_list:
                web_search_meta["attempted"] = True
                search_res = await GoogleSearchService.search_live_web(extracted_claim, search_query)
                if search_res and search_res.get("evidence"):
                    evidence_list.extend(search_res["evidence"])
                    web_search_meta["provider"] = search_res.get("metadata", {}).get("provider", "Live Web Search")
                    web_search_meta["results_count"] = len(search_res["evidence"])

    # 9. Enrich evidence with publisher credibility
    enriched_evidence = []
    for ev in evidence_list:
        ev_site = ev.get("source_site") or ev.get("source_name")
        ev_pub = PublisherCredibilityService.get_publisher_info(db, ev_site)
        ev["publisher_credibility"] = {
            "name": ev_pub.get("name"),
            "credibility_score": ev_pub.get("credibility_score"),
            "trust_tier": ev_pub.get("trust_tier"),
            "bias_rating": ev_pub.get("bias_rating"),
            "factual_reporting": ev_pub.get("factual_reporting")
        }
        enriched_evidence.append(ev)

    # 10. Single Unified Synthesis & Explainability Engine (At most ONE Gemini call)
    synthesis = await SynthesisService.synthesize(
        claim_text=extracted_claim,
        evidence_list=enriched_evidence,
        red_flags=red_flags,
        publisher_info=publisher_info,
        settled_fact_info=settled_fact,
        is_time_sensitive=is_time_sensitive,
        search_query=search_query,
        allow_gemini_call=True
    )

    # Detect category heuristically if not already defined
    category = settled_fact.get("category", "General") if settled_fact else "General"
    claim_lower = extracted_claim.lower()
    if category == "General":
        if any(w in claim_lower for w in ["president", "trump", "biden", "election", "voted", "senate", "congress", "minister", "parliament", "party"]):
            category = "Politics"
        elif any(w in claim_lower for w in ["vaccine", "cure", "cancer", "virus", "who", "cdc", "health", "doctor", "medicine", "disease", "covid", "garlic", "banana"]):
            category = "Health & Medicine"
        elif any(w in claim_lower for w in ["nasa", "space", "planet", "webb", "mars", "moon", "sun", "astronomy", "physics", "telescope"]):
            category = "Science & Space"
        elif any(w in claim_lower for w in ["5g", "ai", "apple", "google", "robot", "crypto", "bitcoin", "tech"]):
            category = "Technology"
        elif any(w in claim_lower for w in ["climate", "carbon", "emission", "warming", "earth", "ev", "flood", "earthquake", "weather", "storm", "cyclone"]):
            category = "Climate & Environment"
        elif any(w in claim_lower for w in ["paris", "capital", "france", "tokyo", "ocean", "river", "mountain", "london", "tibet"]):
            category = "Geography & World Events"

    # 11. Save to Cache ONLY if synthesis did NOT encounter a fatal service error
    if synthesis.get("verdict") != "Error":
        CacheService.set_cached_result(
            db=db,
            raw_input=raw_input if not target_url else target_url,
            extracted_claim=extracted_claim,
            verdict=synthesis["verdict"],
            confidence=synthesis["confidence"],
            category=category,
            sources=enriched_evidence,
            red_flags=red_flags,
            explanation=synthesis["explanation"],
            credibility=publisher_info or {},
            summary=synthesis["summary"],
            confidence_factors=synthesis["confidence_factors"]
        )

        history_entry = ClaimHistory(
            input_text=raw_input if not target_url else target_url,
            extracted_claim=extracted_claim,
            verdict=synthesis["verdict"],
            confidence=synthesis["confidence"],
            category=category,
            sources_count=len(enriched_evidence),
            red_flag_score=red_flags.get("red_flag_score", 0.0),
            explanation_summary=synthesis.get("summary", ""),
            created_at=datetime.datetime.utcnow()
        )
        db.add(history_entry)
        db.commit()

    final_sources = synthesis.get("reranked_sources") if synthesis.get("reranked_sources") is not None else enriched_evidence

    return {
        "cached": False,
        "is_fuzzy_match": False,
        "fuzzy_similarity": 0.0,
        "input_text": raw_input,
        "extracted_claim": extracted_claim,
        "mode": synthesis.get("mode", "Claim Verification"),
        "event_meta": synthesis.get("event_meta"),
        "is_time_sensitive": is_time_sensitive,
        "claim_type": synthesis.get("claim_type", "CURRENT_EVENT"),
        "web_search": web_search_meta,
        "page_title": page_title if target_url else None,
        "url": target_url,
        "verdict": synthesis["verdict"],
        "truth_value": synthesis.get("truth_value", synthesis["verdict"]),
        "knowledge_certainty": synthesis.get("knowledge_certainty", "Emerging / Current Event"),
        "final_verdict_display": synthesis.get("final_verdict_display", synthesis["verdict"]),
        "is_settled_fact": synthesis.get("is_settled_fact", False),
        "fact_type": synthesis.get("fact_type"),
        "confidence": synthesis["confidence"],
        "confidence_factors": synthesis["confidence_factors"],
        "category": category,
        "summary": synthesis["summary"],
        "llm_enhanced": synthesis.get("llm_enhanced", False),
        "llm_warning": synthesis.get("llm_warning"),
        "gemini_calls_made": synthesis.get("gemini_calls_made", 0),
        "error": synthesis.get("error"),
        "explanation": synthesis["explanation"],
        "quick_summary": synthesis.get("quick_summary", {}),
        "red_flags": red_flags,
        "credibility": publisher_info or {},
        "sources": final_sources,
        "verified_at": datetime.datetime.utcnow().isoformat()
    }

@router.post("/article")
async def verify_article(req: ArticleVerifyRequest, db: Session = Depends(get_db)):
    """
    Batch / Article Mode:
    Extracts all checkable claims from article, verifies each using local deterministic checks,
    and computes overall Article Trust Score without spamming Gemini API calls.
    """
    article_text = req.text or ""
    article_title = ""
    domain = None

    if req.url:
        url_data = await ClaimExtractor.extract_from_url(req.url)
        if url_data.get("error"):
            raise HTTPException(status_code=400, detail=f"Failed to fetch article: {url_data['error']}")
        article_title = url_data.get("title", "")
        article_text = url_data.get("text", "") or article_title
        domain = url_data.get("domain")

    if not article_text.strip():
        raise HTTPException(status_code=400, detail="Article text or valid URL is required.")

    # Extract checkable claims
    candidate_claims = ClaimExtractor.extract_all_claims(article_text, max_claims=req.max_claims or 6)
    if not candidate_claims:
        candidate_claims = [{
            "claim_index": 1,
            "claim_text": ClaimExtractor.extract_core_claim(article_text),
            "context": article_text[:200],
            "reasons": ["Primary article assertion"]
        }]

    overall_red_flags = MisinformationPatternAnalyzer.analyze(article_text)
    
    publisher_info = None
    if domain:
        publisher_info = PublisherCredibilityService.get_publisher_info(db, domain)

    verified_claims = []
    verdict_distribution = {"True": 0, "False": 0, "Misleading": 0, "Unverified": 0, "Satire": 0}

    for c in candidate_claims:
        c_text = c["claim_text"]
        
        cached = CacheService.get_cached_result(db, c_text)
        if cached:
            verdict = cached["verdict"]
            confidence = cached["confidence"]
            summary = cached["explanation"].get("why_bullets", ["Verified from cache."])[0] if cached.get("explanation") else "Cached result"
            sources = cached.get("sources", [])
            rf = cached.get("red_flags", {})
        else:
            rf = MisinformationPatternAnalyzer.analyze(c_text)
            settled = FactCheckService.check_settled_fact(c_text)
            evidence = []
            if not settled:
                c_search_query = ClaimExtractor.normalize_search_query(c_text)
                search_res = await GoogleSearchService.search_live_web(c_text, c_search_query)
                if search_res and search_res.get("evidence"):
                    evidence.extend(search_res["evidence"])
                
                fc_ev = await FactCheckService.verify_claim_evidence(c_text)
                if fc_ev:
                    evidence.extend(fc_ev)
            
            # In batch article mode, use deterministic synthesis (allow_gemini_call=False to prevent quota exhaustion)
            synth = await SynthesisService.synthesize(
                claim_text=c_text,
                evidence_list=evidence,
                red_flags=rf,
                publisher_info=publisher_info,
                settled_fact_info=settled,
                allow_gemini_call=False
            )
            verdict = synth["verdict"]
            confidence = synth["confidence"]
            summary = synth["summary"]
            sources = evidence

        verdict_distribution[verdict] = verdict_distribution.get(verdict, 0) + 1

        verified_claims.append({
            "claim_index": c["claim_index"],
            "claim_text": c_text,
            "context": c.get("context", ""),
            "verdict": verdict,
            "confidence": confidence,
            "summary": summary,
            "sources_count": len(sources),
            "sources": sources[:2],
            "red_flags": rf
        })

    # Overall Article Trust Score (0 - 100)
    total_claims = len(verified_claims)
    true_count = verdict_distribution.get("True", 0)
    false_count = verdict_distribution.get("False", 0)
    misleading_count = verdict_distribution.get("Misleading", 0)
    unverified_count = verdict_distribution.get("Unverified", 0)
    satire_count = verdict_distribution.get("Satire", 0)

    if satire_count > 0:
        overall_trust_score = 40.0
        trust_grade = "Satire / Parody"
    else:
        base_score = 50.0
        if total_claims > 0:
            claim_score = (true_count * 100.0 + unverified_count * 45.0 + misleading_count * 20.0 + false_count * 0.0) / total_claims
            base_score = claim_score

        rf_score = overall_red_flags.get("red_flag_score", 0)
        base_score -= (rf_score * 0.25)

        if publisher_info and publisher_info.get("matched"):
            pub_score = publisher_info.get("credibility_score", 50)
            base_score = (base_score * 0.7) + (pub_score * 0.3)

        overall_trust_score = max(5.0, min(98.0, base_score))

        if overall_trust_score >= 80:
            trust_grade = "Highly Trustworthy"
        elif overall_trust_score >= 60:
            trust_grade = "Generally Credible with Nuance"
        elif overall_trust_score >= 40:
            trust_grade = "Questionable / Mixed Factual Accuracy"
        else:
            trust_grade = "High Misinformation Risk / Fabricated"

    return {
        "article_title": article_title or "Submitted Article",
        "url": req.url,
        "total_claims_analyzed": total_claims,
        "overall_trust_score": round(overall_trust_score, 1),
        "trust_grade": trust_grade,
        "verdict_distribution": verdict_distribution,
        "overall_red_flags": overall_red_flags,
        "publisher_credibility": publisher_info or {},
        "claims": verified_claims
    }
