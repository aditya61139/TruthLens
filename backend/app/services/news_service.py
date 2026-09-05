import re
import urllib.parse
import xml.etree.ElementTree as ET
import httpx
from typing import List, Dict, Any
from rapidfuzz import fuzz

DEBUNK_KEYWORDS = [
    r"\b(debunked|false claim|hoax|fake news|myth|disproven|fact check|baseless|untrue|bogus|refutes|denies)\b"
]

CONFIRM_KEYWORDS = [
    r"\b(confirms|announces|officially|discovers|reveals|launches|approves|signs bill|passes|verified|study finds|reported|killed|dead|evacuated|flooded|struck)\b"
]

STOP_WORDS = {
    "the", "a", "an", "is", "are", "was", "were", "and", "or", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "that", "this", "it", "as", "be", "has", "have", "had", "will",
    "there", "near", "about", "did", "been"
}

class NewsCrossReferenceService:
    @staticmethod
    def calculate_relevance(claim_text: str, article_title: str) -> float:
        """
        Computes semantic and token relevance between claim and article headline.
        Ensures unrelated news stories with loose keyword overlap are rejected.
        """
        claim_clean = re.sub(r"[^\w\s]", "", claim_text.lower()).strip()
        title_clean = re.sub(r"[^\w\s]", "", article_title.lower()).strip()

        claim_tokens = set([w for w in claim_clean.split() if w not in STOP_WORDS and len(w) > 2])
        title_tokens = set([w for w in title_clean.split() if w not in STOP_WORDS and len(w) > 2])

        if not claim_tokens:
            return 0.0

        # Token intersection ratio
        overlap = claim_tokens.intersection(title_tokens)
        
        # If claim has 3 or more key tokens but only 1 overlaps, penalize heavily
        if len(claim_tokens) >= 3 and len(overlap) < 2:
            return 25.0

        overlap_ratio = len(overlap) / len(claim_tokens)

        # RapidFuzz token sort and token set ratios
        token_set_score = fuzz.token_set_ratio(claim_clean, title_clean)
        partial_score = fuzz.partial_ratio(claim_clean, title_clean)

        # Weighted combined relevance score (0 - 100)
        combined_score = (overlap_ratio * 45.0) + (token_set_score * 0.35) + (partial_score * 0.2)
        return min(100.0, combined_score)

    @classmethod
    async def fetch_news_consensus(cls, claim_text: str, min_relevance: float = 55.0) -> List[Dict[str, Any]]:
        """
        Queries Google News RSS feed and strictly filters candidate articles
        by relevance to the specific claim proposition.
        """
        query_words = [w for w in re.findall(r"\b[A-Za-z0-9-]{3,}\b", claim_text) if w.lower() not in STOP_WORDS]
        if not query_words:
            return []
        
        search_query = " ".join(query_words[:6])
        encoded_query = urllib.parse.quote(search_query)
        rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 TruthLens/1.0"
        }

        try:
            async with httpx.AsyncClient(timeout=7.0, follow_redirects=True, headers=headers) as client:
                response = await client.get(rss_url)
                if response.status_code != 200:
                    return []
                xml_text = response.text
        except Exception:
            return []

        results = []
        try:
            root = ET.fromstring(xml_text)
            channel = root.find("channel")
            if channel is None:
                return []

            items = channel.findall("item")
            for item in items[:8]:
                title_elem = item.find("title")
                link_elem = item.find("link")
                pub_date_elem = item.find("pubDate")
                source_elem = item.find("source")

                title = title_elem.text if title_elem is not None else ""
                link = link_elem.text if link_elem is not None else ""
                pub_date = pub_date_elem.text if pub_date_elem is not None else ""
                source_name = source_elem.text if source_elem is not None else "News Outlet"

                relevance = cls.calculate_relevance(claim_text, title)
                if relevance < min_relevance:
                    continue

                stance = "Reporting"
                verdict_hint = "Unverified"
                title_lower = title.lower()

                if any(re.search(pat, title_lower) for pat in DEBUNK_KEYWORDS):
                    stance = "Debunking / Refuting"
                    verdict_hint = "False"
                elif any(re.search(pat, title_lower) for pat in CONFIRM_KEYWORDS):
                    stance = "Corroborating / Confirming"
                    verdict_hint = "True"

                results.append({
                    "source_name": source_name,
                    "source_site": link,
                    "source_url": link,
                    "title": title,
                    "raw_rating": stance,
                    "normalized_verdict": verdict_hint,
                    "review_date": pub_date[:16] if pub_date else "Recent",
                    "claim_text": claim_text,
                    "claimant": "News Media Coverage",
                    "relevance_score": round(relevance, 1),
                    "confidence_contribution": min(85.0, 50.0 + (relevance * 0.35)),
                    "explanation": f"Reporting by {source_name} directly addresses this topic: '{title}'"
                })

                if len(results) >= 4:
                    break

        except Exception:
            return []

        return results
