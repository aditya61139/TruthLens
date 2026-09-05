import re
import urllib.parse
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.db.models import PublisherCredibility

class PublisherCredibilityService:
    @staticmethod
    def extract_domain(url_or_text: str) -> Optional[str]:
        """Extracts clean domain from URL or string."""
        url_or_text = url_or_text.strip()
        if not url_or_text:
            return None

        # Check if URL
        if "://" in url_or_text or url_or_text.startswith("www."):
            parsed = urllib.parse.urlparse(url_or_text if "://" in url_or_text else "https://" + url_or_text)
            domain = parsed.netloc.lower()
            if domain.startswith("www."):
                domain = domain[4:]
            return domain

        # Check if contains domain-like pattern (e.g., 'reuters.com')
        domain_match = re.search(r"\b([a-zA-Z0-9-]+\.[a-zA-Z]{2,}(?:\.[a-zA-Z]{2,})?)\b", url_or_text.lower())
        if domain_match:
            domain = domain_match.group(1)
            if domain.startswith("www."):
                domain = domain[4:]
            return domain

        return None

    @classmethod
    def get_publisher_info(cls, db: Session, domain_or_name: str) -> Dict[str, Any]:
        """Looks up publisher credibility, bias, and reporting standards."""
        if not domain_or_name:
            return cls._get_default_unknown_info("Unknown / Unspecified Source")

        domain = cls.extract_domain(domain_or_name) or domain_or_name.lower().strip()
        
        # 1. Exact match on domain
        pub = db.query(PublisherCredibility).filter(PublisherCredibility.domain == domain).first()
        
        # 2. Try subdomain stripping (e.g. news.bbc.co.uk -> bbc.co.uk)
        if not pub and "." in domain:
            parts = domain.split(".")
            if len(parts) > 2:
                main_domain = ".".join(parts[-2:])
                pub = db.query(PublisherCredibility).filter(PublisherCredibility.domain == main_domain).first()

        # 3. Try name match
        if not pub:
            pub = db.query(PublisherCredibility).filter(
                PublisherCredibility.name.ilike(f"%{domain_or_name.strip()}%")
            ).first()

        if pub:
            return {
                "matched": True,
                "domain": pub.domain,
                "name": pub.name,
                "category": pub.category,
                "bias_rating": pub.bias_rating,
                "factual_reporting": pub.factual_reporting,
                "credibility_score": pub.credibility_score,
                "trust_tier": cls._get_trust_tier(pub.credibility_score),
                "country": pub.country,
                "notes": pub.notes
            }

        # If not in DB, guess heuristic tier based on domain extension or return neutral
        return cls._get_default_unknown_info(domain_or_name)

    @staticmethod
    def _get_trust_tier(score: int) -> str:
        if score >= 90:
            return "Top-Tier Credible (Verified / Scientific)"
        elif score >= 75:
            return "Generally Reliable / Mainstream"
        elif score >= 55:
            return "Mixed Reliability / Editorial Bias"
        elif score >= 40:
            return "Questionable / Low Reliability"
        else:
            return "High-Risk / Conspiracy / Fake News"

    @classmethod
    def _get_default_unknown_info(cls, name_or_domain: str) -> Dict[str, Any]:
        is_gov_edu = any(name_or_domain.lower().endswith(ext) for ext in [".gov", ".edu", ".mil", ".ac.uk", ".gov.uk", ".gov.in"])
        score = 92 if is_gov_edu else 50
        return {
            "matched": False,
            "domain": name_or_domain,
            "name": name_or_domain.title() if not "." in name_or_domain else name_or_domain,
            "category": "Educational/Government" if is_gov_edu else "Unranked Publisher",
            "bias_rating": "Center" if is_gov_edu else "Unassessed",
            "factual_reporting": "High" if is_gov_edu else "Unassessed",
            "credibility_score": score,
            "trust_tier": "Official Public / Academic Entity" if is_gov_edu else "Unrated Source",
            "country": "Global",
            "notes": "Domain verified as official educational/government registry." if is_gov_edu else "Publisher not currently in the local reference database."
        }
