import json
import logging
import urllib.parse
from typing import Dict, Any, Optional, List
from app.core.config import settings
from app.services.gemini_rate_limiter import (
    GeminiRateLimiter,
    GeminiApiException,
    GeminiRateLimitException,
    GeminiNotFoundException,
    GeminiAuthException
)

logger = logging.getLogger("truthlens.gemini")

RAG_SYNTHESIS_SYSTEM_PROMPT = """You are TruthLens, an AI fact-checking and real-time event verification assistant. You will receive a USER_INPUT and a list of RETRIEVED_EVIDENCE items, each already labeled with a stance.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 0: CLASSIFY THE USER'S INPUT MODE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. MODE A — CLAIM VERIFICATION: User submits a statement/assertion to be fact-checked (e.g., "The sun rises from the west", "Water boils at 100C", "Vaccines alter DNA").
   → Deliver full fact-check (verdict, confidence, clause mapping, heuristics, sources, 360 summary).

2. MODE B — EVENT / INCIDENT QUERY: User asks a QUESTION about a recent event, disaster, or ongoing situation (e.g., "Is there a recent flash flood in India?", "What happened in the Turkey earthquake?", "Any updates on the Israel-Palestine conflict?").
   → Deliver comprehensive EVENT BRIEFING with event_meta, impact numbers, 360 summary, and cited sources.

3. MODE C — HYBRID: User makes a specific quantitative/causal claim tied to a recent event (e.g., "500 people died in the Assam floods", "The government sent no relief").
   → Deliver BOTH: fact-check the specific claim AND provide the comprehensive event briefing.

VERDICT RULES (For Mode A & Mode C):
- If the claim ALIGNS with established knowledge → truth_value: "TRUE", knowledge_certainty: "SETTLED", final_verdict: "TRUE — Established Knowledge"
- If the claim CONTRADICTS established knowledge → truth_value: "FALSE", knowledge_certainty: "SETTLED", final_verdict: "FALSE — Contradicts Established Knowledge"
- If the claim aligns with current evidence but the domain is actively debated → truth_value: "LIKELY_TRUE", knowledge_certainty: "DEBATED", final_verdict: "LIKELY TRUE — Under Active Debate"
- If the claim contradicts current evidence but the domain is actively debated → truth_value: "LIKELY_FALSE", knowledge_certainty: "DEBATED", final_verdict: "LIKELY FALSE — Under Active Debate"
- If evidence is insufficient to evaluate → truth_value: "UNVERIFIABLE", knowledge_certainty: "INSUFFICIENT", final_verdict: "UNVERIFIABLE — Insufficient Evidence"

CRITICAL GUARD RAIL:
Before rendering the final verdict, perform this consistency check:
- Review the Clause-by-Clause Assertion Mapping results.
- If ANY clause is marked "Debunked" or "False", the Final Verdict MUST NOT be "TRUE". Clause-level evaluations take precedence.

Output strictly as JSON:
{
  "mode": "Claim Verification | Event Query | Hybrid",
  "claim": "...",
  "truth_value": "TRUE | FALSE | LIKELY_TRUE | LIKELY_FALSE | MIXED | UNVERIFIABLE",
  "knowledge_certainty": "SETTLED | DEBATED | EMERGING | INSUFFICIENT",
  "final_verdict_display": "...",
  "confidence": 0-100,
  "reasoning_summary": "2-3 sentences",
  "event_meta": {
    "category_emoji": "🌊 | 🌍 | 🏛️ | 💰 | 🔬 | ⚖️ | 🌋 | 🔥 | 🌀 | 📰",
    "category_label": "Natural Disaster — Flooding | Geopolitics — Armed Conflict | Politics — Governance & Election | etc.",
    "title": "Clear descriptive event title",
    "region": "Country / State / City affected",
    "date_range": "When the event occurred or ongoing range",
    "status": "🔴 Ongoing | 🟡 Developing | 🟢 Resolved"
  },
  "evidence_analysis": [
    {"source": "...", "stance": "ENTAILS|CONTRADICTS|NEUTRAL", "reason": "..."}
  ],
  "claim_breakdown": [
    {"clause": "...", "status": "debunked | verified | accurate | misleading | unverified", "note": "..."}
  ],
  "quick_summary": {
    "what_happened": "3-5 sentences covering the core event (Who, What, When, Where, Scale, Specific locations/districts).",
    "full_context": "3-5 sentences of historical/structural/climate context and why this matters.",
    "timeline": ["YYYY-MM-DD — Key development", "..."],
    "impact_numbers": {
      "deaths": "[number] confirmed / feared or N/A",
      "displaced": "[number] people / districts or N/A",
      "areas_affected": "[list of specific districts/cities]",
      "damage": "[infrastructure, agriculture, economic loss details]",
      "rescue": "[agencies involved, operations, numbers rescued]"
    },
    "key_parties": [{"name": "Entity Name", "role": "Role / Involvement description"}],
    "key_data": ["Important metric or data point", "..."],
    "perspectives": [{"party": "Source or Perspective Name", "stance": "Summary of viewpoint"}],
    "current_status": "Where things stand right now (2-3 sentences).",
    "key_takeaway": "One-sentence memorable bottom line."
  },
  "sources_and_reading": [
    {
      "source_name": "Publication or Organization Name",
      "title": "Exact headline / title",
      "url": "https://...",
      "date_published": "YYYY-MM-DD or Date not available",
      "source_type": "[🟢 Primary Source] | [🔵 Major News Outlet] | [🟡 Fact-Checker] | [🟠 Domain Expert / Academic] | [⚪ Other / General]",
      "paywall": false,
      "archive_url": "https://archive.org/..."
    }
  ]
}

FEW-SHOT EXAMPLE:
CLAIM: "sun rises from west"
RETRIEVED_EVIDENCE:
- Stanford Solar Center: "the Sun rises due east" [stance: CONTRADICTS]
- Wikipedia (Sun path): "The Sun rises in the east" [stance: CONTRADICTS]
CORRECT OUTPUT:
{
  "claim": "sun rises from west",
  "truth_value": "FALSE",
  "knowledge_certainty": "SETTLED",
  "final_verdict_display": "FALSE — Contradicts Established Knowledge",
  "confidence": 97,
  "reasoning_summary": "Multiple credible astronomical sources confirm the sun rises in the east, directly contradicting the claim that it rises in the west. This is a well-established, non-disputed fact.",
  "evidence_analysis": [
    {"source": "Stanford Solar Center", "stance": "CONTRADICTS", "reason": "States the sun rises due east, not west."},
    {"source": "Wikipedia - Sun path", "stance": "CONTRADICTS", "reason": "Confirms sunrise position is east, near arrow in referenced diagram."}
  ],
  "claim_breakdown": [
    {"clause": "sun rises from west", "status": "debunked", "note": "Contradicts eastward rotation of Earth"}
  ],
  "quick_summary": {
    "what_happened": "The claim asserts that the Sun rises in the west, which is physically and astronomically incorrect. On Earth, the Sun appears to rise in the eastern horizon and set in the west every solar day.",
    "full_context": "The apparent movement of celestial bodies across the sky is governed by Earth's prograde (counter-clockwise/eastward) rotation on its polar axis. This principle has been scientifically verified for millennia and forms the foundation of celestial mechanics and timekeeping.",
    "timeline": [
      "Ancient History — Early astronomers establish geodetic and celestial observation of solar paths.",
      "1543 — Nicolaus Copernicus publishes heliocentric model explaining apparent planetary rotation.",
      "Modern Era — Satellite observations confirm continuous eastward planetary rotation at ~1670 km/h at the equator."
    ],
    "key_parties": [
      {"name": "Earth", "role": "Rotating planetary body with eastward rotation axis."},
      {"name": "The Sun", "role": "Central star around which Earth orbits."}
    ],
    "key_data": [
      "Earth rotates eastward at approximately 1,670 km/h (1,037 mph) at the equator.",
      "One full rotation occurs every 23 hours, 56 minutes, and 4 seconds (sidereal day)."
    ],
    "perspectives": [
      {"party": "Global Scientific Consensus", "stance": "Eastward planetary rotation universally dictates sunrise in the east without exception."}
    ],
    "current_status": "Undisputed fundamental principle of terrestrial physics and astronomy.",
    "key_takeaway": "The sun universally rises in the east on Earth due to eastward axial rotation; claiming it rises in the west is completely false."
  },
  "sources_and_reading": [
    {
      "source_name": "NASA Solar System Exploration",
      "title": "Earth: In Depth & Planetary Motion",
      "url": "https://science.nasa.gov/solar-system/",
      "date_published": "2024-01-15",
      "source_type": "[🟢 Primary Source]",
      "paywall": false
    },
    {
      "source_name": "Stanford Solar Center",
      "title": "Solar Physics & Sun Path Guide",
      "url": "http://solar-center.stanford.edu/",
      "date_published": "2023-08-20",
      "source_type": "[🟠 Domain Expert / Academic]",
      "paywall": false
    },
    {
      "source_name": "Encyclopedia Britannica",
      "title": "Sunrise and Sunset Mechanics",
      "url": "https://www.britannica.com/science/sunrise",
      "date_published": "2024-02-10",
      "source_type": "[🟠 Domain Expert / Academic]",
      "paywall": false
    }
  ]
}"""

CANDIDATE_MODELS = [
    settings.GEMINI_MODEL or "gemini-3.6-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash-lite",
    "gemini-flash-latest"
]

class GeminiSynthesisService:
    @classmethod
    async def execute_unified_evaluation(
        cls,
        claim_text: str,
        claim_type: str,
        reranked_evidence: List[Dict[str, Any]],
        is_time_sensitive: bool = False,
        search_query: Optional[str] = None,
        use_search_grounding: bool = False
    ) -> Dict[str, Any]:
        """
        Executes AT MOST ONE single unified Gemini call per user query using
        the RAG-based stance detection and verdict synthesis prompt.
        Protected by GeminiRateLimiter (15 RPM max, serialization lock, exponential backoff).
        """
        api_key = settings.GEMINI_API_KEY or settings.GOOGLE_API_KEY
        if not api_key:
            return {"success": False, "error": None, "reason": "No API key configured."}

        # Build stance-annotated evidence block for the prompt
        evidence_lines = []
        for doc in reranked_evidence[:5]:
            source = doc.get("source_name") or doc.get("source_site") or "Web Source"
            snippet = doc.get("explanation") or doc.get("title") or ""
            stance = doc.get("stance", "NEUTRAL")
            evidence_lines.append(f"- {source}: \"{snippet}\" [stance: {stance}]")

        evidence_str = "\n".join(evidence_lines) if evidence_lines else "- No external documents retrieved."

        user_content = f"""CLAIM: "{claim_text}"
PRE-CLASSIFIED CLAIM_TYPE: {claim_type}
RETRIEVED_EVIDENCE:
{evidence_str}

Please generate the structured JSON verdict synthesis."""

        def _call_gemini_with_model(model_name: str):
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=api_key)
            config = types.GenerateContentConfig(
                system_instruction=RAG_SYNTHESIS_SYSTEM_PROMPT,
                response_mime_type="application/json"
            )
            if use_search_grounding:
                config.tools = [types.Tool(google_search=types.GoogleSearch())]

            logger.info(f"[Gemini RAG Synthesis] Invoking model '{model_name}' (Search Grounding: {use_search_grounding})")
            return client.models.generate_content(
                model=model_name,
                contents=user_content,
                config=config
            )

        def _call_gemini():
            # Try primary model, fallback if 404
            last_err = None
            for model_name in CANDIDATE_MODELS:
                try:
                    return _call_gemini_with_model(model_name)
                except Exception as e:
                    err_str = str(e).lower()
                    if "404" in err_str or "not found" in err_str:
                        logger.warning(f"[Gemini RAG] Model '{model_name}' returned 404, trying fallback candidate...")
                        last_err = e
                        continue
                    raise e
            if last_err:
                raise last_err
            raise Exception("No valid Gemini model available.")

        try:
            response = await GeminiRateLimiter.execute_with_retry(_call_gemini)
            raw_text = response.text.strip() if hasattr(response, "text") and response.text else ""
            
            # Clean markdown JSON wraps if present
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.startswith("```"):
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
            raw_text = raw_text.strip()

            parsed = json.loads(raw_text)

            # Standardize truth_value
            raw_tv = (parsed.get("truth_value") or parsed.get("verdict") or "UNVERIFIABLE").strip().upper()
            if raw_tv in ["TRUE", "VERIFIED"]:
                normalized_truth_value = "True"
            elif raw_tv in ["FALSE", "DEBUNKED"]:
                normalized_truth_value = "False"
            elif raw_tv == "LIKELY_TRUE":
                normalized_truth_value = "Likely True"
            elif raw_tv == "LIKELY_FALSE":
                normalized_truth_value = "Likely False"
            elif raw_tv in ["MIXED", "DISPUTED", "MISLEADING"]:
                normalized_truth_value = "Misleading"
            elif raw_tv == "SATIRE":
                normalized_truth_value = "Satire"
            else:
                normalized_truth_value = "Unverifiable"

            # Standardize knowledge_certainty
            raw_kc = (parsed.get("knowledge_certainty") or parsed.get("claim_type") or "EMERGING").strip().upper()
            if "SETTLED" in raw_kc:
                normalized_certainty = "Settled Knowledge"
            elif "DEBATE" in raw_kc or "CONTESTED" in raw_kc:
                normalized_certainty = "Under Active Debate"
            elif "INSUFFICIENT" in raw_kc or "UNVERIFIABLE" in raw_kc:
                normalized_certainty = "Insufficient Evidence"
            else:
                normalized_certainty = "Emerging / Current Event"

            # Build or use final_verdict_display
            final_display = parsed.get("final_verdict_display")
            if not final_display:
                if normalized_truth_value == "True" and normalized_certainty == "Settled Knowledge":
                    final_display = "TRUE — Established Knowledge"
                elif normalized_truth_value == "False" and normalized_certainty == "Settled Knowledge":
                    final_display = "FALSE — Contradicts Established Knowledge"
                elif normalized_truth_value == "Likely True":
                    final_display = "LIKELY TRUE — Under Active Debate"
                elif normalized_truth_value == "Likely False":
                    final_display = "LIKELY FALSE — Under Active Debate"
                elif normalized_truth_value == "Satire":
                    final_display = "SATIRE / PARODY"
                elif normalized_truth_value in ["Unverifiable", "Unverified"]:
                    final_display = "UNVERIFIABLE — Insufficient Evidence"
                elif normalized_truth_value == "True":
                    final_display = "TRUE / VERIFIED"
                elif normalized_truth_value == "False":
                    final_display = "FALSE"
                else:
                    final_display = "MISLEADING"

            # Backward-compatible verdict
            normalized_verdict = normalized_truth_value if normalized_truth_value in ["True", "False", "Misleading", "Satire"] else "Unverified"

            # Parse grounding evidence if provided
            grounding_evidence = []
            if hasattr(response, "candidates") and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, "grounding_metadata") and candidate.grounding_metadata:
                    chunks = getattr(candidate.grounding_metadata, "grounding_chunks", [])
                    for chunk in chunks:
                        web = getattr(chunk, "web", None)
                        if web:
                            uri = getattr(web, "uri", "")
                            title = getattr(web, "title", "Google Search Citation")
                            if uri:
                                domain = urllib.parse.urlparse(uri).netloc.replace("www.", "")
                                grounding_evidence.append({
                                    "source_name": domain.split(".")[0].title() or "Google Search",
                                    "source_site": domain,
                                    "source_url": uri,
                                    "title": title,
                                    "raw_rating": "Google Search Grounding",
                                    "normalized_verdict": normalized_verdict,
                                    "stance": "ENTAILS" if normalized_truth_value in ["True", "Likely True"] else ("CONTRADICTS" if normalized_truth_value in ["False", "Likely False"] else "NEUTRAL"),
                                    "review_date": "Latest",
                                    "claim_text": claim_text,
                                    "claimant": "Google Web Grounding",
                                    "confidence_contribution": 90.0,
                                    "explanation": f"Google Search Grounding citation: {title}"
                                })

            raw_mode = parsed.get("mode", "Claim Verification").strip()
            if "Event" in raw_mode:
                detected_mode = "Event Query"
            elif "Hybrid" in raw_mode:
                detected_mode = "Hybrid"
            else:
                detected_mode = "Claim Verification"

            return {
                "success": True,
                "data": {
                    "mode": detected_mode,
                    "claim": parsed.get("claim", claim_text),
                    "truth_value": normalized_truth_value,
                    "knowledge_certainty": normalized_certainty,
                    "final_verdict_display": final_display,
                    "claim_type": parsed.get("claim_type", claim_type),
                    "event_meta": parsed.get("event_meta", {}),
                    "verdict": normalized_verdict,
                    "confidence": float(parsed.get("confidence", 75.0)),
                    "summary": parsed.get("reasoning_summary", ""),
                    "evidence_analysis": parsed.get("evidence_analysis", []),
                    "claim_breakdown": parsed.get("claim_breakdown", []),
                    "quick_summary": parsed.get("quick_summary", {}),
                    "sources_and_reading": parsed.get("sources_and_reading", []),
                    "raw_json": parsed
                },
                "grounding_evidence": grounding_evidence,
                "error": None
            }

        except GeminiRateLimitException as e:
            return {"success": False, "data": None, "error": {"code": e.code, "message": e.message, "details": e.details}}
        except GeminiNotFoundException as e:
            return {"success": False, "data": None, "error": {"code": e.code, "message": e.message, "details": e.details}}
        except GeminiAuthException as e:
            return {"success": False, "data": None, "error": {"code": e.code, "message": e.message, "details": e.details}}
        except GeminiApiException as e:
            return {"success": False, "data": None, "error": {"code": e.code, "message": e.message, "details": e.details}}
        except Exception as e:
            logger.error(f"[Gemini RAG Synthesis] Unexpected failure: {e}", exc_info=True)
            return {
                "success": False,
                "data": None,
                "error": {
                    "code": "API_UNEXPECTED_ERROR",
                    "message": "Encountered an unexpected error while contacting AI verification engine.",
                    "details": str(e)
                }
            }
