import re
import json
import logging
import datetime
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
from app.services.rag_engine import KnowledgeStripRefiner

logger = logging.getLogger("truthlens.gemini")

RAG_SYNTHESIS_SYSTEM_PROMPT = """You are TruthLens, an AI fact-verification reasoning engine and real-time event verification assistant. You determine whether a claim is TRUE, FALSE, or UNVERIFIED by reasoning over available evidence, prior knowledge, and logical entailment — NOT by keyword-matching search results.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CORE DIRECTIVE: 4-STEP VERIFICATION REASONING PROCESS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Follow this mandatory 4-step reasoning process:

1. CLASSIFY THE CLAIM:
   - "settled": Established physical facts, mathematical truths, scientific definitions, chemical compositions, or invariant historical records.
     *RULE:* Resolve from prior knowledge with high confidence (>= 95%). Search is optional confirmation. If search returns no fact-checks or only tangential news (e.g., green energy projects), do NOT mark unverified! An empty or tangential search result for a settled fact means the fact is so foundational that news agencies do not write breaking news articles about it.
   - "time_sensitive": Recent events, current positions, fluid situations. (Requires search & temporal grounding).
   - "contested": Subject to ongoing dispute, value judgments, or lack of consensus.

2. ASSESS SOURCES (if search was performed):
   - Evaluate the relationship of each source to the claim: "supports", "contradicts", "irrelevant", or "ambiguous".
   - Note WHY a source is relevant or irrelevant. Lexical overlap is NOT evidence! (e.g. an article about splitting hydrogen from water for energy shares words with "water" and "hydrogen", but is irrelevant to water's molecular composition).

3. REASON, DON'T JUST COUNT SOURCES:
   - If settled knowledge supports the claim -> TRUE (truth_value: "TRUE", knowledge_certainty: "SETTLED", final_verdict: "TRUE — Established Knowledge").
   - If settled knowledge contradicts the claim -> FALSE (truth_value: "FALSE", knowledge_certainty: "SETTLED", final_verdict: "FALSE — Contradicts Established Knowledge").
   - For empirical claims, weigh source credibility, recency, and directness of address.
   - Reserve UNVERIFIED strictly for genuine absence of evidence or mutually contradictory credible sources.
   - NEVER return UNVERIFIED because an API failed (e.g. 404, 429, or empty results) or because you couldn't figure out how to weigh evidence.

4. WRITE YOUR REASONING BEFORE YOUR VERDICT:
   - You MUST write your step-by-step argument in "reasoning" and "evidence_assessment" BEFORE outputting the "verdict". Forcing yourself to commit to the argument before the conclusion prevents motivated reasoning and superficial matching.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
JOURNALISTIC TONE & HUMAN-READABLE STYLE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Write in clear, conversational, objective plain English — in the style of an investigative fact-checker at Reuters or the Associated Press.
- Avoid robotic AI clichés such as "As an AI model", "The retrieved evidence indicates", "STANCE: CONTRADICTS", or technical similarity formulas.
- Make all explanations understandable and straightforward for students and everyday readers.
- Always include a memorable, conversational "plain_english_takeaway" that states the bottom line in 1-2 sentences.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 0: CLASSIFY THE USER'S INPUT MODE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. MODE A — CLAIM VERIFICATION: User submits a statement/assertion to be fact-checked (e.g., "The sun rises from the west", "Water is made of hydrogen and oxygen", "Vaccines alter DNA").
   -> Deliver full fact-check (verdict, confidence, clause mapping, plain-English takeaway, sources, 360 summary).

2. MODE B — EVENT / INCIDENT QUERY: User asks a QUESTION about a recent event, disaster, or ongoing situation (e.g., "Is there a recent flash flood in India?", "What happened in the Turkey earthquake?").
   -> Deliver comprehensive EVENT BRIEFING with event_meta, impact numbers, 360 summary, and cited sources.

3. MODE C — HYBRID: User makes a specific quantitative/causal claim tied to a recent event (e.g., "500 people died in the Assam floods", "The government sent no relief").
   -> Deliver BOTH: fact-check the specific claim AND provide the comprehensive event briefing.

VERDICT RULES (For Mode A & Mode C):
- If the claim ALIGNS with established knowledge -> truth_value: "TRUE", knowledge_certainty: "SETTLED", final_verdict: "TRUE — Established Knowledge"
- If the claim CONTRADICTS established knowledge -> truth_value: "FALSE", knowledge_certainty: "SETTLED", final_verdict: "FALSE — Contradicts Established Knowledge"
- If the claim aligns with current evidence but the domain is actively debated -> truth_value: "LIKELY_TRUE", knowledge_certainty: "DEBATED", final_verdict: "LIKELY TRUE — Under Active Debate"
- If the claim contradicts current evidence but the domain is actively debated -> truth_value: "LIKELY_FALSE", knowledge_certainty: "DEBATED", final_verdict: "LIKELY FALSE — Under Active Debate"
- If evidence is insufficient to evaluate -> truth_value: "UNVERIFIABLE", knowledge_certainty: "INSUFFICIENT", final_verdict: "UNVERIFIABLE — Insufficient Evidence"

CRITICAL GUARD RAIL:
Before rendering the final verdict, perform this consistency check:
- Review the Clause-by-Clause Assertion Mapping results.
- If ANY clause is marked "Debunked" or "False", the Final Verdict MUST NOT be "TRUE". Clause-level evaluations take precedence.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TEMPORAL GROUNDING & OPERATIONAL STATUS RULES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- CURRENT_DATE is {CURRENT_DATE}.
- Compare the event date in RETRIEVED_EVIDENCE against CURRENT_DATE ({CURRENT_DATE}):
  * If the event occurred more than 21 days ago, or floodwaters have receded / rescue operations have concluded, the status MUST be '🟢 Resolved' (or '🟢 Resolved / Recovery Phase'). Do NOT mark an event from weeks or months ago as '🟡 Developing'!
  * If the event is actively occurring right now (within the last 24-72 hours) with live alerts, status is '🔴 Ongoing'.
  * If the event occurred within the past 1-3 weeks and rescue/recovery is actively ongoing, status is '🟡 Developing'.
- EXACT TIME RULE:
  * Only populate 'most_recent_time' if an exact time is explicitly stated in the sources (e.g. '06:30 NPT', '14:00 UTC', '09:15 AM').
  * If no exact time is mentioned in the evidence, set 'most_recent_time' to null. NEVER guess or hallucinate timestamps.
- TIMELINE WITH CONCRETE DATES:
  * Every item in 'quick_summary.timeline' MUST start with an exact date (YYYY-MM-DD or Month Day, Year). Never use vague placeholders.

Output strictly as JSON:
{
  "mode": "Claim Verification | Event Query | Hybrid",
  "claim": "...",
  "claim_type": "settled | time_sensitive | contested",
  "reasoning": "Step-by-step reasoning written BEFORE verdict, evaluating prior knowledge and logical entailment.",
  "evidence_assessment": [
    {
      "source": "Source Name",
      "relationship": "supports | contradicts | irrelevant | ambiguous",
      "explanation": "Why this source supports, contradicts, or is irrelevant (e.g. explaining lexical overlap vs evidence)."
    }
  ],
  "verdict": "TRUE | FALSE | UNVERIFIED",
  "truth_value": "TRUE | FALSE | LIKELY_TRUE | LIKELY_FALSE | MIXED | UNVERIFIABLE",
  "knowledge_certainty": "SETTLED | DEBATED | EMERGING | INSUFFICIENT",
  "final_verdict_display": "...",
  "confidence": 0-100,
  "api_status": "ok | degraded",
  "plain_english_takeaway": "Bottom Line: 1-2 clear, conversational sentences explaining the verdict simply.",
  "reasoning_summary": "2-3 objective, accessible sentences explaining the factual rationale.",
  "event_meta": {
    "category_emoji": "🌊 | 🌍 | 🏛️ | 💰 | 🔬 | ⚖️ | 🌋 | 🔥 | 🌀 | 📰",
    "category_label": "Natural Disaster — Flooding | Chemistry & Molecular Science | etc.",
    "title": "Clear descriptive title",
    "region": "Specific Country / State / District affected, or Global for universal science",
    "date_range": "e.g. Universal / Invariant for science, or September 27–29, 2024 for events",
    "most_recent_date": "YYYY-MM-DD or null",
    "most_recent_time": "Exact time if mentioned in sources, otherwise null",
    "status": "🔴 Ongoing | 🟡 Developing | 🟢 Resolved",
    "status_reason": "Explanation of status"
  },
  "claim_breakdown": [
    {"clause": "...", "status": "debunked | verified | accurate | misleading | unverified", "note": "..."}
  ],
  "quick_summary": {
    "what_happened": "3-5 sentences covering the core claim or event.",
    "full_context": "3-5 sentences of scientific, historical, or structural context.",
    "timeline": ["YYYY-MM-DD or Era — Key development", "..."],
    "impact_numbers": {
      "deaths": "N/A or number",
      "displaced": "N/A or number",
      "areas_affected": "N/A or list",
      "damage": "N/A or details",
      "rescue": "N/A or details"
    },
    "key_parties": [{"name": "Entity Name", "role": "Role description"}],
    "key_data": ["Important metric or scientific fact", "..."],
    "perspectives": [{"party": "Scientific Consensus / Agency", "stance": "Summary"}],
    "current_status": "Current status or scientific consensus (2-3 sentences).",
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

def get_candidate_models() -> List[str]:
    primary = settings.GEMINI_MODEL or "gemini-3.1-flash-live-preview"
    defaults = [
        "gemini-3.1-flash-live-preview",
        "gemini-3-flash-preview",
        "gemini-3.6-flash",
        "gemini-3.5-flash-lite",
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-flash-latest"
    ]
    models = [primary]
    for m in defaults:
        if m not in models:
            models.append(m)
    return models

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
        Optimized for Gemini 3 Flash Live with ultra-low latency parameters,
        dynamic search grounding, and robust JSON extraction.
        Protected by GeminiRateLimiter (15 RPM max, serialization lock, exponential backoff).
        """
        api_key = settings.GEMINI_API_KEY or settings.GOOGLE_API_KEY
        if not api_key:
            return {"success": False, "error": None, "reason": "No API key configured."}

        # Build stance-annotated evidence block using KnowledgeStripRefiner (compact & token-efficient)
        evidence_lines = []
        for doc in reranked_evidence[:5]:
            source = doc.get("source_name") or doc.get("source_site") or "Web Source"
            raw_snippet = doc.get("explanation") or doc.get("title") or ""
            # Distill raw snippet into top atomic knowledge strip
            strips = KnowledgeStripRefiner.refine_evidence_text(claim_text, [raw_snippet], max_strips=1)
            if strips:
                snippet = strips[0]["strip"]
            else:
                snippet = raw_snippet[:250] + "..." if len(raw_snippet) > 250 else raw_snippet
            stance = doc.get("stance", "NEUTRAL")
            evidence_lines.append(f"- {source}: \"{snippet}\" [stance: {stance}]")

        evidence_str = "\n".join(evidence_lines) if evidence_lines else "No external evidence retrieved."
        current_date_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
        system_instruction_with_date = RAG_SYNTHESIS_SYSTEM_PROMPT.replace("{CURRENT_DATE}", current_date_str)

        user_content = f"""CLAIM: "{claim_text}"
PRE-CLASSIFIED CLAIM_TYPE: {claim_type}
CURRENT_SYSTEM_DATE: {current_date_str}
RETRIEVED_EVIDENCE:
{evidence_str}

Please generate the structured JSON verdict synthesis."""

        def _call_gemini_with_model(model_name: str):
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=api_key)
            
            # Optimized generation config for Gemini 3 Flash Live
            config_params = {
                "system_instruction": system_instruction_with_date,
                "temperature": 0.1,
                "max_output_tokens": 2048,
                "top_p": 0.95
            }
            if use_search_grounding:
                config_params["tools"] = [types.Tool(google_search=types.GoogleSearch())]
            else:
                config_params["response_mime_type"] = "application/json"

            config = types.GenerateContentConfig(**config_params)

            logger.info(f"[Gemini 3 Flash Live Synthesis] Invoking model '{model_name}' (Search Grounding: {use_search_grounding})")
            try:
                return client.models.generate_content(
                    model=model_name,
                    contents=user_content,
                    config=config
                )
            except Exception as exc:
                # If response_mime_type caused an issue on models without strict JSON support, retry without it
                if "response_mime_type" in str(exc) or "mime_type" in str(exc).lower():
                    logger.warning(f"[Gemini RAG] Retrying '{model_name}' without response_mime_type constraint...")
                    config_params.pop("response_mime_type", None)
                    fallback_config = types.GenerateContentConfig(**config_params)
                    return client.models.generate_content(
                        model=model_name,
                        contents=user_content,
                        config=fallback_config
                    )
                raise exc

        def _call_gemini():
            # Try candidate models in order, fallback if 404/not supported
            last_err = None
            candidate_list = get_candidate_models()
            for model_name in candidate_list:
                try:
                    return _call_gemini_with_model(model_name)
                except Exception as e:
                    err_str = str(e).lower()
                    if "404" in err_str or "not found" in err_str or "unsupported" in err_str:
                        logger.warning(f"[Gemini RAG] Model '{model_name}' returned error ({e}), trying next candidate...")
                        last_err = e
                        continue
                    raise e
            if last_err:
                raise last_err
            raise Exception("No valid Gemini model available.")

        try:
            response = await GeminiRateLimiter.execute_with_retry(_call_gemini)
            raw_text = response.text.strip() if hasattr(response, "text") and response.text else ""
            
            # Robust JSON extraction and markdown clean
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.startswith("```"):
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
            raw_text = raw_text.strip()

            try:
                parsed = json.loads(raw_text)
            except Exception:
                # Attempt regex search for JSON object block { ... }
                json_match = re.search(r'(\{.*\})', raw_text, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group(1))
                else:
                    raise

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

            conf_val = float(parsed.get("confidence", 75.0))
            if 0.0 < conf_val <= 1.0:
                conf_val = round(conf_val * 100.0, 1)

            step_reasoning = parsed.get("reasoning") or parsed.get("reasoning_summary", "")
            evidence_assess = parsed.get("evidence_assessment") or parsed.get("evidence_analysis", [])

            return {
                "success": True,
                "data": {
                    "mode": detected_mode,
                    "claim": parsed.get("claim", claim_text),
                    "truth_value": normalized_truth_value,
                    "knowledge_certainty": normalized_certainty,
                    "final_verdict_display": final_display,
                    "claim_type": parsed.get("claim_type", claim_type),
                    "reasoning": step_reasoning,
                    "evidence_assessment": evidence_assess,
                    "api_status": parsed.get("api_status", "ok"),
                    "event_meta": parsed.get("event_meta", {}),
                    "verdict": normalized_verdict,
                    "confidence": conf_val,
                    "summary": step_reasoning or parsed.get("reasoning_summary", ""),
                    "plain_english_takeaway": parsed.get("plain_english_takeaway") or parsed.get("quick_summary", {}).get("key_takeaway") or step_reasoning,
                    "evidence_analysis": evidence_assess,
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
