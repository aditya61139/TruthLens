import pytest
from app.services.extractor import ClaimExtractor

def test_clean_text():
    raw = "BREAKING NEWS: You won't believe what happened! #Shocking https://example.com/fake"
    cleaned = ClaimExtractor.clean_text(raw)
    assert "BREAKING NEWS" not in cleaned
    assert "https://" not in cleaned
    assert "#Shocking" not in cleaned
    assert "You won't believe what happened!" in cleaned

def test_extract_core_claim():
    noisy = "ALERT: Scientists discovered ancient water signatures on a distant exoplanet yesterday. I think it is very cool."
    extracted = ClaimExtractor.extract_core_claim(noisy)
    assert "Scientists discovered ancient water signatures" in extracted

def test_extract_all_claims():
    article = """
    A new medical study reported that drinking green tea reduces hypertension risk by 15 percent.
    Researchers analyzed over 5,000 participants across three major hospitals.
    In my personal opinion, everyone should drink tea every morning.
    The FDA announced new clinical trial guidelines for herbal supplements.
    """
    claims = ClaimExtractor.extract_all_claims(article, max_claims=4)
    assert len(claims) >= 2
    claim_texts = " ".join([c["claim_text"] for c in claims])
    assert "drinking green tea reduces hypertension" in claim_texts or "hypertension" in claim_texts
    assert "FDA announced new clinical trial" in claim_texts or "FDA" in claim_texts

def test_is_url():
    assert ClaimExtractor.is_url("https://www.reuters.com/world/article") is True
    assert ClaimExtractor.is_url("http://factcheck.org") is True
    assert ClaimExtractor.is_url("The earth is flat and hollow") is False
