import re
import urllib.parse
import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.services.news_service import NewsCrossReferenceService

CONFIRM_EVENT_KEYWORDS = [
    r"\b(killed|dead|evacuated|damaged|submerged|rescue|flooded|struck|hit|landslide|torrential|debris|destroyed|warning|declared)\b",
    r"\b(authorities confirm|officials said|reported|state media|emergency|disaster)\b"
]

class GoogleSearchService:
    @classmethod
    async def search_live_web(cls, claim_text: str, search_query: str) -> Dict[str, Any]:
        """
        Executes deterministic multi-tier web search without making extraneous Gemini calls:
        1. Google Custom Search JSON API (if CSE credentials configured)
        2. Direct Live Web Search Index (DuckDuckGo HTML)
        3. Google News RSS Feed Search
        
        Returns unified results with explicit metadata on search execution.
        """
        normalized_q = search_query or claim_text
        metadata = {
            "search_attempted": True,
            "search_query_used": normalized_q,
            "provider": "None",
            "raw_count": 0,
            "relevant_count": 0
        }

        # 1. Try Google Custom Search API if CSE key & CX present
        cse_key = settings.GOOGLE_SEARCH_API_KEY or settings.GOOGLE_API_KEY
        if cse_key and settings.GOOGLE_SEARCH_ENGINE_ID:
            cse_ev = await cls.search_google_custom_search(normalized_q)
            if cse_ev:
                metadata["provider"] = "Google Custom Search API"
                metadata["raw_count"] = len(cse_ev)
                metadata["relevant_count"] = len(cse_ev)
                return {
                    "metadata": metadata,
                    "evidence": cse_ev,
                    "verdict": cls._infer_verdict_from_evidence(cse_ev),
                    "confidence": 85.0,
                    "summary": "",
                    "why_bullets": []
                }

        # 2. Direct Live Web Search (Public Open Web Index)
        web_ev = await cls.search_open_web(normalized_q, claim_text)
        if web_ev:
            metadata["provider"] = "Live Web Search Index"
            metadata["raw_count"] = len(web_ev)
            metadata["relevant_count"] = len(web_ev)
            return {
                "metadata": metadata,
                "evidence": web_ev,
                "verdict": cls._infer_verdict_from_evidence(web_ev),
                "confidence": 85.0 if any(e.get("normalized_verdict") == "True" for e in web_ev) else 70.0,
                "summary": "",
                "why_bullets": []
            }

        # 3. Google News RSS Search with normalized query
        news_ev = await NewsCrossReferenceService.fetch_news_consensus(normalized_q, min_relevance=55.0)
        if news_ev:
            metadata["provider"] = "Google News Index"
            metadata["raw_count"] = len(news_ev)
            metadata["relevant_count"] = len(news_ev)
            return {
                "metadata": metadata,
                "evidence": news_ev,
                "verdict": cls._infer_verdict_from_evidence(news_ev),
                "confidence": 85.0 if any(e.get("normalized_verdict") == "True" for e in news_ev) else 70.0,
                "summary": "",
                "why_bullets": []
            }

        return {
            "metadata": metadata,
            "evidence": [],
            "verdict": "Unverified",
            "confidence": 35.0,
            "summary": "No directly relevant live news reports or web documentation found.",
            "why_bullets": []
        }

    @classmethod
    async def search_open_web(cls, query: str, original_claim: str) -> List[Dict[str, Any]]:
        """
        Retrieves real-time coverage using structured news consensus without brittle HTML scraping.
        """
        # First query live news consensus via Google News RSS
        results = await NewsCrossReferenceService.fetch_news_consensus(query, min_relevance=50.0)
        if not results and original_claim and original_claim != query:
            results = await NewsCrossReferenceService.fetch_news_consensus(original_claim, min_relevance=50.0)
        return results

    @classmethod
    async def search_google_custom_search(cls, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """
        Executes Google Web Search via Google Custom Search JSON API if API Key & Engine ID are provided.
        """
        api_key = settings.GOOGLE_SEARCH_API_KEY or settings.GOOGLE_API_KEY
        cx = settings.GOOGLE_SEARCH_ENGINE_ID
        if not api_key or not cx:
            return []

        url = "https://customsearch.googleapis.com/customsearch/v1"
        params = {
            "key": api_key,
            "cx": cx,
            "q": query,
            "num": min(num_results, 10)
        }

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                response = await client.get(url, params=params)
                if response.status_code != 200:
                    return []
                data = response.json()

            results = []
            for item in data.get("items", []):
                title = item.get("title", "")
                link = item.get("link", "")
                snippet = item.get("snippet", "")
                display_link = item.get("displayLink", "")

                relevance = NewsCrossReferenceService.calculate_relevance(query, f"{title} {snippet}")
                if relevance < 55.0:
                    continue

                pub_name = display_link.replace("www.", "").split(".")[0].title()
                is_confirmed = any(re.search(pat, f"{title} {snippet}", re.I) for pat in CONFIRM_EVENT_KEYWORDS)

                results.append({
                    "source_name": f"{pub_name}",
                    "source_site": display_link,
                    "source_url": link,
                    "title": title,
                    "raw_rating": "Corroborated / Reported" if is_confirmed else "Web Search Result",
                    "normalized_verdict": "True" if is_confirmed else "Unverified",
                    "review_date": "Latest",
                    "claim_text": query,
                    "claimant": "Google Web Index",
                    "relevance_score": round(relevance, 1),
                    "confidence_contribution": min(90.0, 55.0 + (relevance * 0.35)),
                    "explanation": f"{pub_name} reporting: \"{snippet[:180]}...\""
                })

            return results
        except Exception:
            return []

    @staticmethod
    def _infer_verdict_from_evidence(evidence: List[Dict[str, Any]]) -> str:
        if not evidence:
            return "Unverified"
        true_votes = sum(1 for e in evidence if e.get("normalized_verdict") == "True")
        false_votes = sum(1 for e in evidence if e.get("normalized_verdict") == "False")
        
        if false_votes >= 2:
            return "False"
        if true_votes >= 1:
            return "True"
        return "Unverified"
