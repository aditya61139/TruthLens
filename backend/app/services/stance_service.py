import re
from typing import Dict, Any, List, Tuple, Optional
from rapidfuzz import fuzz

OPINION_MARKERS = [
    r"\b(best|worst|greatest|tastiest|ugliest|most beautiful|most overrated|underrated)\b",
    r"\b(i think|i believe|in my opinion|should be banned|should be mandatory|is annoying|is boring|is fun)\b",
    r"\b(better than|worse than|superior to|inferior to)\b"
]

CONTESTED_TOPICS = [
    r"\b(universal basic income|ubi|gun control|tax cuts|minimum wage|crypto future|ai alignment)\b",
    r"\b(privatization|free market|socialism vs capitalism|foreign policy doctrine)\b"
]

SETTLED_FACT_DOMAINS = [
    r"\b(sun\s+(rises|sets)|earth\s+(rotates|orbits|revolves)|speed\s+of\s+light|water\s+boils|water\s+freezes)\b",
    r"\b(capital\s+of\s+[a-zA-Z]+|formula\s+for|chemical\s+formula|gravity|dna|chromosomes|periodic\s+table)\b",
    r"\b(boiling\s+point|freezing\s+point|h2o|photosynthesis|pythagorean\s+theorem|speed\s+of\s+sound)\b"
]

TIME_SENSITIVE_PATTERNS = [
    r"\b(recent|recently|today|yesterday|this week|this month|just now|breaking|latest|ongoing|live)\b",
    r"\b(flash flood|flood|earthquake|wildfire|tsunami|hurricane|cyclone|explosion|shooting|plane crash)\b",
    r"\b(resigned|assassinated|arrested|elected|voted today|attack|missile strike)\b",
    r"^(is there|are there|was there|did\s+[a-zA-Z]+\s+happen|has there been)\b"
]

DIRECTIONAL_ANTONYMS = {
    "east": "west",
    "west": "east",
    "north": "south",
    "south": "north",
    "rises": "sets",
    "sets": "rises",
    "rising": "setting",
    "setting": "rising",
    "increases": "decreases",
    "decreases": "increases",
    "cure": "ineffective",
    "cures": "does not cure",
    "prevents": "does not prevent",
    "causes": "does not cause",
    "flat": "round",
    "round": "flat",
    "hollow": "solid",
    "solid": "hollow",
    "freeze": "boil",
    "freezes": "boils",
    "boils": "freezes"
}

DEBUNK_STANCE_KEYWORDS = [
    "debunk", "debunked", "false", "hoax", "myth", "bogus", "untrue", "fake",
    "incorrect", "inaccurate", "misleading", "fabrication", "no evidence",
    "refutes", "denies", "disproven", "not true"
]

CONFIRM_STANCE_KEYWORDS = [
    "confirms", "confirmed", "true", "accurate", "verified", "correct",
    "study finds", "announces", "official report", "established fact", "evidence shows"
]

class ClaimClassifier:
    @classmethod
    def classify(cls, claim_text: str) -> str:
        """
        Cheap, local rule-based classifier (0 Gemini calls).
        Returns one of: 'SETTLED_FACT', 'CURRENT_EVENT', 'OPINION', 'CONTESTED'.
        """
        text = claim_text.strip().lower()

        # 1. Check for subjective opinion markers
        for pat in OPINION_MARKERS:
            if re.search(pat, text, re.I):
                return "OPINION"

        # 2. Check for time-sensitive current events / breaking disasters
        for pat in TIME_SENSITIVE_PATTERNS:
            if re.search(pat, text, re.I):
                return "CURRENT_EVENT"

        # 3. Check for settled scientific / geographic / physical facts
        for pat in SETTLED_FACT_DOMAINS:
            if re.search(pat, text, re.I):
                return "SETTLED_FACT"

        # 4. Check for inherently contested public/policy controversies
        for pat in CONTESTED_TOPICS:
            if re.search(pat, text, re.I):
                return "CONTESTED"

        # Default fallback: if it mentions science, astronomy, geography -> SETTLED_FACT, else CURRENT_EVENT or CONTESTED
        if any(w in text for w in ["sun", "earth", "moon", "planet", "water", "capital", "ocean", "mountain", "country", "boil", "freeze", "light"]):
            return "SETTLED_FACT"

        return "CURRENT_EVENT"


class StanceDetector:
    @classmethod
    def detect_stance(cls, claim_text: str, doc_title: str, doc_content: str = "") -> Tuple[str, float, str]:
        """
        Determines the stance of a document relative to the claim:
        Returns (stance, stance_confidence, reason):
        - stance: 'ENTAILS' | 'CONTRADICTS' | 'NEUTRAL'
        - stance_confidence: 0.0 - 100.0
        - reason: brief explanatory text
        """
        claim_lower = claim_text.strip().lower()
        combined_doc = f"{doc_title} {doc_content}".strip().lower()

        # 1. Check direct fact-check debunking or confirming signals
        for kw in DEBUNK_STANCE_KEYWORDS:
            if re.search(rf"\b{kw}\b", combined_doc):
                # If the document calls the claim a myth/hoax/debunked
                return (
                    "CONTRADICTS",
                    90.0,
                    f"Document identifies claim as {kw} or inaccurate."
                )

        # 2. Antonym / Directional Contradiction Detection
        # (e.g. claim mentions 'west', doc mentions 'sun rises due east')
        for word, antonym in DIRECTIONAL_ANTONYMS.items():
            if re.search(rf"\b{word}\b", claim_lower):
                # Check if the document explicitly asserts the antonym/opposite truth
                if re.search(rf"\b{antonym}\b", combined_doc):
                    # Check token overlap for subject (e.g. 'sun' / 'rise')
                    claim_tokens = set(re.findall(r"\w{3,}", claim_lower)) - {word, "from", "the", "that", "this"}
                    doc_tokens = set(re.findall(r"\w{3,}", combined_doc))
                    if claim_tokens and len(claim_tokens.intersection(doc_tokens)) >= 1:
                        return (
                            "CONTRADICTS",
                            95.0,
                            f"Contradicts claim by affirming opposite property '{antonym}' instead of '{word}'."
                        )

        # 3. Numeric Inconsistency Detection (e.g. 50 degrees vs 100 degrees)
        claim_nums = re.findall(r"\b\d+(?:\.\d+)?\b", claim_lower)
        doc_nums = re.findall(r"\b\d+(?:\.\d+)?\b", combined_doc)
        if claim_nums and doc_nums:
            if not set(claim_nums).intersection(set(doc_nums)):
                # If subject is heavily overlapping but numbers conflict
                sim = fuzz.token_set_ratio(claim_lower, combined_doc)
                if sim > 65:
                    return (
                        "CONTRADICTS",
                        80.0,
                        f"Reports conflicting metrics/data ({doc_nums[0]}) contrasting with claim ({claim_nums[0]})."
                    )

        # 4. Confirmation / Entailment check
        for kw in CONFIRM_STANCE_KEYWORDS:
            if re.search(rf"\b{kw}\b", combined_doc):
                sim = fuzz.token_set_ratio(claim_lower, combined_doc)
                if sim > 60:
                    return (
                        "ENTAILS",
                        85.0,
                        f"Document corroborates claim with affirmative reporting ({kw})."
                    )

        # 5. Direct high semantic entailment check (describing true state of world)
        sim = fuzz.token_set_ratio(claim_lower, combined_doc)
        if sim > 75:
            # If it shares high similarity without debunking keywords, it entails
            return (
                "ENTAILS",
                75.0,
                "Content directly affirms and describes the asserted proposition."
            )

        if sim < 40:
            return (
                "NEUTRAL",
                30.0,
                "Does not directly address or evaluate the specific core assertion."
            )

        return (
            "NEUTRAL",
            50.0,
            "Mentions related entities but does not take a definitive affirmative or contradicting stance."
        )


class EvidenceReranker:
    @classmethod
    def rerank_evidence(
        cls,
        claim_text: str,
        evidence_list: List[Dict[str, Any]],
        max_docs: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Reranks evidence items by relevance + stance strength, annotating each
        item with a stance label ('ENTAILS', 'CONTRADICTS', 'NEUTRAL') and reason.
        """
        if not evidence_list:
            return []

        annotated_items = []
        for item in evidence_list:
            doc_title = item.get("title", "")
            doc_explanation = item.get("explanation", "") or item.get("claim_text", "")
            
            # Use raw rating if it already has a fact-check stance
            raw_rating = (item.get("raw_rating") or "").lower()
            normalized = item.get("normalized_verdict")

            if normalized == "False" or any(w in raw_rating for w in ["false", "debunk", "incorrect", "hoax"]):
                stance = "CONTRADICTS"
                stance_conf = 95.0
                stance_reason = f"Fact-checker rating: {item.get('raw_rating', 'False')}"
            elif normalized == "True" or any(w in raw_rating for w in ["true", "correct", "verified"]):
                stance = "ENTAILS"
                stance_conf = 90.0
                stance_reason = f"Fact-checker / source confirms assertion."
            else:
                stance, stance_conf, stance_reason = StanceDetector.detect_stance(
                    claim_text=claim_text,
                    doc_title=doc_title,
                    doc_content=doc_explanation
                )

            # Combined score for ranking
            relevance = float(item.get("relevance_score", 60.0))
            credibility = float(item.get("publisher_credibility", {}).get("credibility_score", 60.0))
            
            # Prioritize documents that take a clear stance (ENTAILS / CONTRADICTS) over NEUTRAL
            stance_bonus = 25.0 if stance in ["ENTAILS", "CONTRADICTS"] else 0.0
            rank_score = (relevance * 0.4) + (credibility * 0.3) + (stance_conf * 0.3) + stance_bonus

            item_copy = dict(item)
            item_copy["stance"] = stance
            item_copy["stance_confidence"] = stance_conf
            item_copy["stance_reason"] = stance_reason
            item_copy["rank_score"] = rank_score
            annotated_items.append(item_copy)

        # Sort descending by rank score
        annotated_items.sort(key=lambda x: x.get("rank_score", 0.0), reverse=True)
        return annotated_items[:max_docs]
