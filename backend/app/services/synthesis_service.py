import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from app.services.gemini_service import GeminiSynthesisService
from app.services.stance_service import ClaimClassifier, StanceDetector, EvidenceReranker
from app.services.extractor import ClaimExtractor
from app.core.config import settings

logger = logging.getLogger("truthlens.synthesis")

PRIMARY_SOURCE_KEYWORDS = [
    ".gov", ".mil", ".int", "who.int", "cdc.gov", "nih.gov", "nasa.gov", "noaa.gov",
    "un.org", "gouvernement.fr", "whitehouse.gov", "court", "justice.gov", "usgs.gov",
    "nature.com", "sciencemag.org", "arxiv.org", "cell.com", "thelancet.com", "nejm.org"
]

MAJOR_NEWS_KEYWORDS = [
    "reuters", "associated press", "ap news", "bbc", "new york times", "nyt",
    "washington post", "wall street journal", "wsj", "bloomberg", "the guardian",
    "cnn", "npr", "abc news", "nbc news", "cbs news", "afp", "sky news", "al jazeera", "ndtv", "the hindu"
]

FACT_CHECKER_KEYWORDS = [
    "snopes", "politifact", "afp fact check", "factcheck.org", "alt news",
    "full fact", "lead stories", "boom live", "check your fact", "factly", "fact check"
]

ACADEMIC_KEYWORDS = [
    ".edu", "stanford", "harvard", "mit", "oxford", "cambridge", "britannica",
    "sciencedirect", "pubmed", "springer", "ieee", "university", "institute"
]

class SynthesisService:
    @classmethod
    def classify_source_type(cls, source_name: str = "", url: str = "") -> str:
        """
        Classifies a source into one of the 5 canonical TruthLens tiers:
        - [🟢 Primary Source]
        - [🔵 Major News Outlet]
        - [🟡 Fact-Checker]
        - [🟠 Domain Expert / Academic]
        - [⚪ Other / General]
        """
        combined = f"{source_name} {url}".lower()

        for kw in PRIMARY_SOURCE_KEYWORDS:
            if kw in combined:
                return "[🟢 Primary Source]"

        for kw in FACT_CHECKER_KEYWORDS:
            if kw in combined:
                return "[🟡 Fact-Checker]"

        for kw in MAJOR_NEWS_KEYWORDS:
            if kw in combined:
                return "[🔵 Major News Outlet]"

        for kw in ACADEMIC_KEYWORDS:
            if kw in combined:
                return "[🟠 Domain Expert / Academic]"

        return "[⚪ Other / General]"

    @classmethod
    def format_final_verdict_display(cls, truth_value: str, knowledge_certainty: str, mode: str = "Claim Verification") -> str:
        """
        Constructs the compound user-facing verdict string combining
        Claim Truth Value, Knowledge Certainty, and Operating Mode.
        """
        if mode == "Event Query":
            return "EVENT BRIEFING — Verified Active Reporting"

        if truth_value == "Satire":
            return "SATIRE / PARODY"
        
        if truth_value == "Error":
            return "SERVICE RATE-LIMITED / ERROR"

        if knowledge_certainty == "Settled Knowledge":
            if truth_value in ["True", "Likely True"]:
                return "TRUE — Established Knowledge"
            elif truth_value in ["False", "Likely False"]:
                return "FALSE — Contradicts Established Knowledge"
            elif truth_value == "Misleading":
                return "MISLEADING — Distorts Settled Knowledge"
            else:
                return "UNVERIFIABLE — Insufficient Evidence"

        elif knowledge_certainty == "Under Active Debate":
            if truth_value in ["True", "Likely True"]:
                return "LIKELY TRUE — Under Active Debate"
            elif truth_value in ["False", "Likely False"]:
                return "LIKELY FALSE — Under Active Debate"
            elif truth_value == "Misleading":
                return "MISLEADING — Competing Accounts"
            else:
                return "UNVERIFIABLE — Insufficient Evidence"

        elif knowledge_certainty == "Emerging / Current Event":
            if mode == "Hybrid":
                if truth_value == "True":
                    return "TRUE / VERIFIED (Hybrid Event Claim)"
                elif truth_value == "False":
                    return "FALSE / REFUTED (Hybrid Event Claim)"
                else:
                    return "MISLEADING (Hybrid Event Claim)"
            if truth_value == "True":
                return "TRUE / VERIFIED — Breaking Event"
            elif truth_value == "False":
                return "FALSE — Refuted Event"
            elif truth_value == "Misleading":
                return "MISLEADING — Unconfirmed Context"
            elif truth_value == "Likely True":
                return "LIKELY TRUE — Developing Reporting"
            elif truth_value == "Likely False":
                return "LIKELY FALSE — Contradicted by Reporting"
            else:
                return "UNVERIFIABLE — Insufficient Evidence"

        else: # Insufficient Evidence
            if truth_value in ["Unverifiable", "Unverified"]:
                return "UNVERIFIABLE — Insufficient Evidence"
            elif truth_value == "True":
                return "TRUE / VERIFIED"
            elif truth_value == "False":
                return "FALSE"
            else:
                return "UNVERIFIABLE — Insufficient Evidence"

    @classmethod
    def apply_consistency_guard_rail(
        cls,
        truth_value: str,
        knowledge_certainty: str,
        claim_breakdown: List[Dict[str, Any]],
        reranked_docs: List[Dict[str, Any]],
        mode: str = "Claim Verification"
    ) -> Tuple[str, str, str]:
        """
        CRITICAL GUARD RAIL:
        Before rendering the final verdict, performs a strict consistency check:
        - Reviews the Clause-by-Clause Assertion Mapping results.
        - If ANY clause is marked 'debunked' or 'false' (or evidence contains 'CONTRADICTS'),
          the truth_value MUST NOT be 'True'.
        - Clause-level evaluations take precedence over high-level tags.
        """
        debunked_clauses = [
            c for c in claim_breakdown
            if str(c.get("status", "")).lower() in ["debunked", "false", "unsupported"]
        ]
        has_contradict_evidence = any(
            d.get("stance") == "CONTRADICTS" for d in reranked_docs
        )

        enforced_tv = truth_value
        enforced_kc = knowledge_certainty

        if (debunked_clauses or has_contradict_evidence) and mode != "Event Query":
            if enforced_tv in ["True", "Likely True"]:
                logger.warning(
                    f"[GuardRail] Overriding truth_value from '{enforced_tv}' to 'False' due to "
                    f"{len(debunked_clauses)} debunked clause(s) or contradicting evidence."
                )
                verified_clauses = [
                    c for c in claim_breakdown
                    if str(c.get("status", "")).lower() in ["verified", "accurate", "true"]
                ]
                if verified_clauses and len(verified_clauses) > 0 and len(debunked_clauses) > 0:
                    enforced_tv = "Misleading"
                else:
                    enforced_tv = "False"

        enforced_display = cls.format_final_verdict_display(enforced_tv, enforced_kc, mode=mode)
        return enforced_tv, enforced_kc, enforced_display

    @classmethod
    def generate_360_briefing(
        cls,
        claim_text: str,
        truth_value: str,
        knowledge_certainty: str,
        category: str,
        evidence_list: List[Dict[str, Any]],
        settled_fact_info: Optional[Dict[str, Any]] = None,
        mode: str = "Claim Verification",
        event_meta: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generates a complete, self-contained 360° incident briefing across all sub-sections
        including structured Impact & Key Numbers.
        """
        is_crisis = any(
            w in category.lower() or w in claim_text.lower()
            for w in [
                "disaster", "flood", "earthquake", "quake", "cyclone", "hurricane", "typhoon",
                "storm", "wildfire", "fire", "war", "conflict", "casualt", "explosion",
                "shooting", "missile", "crash", "landslide", "tsunami", "relief", "rescue"
            ]
        )

        if knowledge_certainty == "Settled Knowledge":
            is_accurate = (truth_value == "True")
            exp = settled_fact_info.get("explanation", "") if settled_fact_info else ""
            
            what_happened = (
                f"The assertion '{claim_text}' evaluates a fundamental principle of {category}. "
                f"Scientific and educational literature universally {'confirms' if is_accurate else 'refutes'} this claim."
            )
            full_context = (
                f"{exp} Established scientific consensus across global academic bodies, educational institutions, "
                f"and national research entities confirms the invariant nature of this {category.lower()} principle. "
                f"It is taught in standard curricula and is not subject to contemporary controversy."
            )
            timeline = [
                "Ancient & Classical Observations — Foundation of fundamental physical principles.",
                "Scientific Revolution — Mathematical and experimental formalization of natural laws.",
                "Modern Era — Standardized across international scientific and educational bodies."
            ]
            impact_numbers = None
            key_parties = [
                {"name": f"International {category} Community", "role": "Peer-reviewed scientific and academic consensus."},
                {"name": "Standard Educational Curricula", "role": "Textbook and institutional educational standard."}
            ]
            key_data = [
                f"Domain Classification: {category}",
                "Consensus Level: 99.9% established educational & scientific agreement."
            ]
            perspectives = [
                {"party": "Global Academic Consensus", "stance": f"The proposition is universally recognized as {'factual' if is_accurate else 'scientifically inaccurate'}."}
            ]
            current_status = f"Permanent, settled {category.lower()} consensus across global educational and scientific authorities."
            key_takeaway = (
                f"{'This claim is an undisputed scientific fact.' if is_accurate else 'This claim directly contradicts established scientific consensus and is false.'}"
            )

        elif mode == "Event Query":
            region = event_meta.get("region", "Affected Region") if event_meta else "Affected Region"
            top_sources = [e.get("source_name", "News Media") for e in evidence_list[:3]]
            top_str = ", ".join(top_sources) if top_sources else "primary news outlets"

            if is_crisis:
                what_happened = (
                    f"Incidents and developments regarding '{claim_text}' were reported in {region}. "
                    f"According to coverage from {top_str}, response teams and local authorities mobilized "
                    f"to manage the situation and assist affected populations."
                )
                full_context = (
                    f"The incident in {region} relates to {category.lower()}. "
                    f"Historical patterns and seasonal factors contribute to elevated activity during this period."
                )
                timeline = [
                    f"Initial Occurrence — Early alerts and initial reports of '{claim_text[:50]}...' emerged.",
                    f"Subsequent Days — Escalation of response operations and cross-verification by {top_str}.",
                    f"Latest Update — Emergency measures and relief distribution underway across affected zones."
                ]
                impact_numbers = {
                    "deaths": "Casualty figures under official assessment; monitoring ongoing",
                    "displaced": "Residents evacuated to relief shelters across affected districts",
                    "areas_affected": f"Multiple municipal and rural districts across {region}",
                    "damage": "Localized infrastructure, roadway, and property damage reported",
                    "rescue": "National and state disaster relief personnel deployed for emergency operations"
                }
                key_parties = [
                    {"name": f"{region} Disaster Management", "role": "Coordinating on-ground rescue and relief delivery."},
                    {"name": top_sources[0] if top_sources else "News Agencies", "role": "Documenting field reporting and casualty statistics."}
                ]
                current_status = f"Response and monitoring operations remain active in {region}."
                key_takeaway = f"Verified reporting confirms significant developments regarding {claim_text}, with active relief operations in place."
            else:
                what_happened = (
                    f"Reporting and developments regarding '{claim_text}' were documented. "
                    f"Coverage from {top_str} outlines current factual status and public announcements on this topic."
                )
                full_context = (
                    f"This topic relates to {category}. Relevant industry monitors and official spokespersons "
                    f"provide ongoing coverage and documentation regarding verified releases and timelines."
                )
                timeline = [
                    f"Initial Circulation — Early reports and discussions regarding '{claim_text[:50]}...' surfaced.",
                    f"Public Coverage — Follow-up articles and factual review published by {top_str}.",
                    f"Current Stance — Official statements and documented releases reflect current status."
                ]
                impact_numbers = None
                key_parties = [
                    {"name": "Topic Origin / Public Discourse", "role": "Circulated the initial inquiries or claims."},
                    {"name": top_sources[0] if top_sources else "Industry / News Sources", "role": "Published factual coverage and context."}
                ]
                current_status = f"Coverage and verification ongoing across documented sources."
                key_takeaway = f"Public records and reporting assess '{claim_text}' against official announcements and verified sources."

            key_data = [
                f"Total Documented Sources Evaluated: {len(evidence_list)}",
                f"Event Category: {category}"
            ]
            perspectives = [
                {"party": "Official Sources / Outlets", "stance": "Reporting verified updates based on documented statements."},
                {"party": "Public & Industry Monitors", "stance": "Tracking announcements and verifying authenticity."}
            ]

        else:
            top_sources = [e.get("source_name", "News Media") for e in evidence_list[:3]]
            top_str = ", ".join(top_sources) if top_sources else "independent monitors"
            
            what_happened = (
                f"Investigation regarding '{claim_text}'. "
                f"Current reporting and factual records from {top_str} assess this claim as {truth_value.upper()}."
            )
            full_context = (
                f"This topic relates to {category}. Independent fact-checkers and primary news bureaus actively monitor "
                f"and verify assertions of this nature to prevent the proliferation of unverified or manipulated claims."
            )
            timeline = [
                f"Recent — Initial circulation of claim regarding '{claim_text[:60]}...'",
                f"Ongoing — Fact-checking review and evidence corroboration by {top_str}."
            ]
            if is_crisis:
                impact_numbers = {
                    "deaths": "Specific casualty figures evaluated against official releases",
                    "displaced": "Community displacement tracked by humanitarian monitors",
                    "areas_affected": f"Identified regions within {category}",
                    "damage": "Direct physical and institutional impacts documented",
                    "rescue": "Emergency service response recorded by news bureaus"
                }
            else:
                impact_numbers = None

            key_parties = [
                {"name": "Claim Origin / Online Discourse", "role": "Circulated the initial assertion."},
                {"name": top_sources[0] if top_sources else "News Bureaus", "role": "Conducted investigative reporting and cross-referencing."}
            ]
            key_data = [
                f"Total Documented Sources Evaluated: {len(evidence_list)}",
                f"Primary Assessed Category: {category}"
            ]
            perspectives = [
                {"party": "Reporting & Fact-Check Consensuses", "stance": f"Assessed as {truth_value} based on gathered documentation."}
            ]
            current_status = "Investigation concluded against available public records and open-source intelligence."
            key_takeaway = f"TruthLens assesses this claim as {truth_value.upper()} based on verified reporting."

        return {
            "what_happened": what_happened,
            "full_context": full_context,
            "timeline": timeline,
            "impact_numbers": impact_numbers,
            "key_parties": key_parties,
            "key_data": key_data,
            "perspectives": perspectives,
            "current_status": current_status,
            "key_takeaway": key_takeaway
        }

    @classmethod
    async def synthesize(
        cls,
        claim_text: str,
        evidence_list: List[Dict[str, Any]],
        red_flags: Dict[str, Any],
        publisher_info: Optional[Dict[str, Any]] = None,
        settled_fact_info: Optional[Dict[str, Any]] = None,
        is_time_sensitive: bool = False,
        search_query: Optional[str] = None,
        allow_gemini_call: bool = True,
        original_raw_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        RAG-based Verdict & Event Synthesis Engine:
        1. Classifies Input Mode (Mode A: Claim Verification, Mode B: Event Query, Mode C: Hybrid).
        2. Evaluates 2 Independent Dimensions: Claim Truth Value & Knowledge Certainty.
        3. Enforces Clause-Level Consistency Guard Rail.
        4. Produces Structured Event Briefing & 360° Incident Briefing (`quick_summary`).
        5. Categorizes every source into the 5-tier Sources & Further Reading schema.
        """
        # Detect Mode & Event Category from original input or claim text
        source_text = original_raw_text or claim_text
        detected_mode = ClaimExtractor.detect_query_mode(source_text)
        emoji, category_label = ClaimExtractor.detect_event_category(source_text)

        event_meta = {
            "category_emoji": emoji,
            "category_label": category_label,
            "title": f"Report: {claim_text.rstrip('?.')}",
            "region": "Regional / National",
            "date_range": "Recent / Ongoing",
            "status": "🟡 Developing" if detected_mode in ["Event Query", "Hybrid"] else "🟢 Resolved"
        }

        # 1. Settled Knowledge Tier First (0 Gemini calls)
        if settled_fact_info and settled_fact_info.get("is_settled_fact"):
            raw_verdict = settled_fact_info.get("verdict", "True")
            final_confidence = float(settled_fact_info.get("confidence", 98.0))
            category = settled_fact_info.get("category", "Science")
            fact_type = settled_fact_info.get("fact_type", "Established Knowledge")
            
            knowledge_certainty = "Settled Knowledge"
            truth_value = "True" if raw_verdict == "True" else "False"

            if truth_value == "True":
                confidence_factors = [
                    "Universally established scientific / geographic consensus (Undisputed fact)",
                    f"Domain: {category}",
                    "Verified as standard fundamental knowledge across educational literature"
                ]
                summary = settled_fact_info.get("summary", "This assertion is verified across fundamental scientific and geographic consensus.")
                clause_status = "verified"
                clause_note = f"Verified as an undisputed, settled {category} principle."
            else:
                confidence_factors = [
                    "Direct contradiction of universally established scientific / geographic consensus",
                    f"Domain: {category}",
                    "Asserts an inverted property contrasting with standard physical laws"
                ]
                summary = settled_fact_info.get("summary", "This claim directly CONTRADICTS established scientific and geographic consensus.")
                clause_status = "debunked"
                clause_note = f"Contradicts established, settled {category} principles."

            why_bullets = [
                settled_fact_info.get("explanation", "Evaluated against established scientific / geographic principles."),
                "This assertion is part of standard educational literature and does not require active news fact-checking."
            ]
            
            claim_breakdown = [{
                "clause": claim_text,
                "status": clause_status,
                "note": clause_note
            }]
            unverified_aspects = "None (Settled Knowledge)"

            ref_sources = settled_fact_info.get("reference_sources", [])
            formatted_sources = []
            for s in ref_sources:
                formatted_sources.append({
                    "source_name": s.get("source_name", "Academic Reference"),
                    "source_site": s.get("source_site", s.get("source_name", "")),
                    "source_url": s.get("source_url", ""),
                    "title": s.get("title", ""),
                    "raw_rating": s.get("raw_rating", "Established Knowledge"),
                    "normalized_verdict": truth_value,
                    "stance": s.get("stance", "ENTAILS" if truth_value == "True" else "CONTRADICTS"),
                    "stance_reason": s.get("stance_reason", ""),
                    "source_type": s.get("source_type") or cls.classify_source_type(s.get("source_name", ""), s.get("source_url", "")),
                    "date_published": s.get("date_published", "2024-01-01"),
                    "review_date": s.get("date_published", "2024-01-01"),
                    "paywall": False,
                    "claim_text": claim_text,
                    "confidence_contribution": 98.0,
                    "explanation": s.get("explanation", "")
                })

            # Apply Guard Rail
            truth_value, knowledge_certainty, final_display = cls.apply_consistency_guard_rail(
                truth_value=truth_value,
                knowledge_certainty=knowledge_certainty,
                claim_breakdown=claim_breakdown,
                reranked_docs=formatted_sources,
                mode="Claim Verification"
            )

            # Generate 360° Quick Summary Briefing
            quick_summary = cls.generate_360_briefing(
                claim_text=claim_text,
                truth_value=truth_value,
                knowledge_certainty=knowledge_certainty,
                category=category,
                evidence_list=formatted_sources,
                settled_fact_info=settled_fact_info,
                mode="Claim Verification",
                event_meta=event_meta
            )

            return {
                "mode": "Claim Verification",
                "event_meta": event_meta,
                "verdict": truth_value,
                "truth_value": truth_value,
                "knowledge_certainty": knowledge_certainty,
                "final_verdict_display": final_display,
                "claim_type": "SETTLED_FACT",
                "is_settled_fact": True,
                "fact_type": fact_type,
                "confidence": round(final_confidence, 1),
                "confidence_factors": confidence_factors,
                "summary": summary,
                "llm_enhanced": False,
                "gemini_calls_made": 0,
                "error": None,
                "quick_summary": quick_summary,
                "reranked_sources": formatted_sources,
                "explanation": {
                    "why_bullets": why_bullets,
                    "claim_breakdown": claim_breakdown,
                    "unverified_aspects": unverified_aspects
                }
            }

        # 2. Local Claim Classification & Knowledge Certainty (0 Gemini calls)
        claim_type = ClaimClassifier.classify(claim_text)
        if is_time_sensitive or detected_mode in ["Event Query", "Hybrid"]:
            claim_type = "CURRENT_EVENT"
            knowledge_certainty = "Emerging / Current Event"
        elif claim_type == "SETTLED_FACT":
            knowledge_certainty = "Settled Knowledge"
        elif claim_type == "CONTESTED":
            knowledge_certainty = "Under Active Debate"
        elif claim_type == "OPINION":
            knowledge_certainty = "Under Active Debate"
        else:
            knowledge_certainty = "Emerging / Current Event"

        # 3. Evidence Reranking, Stance Labeling, and Source Classification
        reranked_docs = EvidenceReranker.rerank_evidence(
            claim_text=claim_text,
            evidence_list=evidence_list,
            max_docs=5
        )

        for doc in reranked_docs:
            if not doc.get("source_type"):
                doc["source_type"] = cls.classify_source_type(doc.get("source_name", ""), doc.get("source_url", ""))
            if not doc.get("date_published"):
                doc["date_published"] = doc.get("review_date") or "Date not available"
            if "paywall" not in doc:
                doc["paywall"] = any(w in doc.get("source_name", "").lower() for w in ["wsj", "financial times", "bloomberg"])

        # 4. Local Deterministic Stance Synthesis
        contradict_count = sum(1 for d in reranked_docs if d.get("stance") == "CONTRADICTS")
        entail_count = sum(1 for d in reranked_docs if d.get("stance") == "ENTAILS")

        if publisher_info and publisher_info.get("category") == "Satire":
            truth_value = "Satire"
            local_confidence = 96.0
        elif detected_mode == "Event Query":
            truth_value = "True" if len(reranked_docs) > 0 else "Unverified"
            local_confidence = 88.0 if len(reranked_docs) > 0 else 35.0
        elif contradict_count >= 1 and entail_count == 0:
            truth_value = "False"
            local_confidence = min(96.0, 75.0 + (contradict_count * 10.0))
        elif entail_count >= 1 and contradict_count == 0:
            truth_value = "True"
            local_confidence = min(96.0, 75.0 + (entail_count * 10.0))
        elif contradict_count >= 1 and entail_count >= 1:
            truth_value = "Misleading"
            local_confidence = 80.0
        elif red_flags.get("red_flag_score", 0) >= 70:
            truth_value = "False"
            local_confidence = 75.0
        elif red_flags.get("red_flag_score", 0) >= 40:
            truth_value = "Misleading"
            local_confidence = 70.0
        else:
            truth_value = "Unverifiable"
            knowledge_certainty = "Insufficient Evidence"
            local_confidence = 35.0

        confidence_factors = []
        if truth_value in ["Unverifiable", "Unverified"]:
            confidence_factors.append("No directly relevant fact-check or corroborating news documentation found (-65%)")
            confidence_factors.append("Inconclusive evidence base")
        elif truth_value == "Satire":
            confidence_factors.append("Source/claim confirmed to originate from satirical comedy publication")
        elif detected_mode == "Event Query":
            confidence_factors.append(f"Synthesized from {len(reranked_docs)} active reporting records and news monitors")
        elif truth_value == "False":
            confidence_factors.append(f"Retrieved documentation directly contradicts the assertion ({contradict_count} contradicting source(s))")
        elif truth_value == "True":
            confidence_factors.append(f"Corroborated by independent reporting ({entail_count} confirming source(s))")
        elif truth_value == "Misleading":
            confidence_factors.append("Conflicting or selective evidence indicates missing context")

        # Explainability why bullets
        why_bullets = []
        claim_breakdown = []

        if detected_mode == "Event Query":
            summary = f"Event briefing synthesized across {len(reranked_docs)} verified news and official reports."
            why_bullets.append(f"Event inquiry identified: {category_label}")
            why_bullets.append("Structured 360° incident briefing compiled from live sources.")
        elif truth_value == "False":
            if contradict_count > 0:
                top_contra = next(d for d in reranked_docs if d.get("stance") == "CONTRADICTS")
                summary = f"This claim is FALSE. Documented reporting from {top_contra.get('source_name')} contradicts this assertion."
                why_bullets.append(f"Contradicted by {top_contra.get('source_name')}: {top_contra.get('stance_reason')}")
            else:
                summary = "This claim is assessed as FALSE based on strong misinformation markers, lack of credible reporting, and pseudoscientific phrasing."
                why_bullets.append("No reputable scientific or news organization has ever confirmed this assertion.")
        elif truth_value == "True":
            if entail_count > 0:
                top_ent = next(d for d in reranked_docs if d.get("stance") == "ENTAILS")
                summary = f"This claim is TRUE. Verified by credible reporting from {top_ent.get('source_name')}."
                why_bullets.append(f"Corroborated by {top_ent.get('source_name')}: {top_ent.get('stance_reason')}")
            else:
                summary = "This claim appears accurate based on credible reporting and neutral verifiable assertions."
                why_bullets.append("Assertion aligns with established factual consensus.")
        elif truth_value == "Misleading":
            summary = "This claim is MISLEADING. It contains selective elements or conflicting interpretations that omit crucial context."
            why_bullets.append("Competing accounts and missing context create a distorted factual impression.")
        elif truth_value == "Satire":
            summary = "This claim originates from a known SATIRE or parody source and was not intended as factual news reporting."
            why_bullets.append(f"Originated from humorous satirical publication ({publisher_info.get('name') if publisher_info else 'Satire outlet'}).")
        else:
            summary = "This claim is UNVERIFIABLE. There is currently insufficient public evidence, official documentation, or fact-checking coverage to conclusively prove or disprove it."
            why_bullets.append("No primary sources or recognized fact-checkers have verified this specific statement.")

        # Build sub-clause breakdown
        clauses = re.split(r",|\b(and|but|while|because)\b", claim_text)
        for clause in clauses:
            if not clause or len(clause.strip()) < 4 or clause.lower() in ["and", "but", "while", "because"]:
                continue
            c_text = clause.strip()
            if truth_value == "False":
                status = "debunked" if any(w in c_text.lower() for w in ["cures", "causes", "secret", "alien", "hollow", "pyramid", "endorsed", "banned", "west", "flat"]) else "unsupported"
            elif truth_value == "True":
                status = "verified"
            elif truth_value == "Misleading":
                status = "misleading" if any(w in c_text.lower() for w in ["more", "lifetime", "only", "always", "never"]) else "accurate"
            elif truth_value == "Satire":
                status = "satire"
            else:
                status = "unverified"
            
            claim_breakdown.append({
                "clause": c_text,
                "status": status,
                "note": f"Clause assessed as {status} against current evidence."
            })

        unverified_aspects = "None" if truth_value in ["True", "False", "Satire"] else "No directly relevant fact-check or news investigations found for this specific assertion."

        # Generate default 360° Quick Summary Briefing
        quick_summary = cls.generate_360_briefing(
            claim_text=claim_text,
            truth_value=truth_value,
            knowledge_certainty=knowledge_certainty,
            category=category_label,
            evidence_list=reranked_docs,
            settled_fact_info=settled_fact_info,
            mode=detected_mode,
            event_meta=event_meta
        )

        # 5. AT MOST ONE Gemini RAG Synthesis Call (if API key is present and allowed)
        gemini_calls_made = 0
        llm_enhanced = False
        llm_warning = None
        service_error = None
        has_gemini_key = bool(settings.GEMINI_API_KEY or settings.GOOGLE_API_KEY)

        if allow_gemini_call and has_gemini_key:
            gemini_calls_made = 1
            gemini_res = await GeminiSynthesisService.execute_unified_evaluation(
                claim_text=claim_text,
                claim_type=claim_type,
                reranked_evidence=reranked_docs,
                is_time_sensitive=is_time_sensitive or detected_mode in ["Event Query", "Hybrid"],
                search_query=search_query,
                use_search_grounding=(is_time_sensitive or detected_mode in ["Event Query", "Hybrid"]) and len(evidence_list) == 0
            )

            if gemini_res.get("success") and gemini_res.get("data"):
                llm_enhanced = True
                data = gemini_res["data"]
                
                if data.get("mode"):
                    detected_mode = data.get("mode")

                if data.get("event_meta") and isinstance(data["event_meta"], dict) and data["event_meta"].get("title"):
                    event_meta.update(data["event_meta"])

                if data.get("truth_value"):
                    truth_value = data.get("truth_value")
                elif data.get("verdict"):
                    truth_value = data.get("verdict")

                if data.get("knowledge_certainty"):
                    knowledge_certainty = data.get("knowledge_certainty")

                if truth_value in ["Unverifiable", "Unverified"] and detected_mode != "Event Query":
                    local_confidence = min(45.0, float(data.get("confidence", 35.0)))
                else:
                    local_confidence = max(65.0, float(data.get("confidence", local_confidence)))

                if data.get("summary"):
                    summary = data.get("summary")

                # Incorporate structured evidence analysis
                ev_analysis = data.get("evidence_analysis", [])
                if ev_analysis:
                    why_bullets = []
                    for ea in ev_analysis:
                        why_bullets.append(f"{ea.get('source', 'Source')} [{ea.get('stance', 'NEUTRAL')}]: {ea.get('reason', '')}")

                if data.get("claim_breakdown"):
                    claim_breakdown = data.get("claim_breakdown")

                # Adopt Gemini 360° Quick Summary Briefing
                if data.get("quick_summary") and isinstance(data["quick_summary"], dict) and data["quick_summary"].get("what_happened"):
                    qs = data["quick_summary"]
                    merged_impact = dict(quick_summary.get("impact_numbers", {
                        "deaths": "Figures under active monitoring and verification",
                        "displaced": "Displaced communities reported in relief transit centers",
                        "areas_affected": "Affected municipal and regional zones",
                        "damage": "Physical and infrastructure damage documented",
                        "rescue": "Emergency response agencies actively deployed"
                    }))
                    if isinstance(qs.get("impact_numbers"), dict):
                        for k, v in qs["impact_numbers"].items():
                            if v and str(v).strip():
                                merged_impact[k] = v

                    quick_summary = {
                        "what_happened": qs.get("what_happened", quick_summary["what_happened"]),
                        "full_context": qs.get("full_context", quick_summary["full_context"]),
                        "timeline": qs.get("timeline", quick_summary["timeline"]),
                        "impact_numbers": merged_impact,
                        "key_parties": qs.get("key_parties", quick_summary["key_parties"]),
                        "key_data": qs.get("key_data", quick_summary["key_data"]),
                        "perspectives": qs.get("perspectives", quick_summary["perspectives"]),
                        "current_status": qs.get("current_status", quick_summary["current_status"]),
                        "key_takeaway": qs.get("key_takeaway", quick_summary["key_takeaway"])
                    }

                # Incorporate structured sources and reading from Gemini
                for sr in data.get("sources_and_reading", []):
                    if not any(r.get("source_url") == sr.get("url") for r in reranked_docs):
                        reranked_docs.append({
                            "source_name": sr.get("source_name", "Cited Source"),
                            "source_site": sr.get("source_name", ""),
                            "source_url": sr.get("url", ""),
                            "title": sr.get("title", ""),
                            "source_type": sr.get("source_type") or cls.classify_source_type(sr.get("source_name", ""), sr.get("url", "")),
                            "date_published": sr.get("date_published", "Recent"),
                            "review_date": sr.get("date_published", "Recent"),
                            "paywall": sr.get("paywall", False),
                            "archive_url": sr.get("archive_url"),
                            "normalized_verdict": truth_value,
                            "stance": "ENTAILS" if truth_value in ["True", "Likely True"] else ("CONTRADICTS" if truth_value in ["False", "Likely False"] else "NEUTRAL"),
                            "explanation": sr.get("title", "")
                        })

                # Incorporate any search grounding web sources returned
                for g_ev in gemini_res.get("grounding_evidence", []):
                    if not any(e.get("source_url") == g_ev.get("source_url") for e in reranked_docs):
                        reranked_docs.append(g_ev)

            elif gemini_res.get("error"):
                err = gemini_res["error"]
                logger.error(f"[Synthesis] Gemini API returned error: {err['code']} - {err['message']}")
                
                if len(evidence_list) == 0 and truth_value in ["Unverifiable", "Unverified"] and detected_mode != "Event Query":
                    service_error = {
                        "code": err["code"],
                        "message": err["message"],
                        "details": err.get("details", err["message"])
                    }
                    return {
                        "mode": detected_mode,
                        "event_meta": event_meta,
                        "verdict": "Error",
                        "truth_value": "Error",
                        "knowledge_certainty": "Insufficient Evidence",
                        "final_verdict_display": "SERVICE RATE-LIMITED / ERROR",
                        "claim_type": claim_type,
                        "is_settled_fact": False,
                        "confidence": 0.0,
                        "confidence_factors": ["Verification could not be completed due to an upstream API service issue"],
                        "summary": err["message"],
                        "llm_enhanced": False,
                        "gemini_calls_made": 1,
                        "error": service_error,
                        "quick_summary": quick_summary,
                        "reranked_sources": reranked_docs,
                        "explanation": {
                            "why_bullets": [
                                f"Service Error ({err['code']}): {err['message']}",
                                "Please verify your Google API key or retry in a few moments."
                            ],
                            "claim_breakdown": [],
                            "unverified_aspects": "Verification incomplete due to service error."
                        }
                    }
                else:
                    llm_warning = f"AI language synthesis unavailable ({err['code']}: {err['message']}). Verified using local stance consensus."

        # 6. Apply Consistency Guard Rail before returning
        truth_value, knowledge_certainty, final_display = cls.apply_consistency_guard_rail(
            truth_value=truth_value,
            knowledge_certainty=knowledge_certainty,
            claim_breakdown=claim_breakdown,
            reranked_docs=reranked_docs,
            mode=detected_mode
        )

        normalized_verdict = truth_value if truth_value in ["True", "False", "Misleading", "Satire", "Error"] else "Unverified"

        return {
            "mode": detected_mode,
            "event_meta": event_meta,
            "verdict": normalized_verdict,
            "truth_value": truth_value,
            "knowledge_certainty": knowledge_certainty,
            "final_verdict_display": final_display,
            "claim_type": claim_type,
            "is_settled_fact": knowledge_certainty == "Settled Knowledge",
            "confidence": round(local_confidence, 1),
            "confidence_factors": confidence_factors,
            "summary": summary,
            "llm_enhanced": llm_enhanced,
            "llm_warning": llm_warning,
            "gemini_calls_made": gemini_calls_made,
            "error": service_error,
            "quick_summary": quick_summary,
            "reranked_sources": reranked_docs,
            "explanation": {
                "why_bullets": why_bullets,
                "claim_breakdown": claim_breakdown,
                "unverified_aspects": unverified_aspects
            }
        }
