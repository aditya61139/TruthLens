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
        Queries open live web search (DuckDuckGo HTML) to find real-time coverage without requiring API keys.
        """
        encoded_query = urllib.parse.quote(query)
        search_url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 TruthLens/1.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5"
        }

        try:
            async with httpx.AsyncClient(timeout=8.0, follow_redirects=True, headers=headers) as client:
                response = await client.get(search_url)
                if response.status_code != 200:
                    return []
                html_text = response.text
        except Exception:
            return []

        soup = BeautifulSoup(html_text, "html.parser")
        results = []
        
        result_divs = soup.find_all("div", class_=re.compile(r"result\b|results_links"))
        if not result_divs:
            result_divs = soup.find_all("div", class_="web-result")

        for div in result_divs[:8]:
            title_tag = div.find("a", class_=re.compile(r"result__a|result-title"))
            snippet_tag = div.find("a", class_=re.compile(r"result__snippet|snippet")) or div.find("div", class_=re.compile(r"result__snippet|snippet"))

            title = title_tag.get_text().strip() if title_tag else ""
            snippet = snippet_tag.get_text().strip() if snippet_tag else ""
            raw_url = title_tag["href"] if (title_tag and title_tag.has_attr("href")) else ""

            # Unquote redirect URL
            real_url = raw_url
            if "uddg=" in raw_url:
                parsed = urllib.parse.parse_qs(urllib.parse.urlparse(raw_url).query)
                if "uddg" in parsed:
                    real_url = parsed["uddg"][0]

            if not title or not snippet:
                continue

            # Calculate relevance
            combined_text = f"{title} {snippet}"
            relevance = NewsCrossReferenceService.calculate_relevance(query, combined_text)
            
            # If query is short entity query, also check original claim
            if relevance < 55.0 and original_claim:
                relevance = max(relevance, NewsCrossReferenceService.calculate_relevance(original_claim, combined_text))

            if relevance < 55.0:
                continue

            domain = urllib.parse.urlparse(real_url).netloc.replace("www.", "")
            pub_name = domain.split(".")[0].title() if domain else "News Source"

            is_confirmed = any(re.search(pat, combined_text, re.I) for pat in CONFIRM_EVENT_KEYWORDS)
            verdict_hint = "True" if is_confirmed else "Unverified"
            rating_label = "Corroborated / Reported" if is_confirmed else "Web Reporting"

            results.append({
                "source_name": pub_name,
                "source_site": domain,
                "source_url": real_url,
                "title": title,
                "raw_rating": rating_label,
                "normalized_verdict": verdict_hint,
                "review_date": "Recent / Ongoing",
                "claim_text": query,
                "claimant": "Live Web Reporting",
                "relevance_score": round(relevance, 1),
                "confidence_contribution": min(90.0, 60.0 + (relevance * 0.3)),
                "explanation": f"{pub_name} reporting: \"{snippet[:180]}...\""
            })

            if len(results) >= 4:
                break

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
