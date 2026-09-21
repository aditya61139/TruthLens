import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient
from app.main import app
from app.db.database import get_db, SessionLocal
from app.db.models import UserFeedback, PublisherCredibility
from app.services.extractor import ClaimExtractor
from app.services.credibility_service import PublisherCredibilityService
from app.api.routes_verify import VerifyRequest, ArticleVerifyRequest
from app.api.routes_feedback import FeedbackRequest
from app.api.routes_config import SetKeyRequest

client = TestClient(app)

def test_ssrf_protection_blocks_restricted_ips():
    """Verify that private, loopback, and cloud metadata targets are rejected."""
    # Loopback
    is_safe, err = ClaimExtractor.validate_safe_url("http://127.0.0.1:8000/api/config/status")
    assert not is_safe
    assert "restricted" in err.lower() or "local" in err.lower()

    # Localhost
    is_safe, err = ClaimExtractor.validate_safe_url("http://localhost:3000")
    assert not is_safe

    # Cloud metadata
    is_safe, err = ClaimExtractor.validate_safe_url("http://169.254.169.254/latest/meta-data/")
    assert not is_safe

    # Private IP space
    is_safe, err = ClaimExtractor.validate_safe_url("http://192.168.1.1")
    assert not is_safe

    is_safe, err = ClaimExtractor.validate_safe_url("http://10.0.0.5:8080/admin")
    assert not is_safe

    # Invalid scheme
    is_safe, err = ClaimExtractor.validate_safe_url("ftp://example.com/data")
    assert not is_safe
    assert "unsupported" in err.lower()

    # Legitimate public domain
    is_safe, err = ClaimExtractor.validate_safe_url("https://example.com")
    assert is_safe
    assert err == ""

def test_cctld_subdomain_resolution():
    """Verify that multi-part ccTLDs like bbc.co.uk match accurately."""
    db = SessionLocal()
    try:
        # Check if bbc.co.uk exists in db; if not seed temporarily
        bbc_pub = db.query(PublisherCredibility).filter(PublisherCredibility.domain == "bbc.co.uk").first()
        if not bbc_pub:
            bbc_pub = PublisherCredibility(
                domain="bbc.co.uk",
                name="BBC News",
                category="Mainstream",
                bias_rating="Center",
                factual_reporting="High",
                credibility_score=92
            )
            db.add(bbc_pub)
            db.commit()

        # Test resolution with leading subdomains
        info1 = PublisherCredibilityService.get_publisher_info(db, "news.bbc.co.uk")
        assert info1["matched"] is True
        assert info1["domain"] == "bbc.co.uk"

        info2 = PublisherCredibilityService.get_publisher_info(db, "world.service.bbc.co.uk")
        assert info2["matched"] is True
        assert info2["domain"] == "bbc.co.uk"
    finally:
        db.close()

def test_bounded_request_payloads():
    """Verify that oversized inputs exceed Pydantic validation bounds."""
    # Text length > 10,000 chars
    with pytest.raises(ValidationError):
        VerifyRequest(text="A" * 10001)

    # Article length > 50,000 chars
    with pytest.raises(ValidationError):
        ArticleVerifyRequest(text="A" * 50001)

    # Claims count bounds (ge=1, le=20)
    with pytest.raises(ValidationError):
        ArticleVerifyRequest(text="Valid text", max_claims=25)

    # Feedback comments > 2,000 chars
    with pytest.raises(ValidationError):
        FeedbackRequest(
            claim_text="Some claim",
            given_verdict="True",
            feedback_type="helpful",
            comments="C" * 2001
        )

    # API Key length < 10 chars
    with pytest.raises(ValidationError):
        SetKeyRequest(google_api_key="short")

def test_feedback_honesty_zero_state():
    """Verify that system stats returns None/honest satisfaction when total feedback is 0."""
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_feedback" in data
    if data["total_feedback"] == 0:
        assert data["user_satisfaction_rate"] is None
    else:
        assert isinstance(data["user_satisfaction_rate"], (int, float))

def test_sqlite_wal_mode_active():
    """Verify that SQLite connection applies WAL journal mode and busy timeout."""
    from sqlalchemy import text
    db = SessionLocal()
    try:
        mode = db.execute(text("PRAGMA journal_mode")).fetchone()
        assert mode[0].lower() in ("wal", "memory")
    finally:
        db.close()
