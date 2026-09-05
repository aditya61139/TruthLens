import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.models import Base, PublisherCredibility
from app.services.credibility_service import PublisherCredibilityService
from app.services.factcheck_service import FactCheckService

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Seed test publisher
    session.add(PublisherCredibility(
        domain="reuters.com",
        name="Reuters",
        category="Fact-Checker",
        bias_rating="Center",
        factual_reporting="Very High",
        credibility_score=99,
        country="Global"
    ))
    session.add(PublisherCredibility(
        domain="infowars.com",
        name="InfoWars",
        category="Conspiracy/Fake",
        bias_rating="Extreme",
        factual_reporting="Very Low",
        credibility_score=12,
        country="USA"
    ))
    session.commit()
    yield session
    session.close()

def test_extract_domain():
    assert PublisherCredibilityService.extract_domain("https://www.reuters.com/fact-check") == "reuters.com"
    assert PublisherCredibilityService.extract_domain("Check this out at infowars.com/story") == "infowars.com"

def test_get_publisher_info(db_session):
    reuters_info = PublisherCredibilityService.get_publisher_info(db_session, "https://www.reuters.com/news")
    assert reuters_info["matched"] is True
    assert reuters_info["credibility_score"] == 99
    assert reuters_info["bias_rating"] == "Center"

    infowars_info = PublisherCredibilityService.get_publisher_info(db_session, "infowars.com")
    assert infowars_info["matched"] is True
    assert infowars_info["credibility_score"] == 12
    assert "High-Risk" in infowars_info["trust_tier"]

def test_normalize_rating():
    assert FactCheckService.normalize_rating("Pants on Fire") == "False"
    assert FactCheckService.normalize_rating("mostly false") == "False"
    assert FactCheckService.normalize_rating("Misleading context") == "Misleading"
    assert FactCheckService.normalize_rating("Half True") == "Misleading"
    assert FactCheckService.normalize_rating("Correct Attribution") == "True"
    assert FactCheckService.normalize_rating("Satire") == "Satire"
