import pytest
import asyncio
from fastapi.testclient import TestClient
from app.main import app
from app.db.database import engine, Base, SessionLocal
from app.db.seed_data import seed_database
from app.services.news_service import NewsCrossReferenceService
from app.services.extractor import ClaimExtractor
from app.services.gemini_rate_limiter import (
    GeminiRateLimiter,
    GeminiRateLimitException,
    GeminiNotFoundException,
    GeminiAuthException,
    GeminiApiException
)

@pytest.fixture(scope="session", autouse=True)
def init_test_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    yield

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_single_gemini_call_budget_enforcement():
    """Bug fix verification: A single query must NEVER make more than 1 Gemini API call."""
    payload = {
        "text": "is there a recent flash flood near tibet?",
        "bypass_cache": True
    }
    response = client.post("/api/verify", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data.get("gemini_calls_made", 0) <= 1

def test_rate_limiter_inter_call_spacing():
    """Verify GeminiRateLimiter enforces spacing between successive calls."""
    async def run_limiter_test():
        start = asyncio.get_event_loop().time()
        await GeminiRateLimiter.acquire()
        await GeminiRateLimiter.acquire()
        duration = asyncio.get_event_loop().time() - start
        assert duration >= 0.4  # At least ~500ms spacing enforced

    asyncio.run(run_limiter_test())

def test_rate_limiter_404_not_found_fails_fast():
    """Verify that 404 model errors fail fast without blind retries."""
    def fail_with_404():
        raise Exception("404 Model gemini-invalid not found")

    with pytest.raises(GeminiNotFoundException) as exc_info:
        asyncio.run(GeminiRateLimiter.execute_with_retry(fail_with_404))
    assert exc_info.value.code == "API_NOT_FOUND"

def test_rate_limiter_401_auth_error_fails_fast():
    """Verify that 401 invalid key errors fail fast without retries."""
    def fail_with_401():
        raise Exception("401 API_KEY_INVALID")

    with pytest.raises(GeminiAuthException) as exc_info:
        asyncio.run(GeminiRateLimiter.execute_with_retry(fail_with_401))
    assert exc_info.value.code == "API_AUTH_ERROR"

def test_time_sensitive_detection_and_query_normalization():
    """Verify that current events / question-form claims are detected and normalized."""
    raw_question = "is there a recent flash flood near tibet?"
    assert ClaimExtractor.is_time_sensitive(raw_question) is True
    
    normalized = ClaimExtractor.normalize_search_query(raw_question)
    assert "flash flood" in normalized.lower()
    assert "tibet" in normalized.lower()
    assert not normalized.lower().startswith("is there")

def test_time_sensitive_verification_attempts_web_search():
    """Bug fix verification: time-sensitive claims trigger live web search and return search metadata."""
    payload = {
        "text": "is there a recent flash flood near tibet?",
        "bypass_cache": True
    }
    response = client.post("/api/verify", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_time_sensitive"] is True
    assert "web_search" in data
    assert data["web_search"]["attempted"] is True
    assert "flash flood" in data["web_search"]["query_used"].lower()
    assert "tibet" in data["web_search"]["query_used"].lower()
    assert "provider" in data["web_search"]
    assert data["gemini_calls_made"] <= 1

def test_settled_fact_sun_rises_in_east():
    """Bug fix verification: 'sun rises from east' must return TRUE (Established Knowledge), 0 AI calls, 95%+ confidence."""
    payload = {
        "text": "sun rises from east",
        "bypass_cache": True
    }
    response = client.post("/api/verify", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["verdict"] == "True"
    assert data["is_settled_fact"] is True
    assert data["confidence"] >= 95.0
    assert data["gemini_calls_made"] == 0  # 0 AI calls for settled facts!
    assert len(data["sources"]) >= 2  # Settled facts return educational reference sources (NASA, Stanford, Britannica, etc.)
    assert "established" in data["summary"].lower() or "undisputed" in data["summary"].lower()

def test_settled_fact_water_boils():
    """Test fundamental physics/thermodynamics settled fact."""
    payload = {
        "text": "water boils at 100 degrees celsius",
        "bypass_cache": True
    }
    response = client.post("/api/verify", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["verdict"] == "True"
    assert data["is_settled_fact"] is True
    assert data["confidence"] >= 95.0
    assert data["gemini_calls_made"] == 0

def test_settled_fact_paris_capital_france():
    """Test fundamental world geography settled fact."""
    payload = {
        "text": "Paris is the capital of France",
        "bypass_cache": True
    }
    response = client.post("/api/verify", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["verdict"] == "True"
    assert data["is_settled_fact"] is True
    assert data["confidence"] >= 95.0
    assert data["gemini_calls_made"] == 0

def test_unverified_claim_confidence_coupling():
    """Bug fix verification: Genuinely unverified claims must NEVER have high confidence (must be <= 45%)."""
    payload = {
        "text": "A local farmer in a remote village found a 17-sided pebble in 1983",
        "bypass_cache": True
    }
    response = client.post("/api/verify", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["verdict"] in ["Unverified", "Error"]
    assert data["confidence"] <= 45.0
    assert len(data["sources"]) == 0
    assert data["web_search"]["attempted"] is True

def test_news_relevance_filter():
    """Verify that NewsCrossReferenceService calculates low relevance for unrelated news."""
    claim = "sun rises from east"
    unrelated_title = "Equinox 2026: Why sunrise looks different on Mars"
    relevance = NewsCrossReferenceService.calculate_relevance(claim, unrelated_title)
    assert relevance < 55.0

    matched_title = "Sun rises in the east and sets in the west: Earth rotation guide"
    high_relevance = NewsCrossReferenceService.calculate_relevance(claim, matched_title)
    assert high_relevance > 70.0

def test_verify_known_false_claim():
    payload = {
        "text": "Drinking boiled garlic water cures coronavirus",
        "bypass_cache": True
    }
    response = client.post("/api/verify", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["verdict"] == "False"
    assert data["confidence"] >= 80.0
    assert len(data["sources"]) > 0
    assert "explanation" in data
    assert "red_flags" in data

def test_verify_known_true_claim():
    payload = {
        "text": "NASA James Webb Space Telescope detected atmospheric water vapor on exoplanet WASP-96b",
        "bypass_cache": True
    }
    response = client.post("/api/verify", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["verdict"] == "True"
    assert data["confidence"] >= 80.0

def test_fuzzy_caching_performance():
    payload1 = {
        "text": "Pope Francis officially endorsed Donald Trump for US President",
        "bypass_cache": False
    }
    resp1 = client.post("/api/verify", json=payload1)
    assert resp1.status_code == 200

    payload2 = {
        "text": "Did Pope Francis officially endorse Donald Trump for US President?",
        "bypass_cache": False
    }
    resp2 = client.post("/api/verify", json=payload2)
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["cached"] is True
    assert data2["verdict"] == "False"

def test_article_mode_verification():
    article_text = """
    A viral online rumor claimed that 5G mobile network radiation causes viral respiratory illnesses.
    Meanwhile, NASA confirmed that James Webb Telescope revealed steamy atmosphere on distant exoplanet WASP-96b.
    Medical experts continue to study the long term effects of viral pathogens across world populations.
    """
    payload = {
        "text": article_text,
        "max_claims": 4
    }
    response = client.post("/api/verify/article", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "overall_trust_score" in data
    assert "claims" in data
    assert len(data["claims"]) >= 2
    assert "verdict_distribution" in data

def test_publisher_sources_endpoint():
    response = client.get("/api/sources?q=reuters")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert any("Reuters" in r["name"] for r in data["results"])

def test_trending_claims_endpoint():
    response = client.get("/api/trending")
    assert response.status_code == 200
    assert len(data := response.json()["trending"]) >= 3
    assert "stats" in response.json()

def test_community_feedback():
    payload = {
        "claim_text": "Drinking boiled garlic water cures coronavirus",
        "given_verdict": "False",
        "feedback_type": "helpful",
        "comments": "Accurate fact check with verified WHO source."
    }
    response = client.post("/api/feedback", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "success"

def test_settled_fact_contradiction_sun_rises_in_west():
    """RAG Bug fix verification: 'sun rises from west' must return FALSE (Settled Contradiction), 0 AI calls, 95%+ confidence."""
    payload = {
        "text": "sun rises from west",
        "bypass_cache": True
    }
    response = client.post("/api/verify", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["verdict"] == "False"
    assert data["is_settled_fact"] is True
    assert data["confidence"] >= 95.0
    assert data["gemini_calls_made"] == 0
    assert "contradict" in data["summary"].lower() or "false" in data["summary"].lower()

def test_settled_fact_contradiction_earth_is_flat():
    """Settled contradiction: 'earth is flat' must return FALSE (97%+ confidence, 0 AI calls)."""
    payload = {
        "text": "earth is flat",
        "bypass_cache": True
    }
    response = client.post("/api/verify", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["verdict"] == "False"
    assert data["is_settled_fact"] is True
    assert data["confidence"] >= 95.0
    assert data["gemini_calls_made"] == 0

def test_claim_classifier_domains():
    """Verify local ClaimClassifier categorizes claims into SETTLED_FACT, CURRENT_EVENT, OPINION, CONTESTED."""
    from app.services.stance_service import ClaimClassifier
    assert ClaimClassifier.classify("sun rises in east") == "SETTLED_FACT"
    assert ClaimClassifier.classify("water boils at 100 celsius") == "SETTLED_FACT"
    assert ClaimClassifier.classify("is there a recent flash flood near tibet?") == "CURRENT_EVENT"
    assert ClaimClassifier.classify("avocado toast is the tastiest breakfast ever") == "OPINION"
    assert ClaimClassifier.classify("universal basic income ubi policy impacts") == "CONTESTED"

def test_stance_detector_antonym_contradiction():
    """Verify StanceDetector identifies directional/antonym contradiction between claim and evidence."""
    from app.services.stance_service import StanceDetector
    claim = "sun rises from west"
    doc_title = "Stanford Solar Center: The Sun rises due east"
    doc_content = "Earth rotation causes the Sun to appear in the eastern horizon every morning."
    
    stance, conf, reason = StanceDetector.detect_stance(claim, doc_title, doc_content)
    assert stance == "CONTRADICTS"
    assert conf >= 85.0
    assert "east" in reason.lower()

def test_evidence_reranker_with_stances():
    """Verify EvidenceReranker labels stances and prioritizes clear entailment/contradiction."""
    from app.services.stance_service import EvidenceReranker
    claim = "sun rises from west"
    docs = [
        {"title": "Equinox weather photos around the world", "explanation": "General scenery photos.", "relevance_score": 30.0},
        {"title": "Stanford Solar Center: The Sun rises due east", "explanation": "Solar physics guide showing sunrise due east.", "relevance_score": 75.0}
    ]
    reranked = EvidenceReranker.rerank_evidence(claim, docs, max_docs=2)
    assert len(reranked) == 2
    assert reranked[0]["stance"] == "CONTRADICTS"
    assert "Stanford" in reranked[0]["title"]

def test_two_dimensional_verdict_sun_rises_from_west():
    """Verify 2 independent dimensions: Truth Value='False', Certainty='Settled Knowledge', Display='FALSE — Contradicts Established Knowledge'."""
    payload = {
        "text": "sun rises from west",
        "bypass_cache": True
    }
    response = client.post("/api/verify", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["truth_value"] == "False"
    assert data["knowledge_certainty"] == "Settled Knowledge"
    assert data["final_verdict_display"] == "FALSE — Contradicts Established Knowledge"
    assert data["verdict"] == "False"
    assert data["final_verdict_display"] != "TRUE — Established Knowledge"

def test_two_dimensional_verdict_sun_rises_from_east():
    """Verify 2 independent dimensions: Truth Value='True', Certainty='Settled Knowledge', Display='TRUE — Established Knowledge'."""
    payload = {
        "text": "sun rises from east",
        "bypass_cache": True
    }
    response = client.post("/api/verify", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["truth_value"] == "True"
    assert data["knowledge_certainty"] == "Settled Knowledge"
    assert data["final_verdict_display"] == "TRUE — Established Knowledge"
    assert data["verdict"] == "True"

def test_clause_level_consistency_guard_rail_overrides_true():
    """Verify that if any clause is marked 'debunked', the guard rail strictly prevents a 'True' verdict."""
    from app.services.synthesis_service import SynthesisService
    breakdown = [
        {"clause": "the sun rises from the west", "status": "debunked", "note": "Contradicts Earth rotation"}
    ]
    tv, kc, display = SynthesisService.apply_consistency_guard_rail(
        truth_value="True",
        knowledge_certainty="Settled Knowledge",
        claim_breakdown=breakdown,
        reranked_docs=[]
    )
    assert tv == "False"
    assert display == "FALSE — Contradicts Established Knowledge"

def test_quick_summary_360_briefing_structure():
    """Verify that the 360° Incident Briefing contains all 8 required sub-sections."""
    payload = {
        "text": "sun rises in east",
        "bypass_cache": True
    }
    response = client.post("/api/verify", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "quick_summary" in data
    qs = data["quick_summary"]
    assert "what_happened" in qs and len(qs["what_happened"]) > 10
    assert "full_context" in qs and len(qs["full_context"]) > 10
    assert "timeline" in qs and isinstance(qs["timeline"], list)
    assert "key_parties" in qs and isinstance(qs["key_parties"], list)
    assert "key_data" in qs and isinstance(qs["key_data"], list)
    assert "perspectives" in qs and isinstance(qs["perspectives"], list)
    assert "current_status" in qs and len(qs["current_status"]) > 5
    assert "key_takeaway" in qs and len(qs["key_takeaway"]) > 5

def test_source_type_classification_tiers():
    """Verify the 5 canonical source classification tiers."""
    from app.services.synthesis_service import SynthesisService
    assert SynthesisService.classify_source_type("NASA", "https://science.nasa.gov/") == "[🟢 Primary Source]"
    assert SynthesisService.classify_source_type("CDC", "https://cdc.gov/flu") == "[🟢 Primary Source]"
    assert SynthesisService.classify_source_type("Reuters", "https://reuters.com/world") == "[🔵 Major News Outlet]"
    assert SynthesisService.classify_source_type("BBC News", "https://bbc.com/news") == "[🔵 Major News Outlet]"
    assert SynthesisService.classify_source_type("Snopes", "https://snopes.com/fact-check") == "[🟡 Fact-Checker]"
    assert SynthesisService.classify_source_type("PolitiFact", "https://politifact.com/") == "[🟡 Fact-Checker]"
    assert SynthesisService.classify_source_type("Stanford University", "https://solar-center.stanford.edu") == "[🟠 Domain Expert / Academic]"
    assert SynthesisService.classify_source_type("Encyclopedia Britannica", "https://britannica.com") == "[🟠 Domain Expert / Academic]"
    assert SynthesisService.classify_source_type("Wikipedia", "https://en.wikipedia.org/wiki/Earth") == "[⚪ Other / General]"

def test_settled_fact_sources_and_further_reading():
    """Verify that settled knowledge facts return minimum 2 curated reference sources with proper tiers and links."""
    payload = {
        "text": "water boils at 100 celsius",
        "bypass_cache": True
    }
    response = client.post("/api/verify", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["sources"]) >= 2
    for s in data["sources"]:
        assert "source_name" in s and len(s["source_name"]) > 0
        assert "source_url" in s and s["source_url"].startswith("http")
        assert "source_type" in s and s["source_type"].startswith("[")
        assert "date_published" in s

def test_tri_mode_input_classification():
    """Verify Mode A (Claim Verification), Mode B (Event Query), and Mode C (Hybrid)."""
    from app.services.extractor import ClaimExtractor
    assert ClaimExtractor.detect_query_mode("The sun rises from the west") == "Claim Verification"
    assert ClaimExtractor.detect_query_mode("India has the largest population in the world") == "Claim Verification"
    assert ClaimExtractor.detect_query_mode("Is there a recent flash flood in India?") == "Event Query"
    assert ClaimExtractor.detect_query_mode("What happened in the Turkey earthquake?") == "Event Query"
    assert ClaimExtractor.detect_query_mode("Any updates on the Israel-Palestine conflict?") == "Event Query"
    assert ClaimExtractor.detect_query_mode("500 people died in the Assam floods") == "Hybrid"
    assert ClaimExtractor.detect_query_mode("The government has not sent any relief to flood victims") == "Hybrid"

def test_event_category_detection():
    """Verify event category emojis and labels."""
    from app.services.extractor import ClaimExtractor
    emoji, label = ClaimExtractor.detect_event_category("Assam monsoon flash flood")
    assert emoji == "🌊"
    assert "Flooding" in label

    emoji, label = ClaimExtractor.detect_event_category("Turkey earthquake tremor")
    assert emoji == "🌋"
    assert "Earthquake" in label

    emoji, label = ClaimExtractor.detect_event_category("Israel Gaza conflict military")
    assert emoji == "🌍"
    assert "Conflict" in label

def test_mode_b_event_query_endpoint_structure():
    """Verify that Mode B event queries return event_meta and structured impact_numbers."""
    payload = {
        "text": "Is there a recent flash flood in India?",
        "bypass_cache": True
    }
    response = client.post("/api/verify", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "Event Query"
    assert "event_meta" in data and data["event_meta"] is not None
    assert "category_emoji" in data["event_meta"]
    assert "category_label" in data["event_meta"]
    assert "status" in data["event_meta"]
    assert "quick_summary" in data
    qs = data["quick_summary"]
    assert "impact_numbers" in qs
    assert "deaths" in qs["impact_numbers"]
    assert "displaced" in qs["impact_numbers"]
    assert "areas_affected" in qs["impact_numbers"]


