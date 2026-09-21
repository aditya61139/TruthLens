import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Boolean
from app.db.database import Base

def get_utc_now():
    return datetime.datetime.now(datetime.timezone.utc)

class QueryCache(Base):
    __tablename__ = "query_cache"

    id = Column(Integer, primary_key=True, index=True)
    query_hash = Column(String(64), index=True, nullable=False)
    normalized_query = Column(Text, index=True, nullable=False)
    input_text = Column(Text, nullable=False)
    extracted_claim = Column(Text, nullable=False)
    verdict = Column(String(32), nullable=False)  # True, False, Misleading, Unverified, Satire
    confidence = Column(Float, nullable=False)   # 0.0 - 100.0
    category = Column(String(64), default="General")
    sources_json = Column(Text, default="[]")
    red_flags_json = Column(Text, default="{}")
    explanation_json = Column(Text, default="{}")
    credibility_json = Column(Text, default="{}")
    access_count = Column(Integer, default=1)
    created_at = Column(DateTime, default=get_utc_now)
    expires_at = Column(DateTime, nullable=False)


class ClaimHistory(Base):
    __tablename__ = "claim_history"

    id = Column(Integer, primary_key=True, index=True)
    input_text = Column(Text, nullable=False)
    extracted_claim = Column(Text, nullable=False)
    verdict = Column(String(32), nullable=False)
    confidence = Column(Float, nullable=False)
    category = Column(String(64), default="General")
    sources_count = Column(Integer, default=0)
    red_flag_score = Column(Float, default=0.0)
    explanation_summary = Column(Text, default="")
    created_at = Column(DateTime, default=get_utc_now)


class TrendingClaim(Base):
    __tablename__ = "trending_claims"

    id = Column(Integer, primary_key=True, index=True)
    claim_text = Column(Text, nullable=False)
    verdict = Column(String(32), nullable=False)
    confidence = Column(Float, nullable=False)
    category = Column(String(64), default="General")
    summary = Column(Text, nullable=False)
    source_name = Column(String(128), default="")
    source_url = Column(Text, default="")
    search_volume = Column(Integer, default=100)
    last_checked = Column(DateTime, default=get_utc_now)


class PublisherCredibility(Base):
    __tablename__ = "publisher_credibility"

    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String(128), unique=True, index=True, nullable=False)
    name = Column(String(128), nullable=False)
    category = Column(String(64), default="Mainstream") # Mainstream, Fact-Checker, Satire, Conspiracy, State
    bias_rating = Column(String(64), default="Center") # Left, Lean Left, Center, Lean Right, Right, Extreme, Satire
    factual_reporting = Column(String(64), default="High") # Very High, High, Mostly Factual, Mixed, Low, Very Low
    credibility_score = Column(Integer, default=75) # 0 - 100
    country = Column(String(64), default="Global")
    notes = Column(Text, default="")
    mbfc_url = Column(Text, default="")


class UserFeedback(Base):
    __tablename__ = "user_feedback"

    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(String(64), nullable=True)
    claim_text = Column(Text, nullable=False)
    given_verdict = Column(String(32), nullable=False)
    feedback_type = Column(String(32), nullable=False) # helpful, incorrect
    suggested_verdict = Column(String(32), nullable=True)
    comments = Column(Text, nullable=True)
    created_at = Column(DateTime, default=get_utc_now)
