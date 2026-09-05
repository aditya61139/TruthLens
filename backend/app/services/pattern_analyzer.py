import re
from typing import Dict, Any, List

# Common misinformation and sensationalist pattern lexicons
CLICKBAIT_PATTERNS = [
    (r"\b(you won't believe|what happens next|will blow your mind|shocking truth|the real reason why)\b", "Curiosity Gap / Clickbait Hook", 20),
    (r"\b(secret that|they don't want you to know|hidden truth|censored by|banned by|shocking secret)\b", "Information Suppression / Secret Claim", 25),
    (r"\b(miracle cure|doctors are stunned|cure for all|overnight trick|effortless cure)\b", "Miracle Cure / Exaggerated Promise", 30),
    (r"\b(urgent warning|wake up people|share before it gets taken down|share before taken down|share before deleted)\b", "Artificial Urgency / Viral Coercion", 25),
    (r"\b(mind-blowing|jaw-dropping|unbelievable|astonishing discovery)\b", "Superlative Sensationalism", 15)
]

EMOTIONAL_MANIPULATION_PATTERNS = [
    (r"\b(evil|corrupt|traitor|traitorous|monster|massacre|bloodbath|disgrace|pure evil)\b", "Dehumanizing / Inflammatory Moral Language", 20),
    (r"\b(terrifying|horrific|catastrophic|apocalyptic|deadly threat|doomsday)\b", "Fearmongering / Catastrophizing", 20),
    (r"\b(destroyed|slammed|annihilated|demolished|obliterated|eviscerated)\b", "Aggressive Hyperbole", 15),
    (r"\b(sheep|sheeple|brainwashed|puppets|clowns|idiots)\b", "In-group vs Out-group Derogation", 15)
]

UNVERIFIED_ATTRIBUTION_PATTERNS = [
    (r"\b(scientists say|experts claim|doctors confirm|sources reveal|insiders say|studies prove)\b(?!\s+(at|from|by)\s+[A-Z])", "Vague / Anonymous Authority Attribution", 20),
    (r"\b(many people are saying|everyone knows that|it is widely known|rumor has it)\b", "Bandwagon / Unsubstantiated Consensus", 20),
    (r"\b(a secret whistleblower|an anonymous official|a high-ranking source)\b", "Unverifiable Anonymous Source", 20)
]

CONSPIRACY_PATTERNS = [
    (r"\b(deep state|globalist agenda|depopulation agenda|chemtrails|flat earth|illuminati)\b", "Known Conspiracy Keyword", 30),
    (r"\b(big pharma is hiding|big pharma|microchips in vaccines|5g causes|5g towers control)\b", "Pseudoscience / Medical Conspiracy", 35),
    (r"\b(staged by crisis actors|false flag operation|orchestrated hoax)\b", "Crisis Denialism / False Flag Claim", 35),
    (r"\b(new world order|wef agenda 2030 depopulation|rothschilds control)\b", "Grand Conspiracy Trope", 30)
]

STATISTICAL_PATTERNS = [
    (r"(\b\d{3,}\s*%|\b\d+%\s*of\s*all|\b1000%|millions\s*dead\s*secretly|\b\d+x\s*death\s*rate|\b100%\s*recovery)", "Extreme / Unreferenced Statistical Claim", 25)
]

class MisinformationPatternAnalyzer:
    @classmethod
    def analyze(cls, text: str) -> Dict[str, Any]:
        """
        Scans text for linguistic red flags, emotional manipulation, clickbait syntax,
        vague attribution, and conspiracy tropes. Returns a red flag score (0-100) and itemized checklist.
        """
        flags = []
        raw_score = 0
        text_lower = text.lower()

        # 1. Check ALL CAPS ratio
        words = text.split()
        if len(words) >= 4:
            caps_words = [w for w in words if w.isupper() and len(w) > 2 and w.isalpha()]
            caps_ratio = len(caps_words) / len(words)
            if caps_ratio > 0.30:
                flags.append({
                    "category": "Stylistic Red Flag",
                    "pattern": "Excessive Capitalization (Shouting / Alarmism)",
                    "severity": "High" if caps_ratio > 0.6 else "Medium",
                    "impact": 20,
                    "explanation": f"{int(caps_ratio*100)}% of words in the claim are capitalized to trigger psychological urgency.",
                    "detected_instances": caps_words[:5]
                })
                raw_score += 20

        # 2. Check Excessive Punctuation (!!!, ???, !?!)
        punct_matches = re.findall(r"(!{2,}|\?{2,}|\!+\?+|\?+\!+)", text)
        if punct_matches:
            flags.append({
                "category": "Stylistic Red Flag",
                "pattern": "Multiple Exclamation / Question Marks",
                "severity": "Medium",
                "impact": 15,
                "explanation": "Multiple punctuation marks are frequently used in sensationalized content to induce panic or outrage.",
                "detected_instances": punct_matches[:3]
            })
            raw_score += 15

        # 3. Check Clickbait Patterns
        for regex, desc, impact in CLICKBAIT_PATTERNS:
            matches = re.findall(regex, text_lower)
            if matches:
                flags.append({
                    "category": "Clickbait & Curiosity Gap",
                    "pattern": desc,
                    "severity": "High" if impact >= 25 else "Medium",
                    "impact": impact,
                    "explanation": f"Uses clickbait formulation '{matches[0]}' to withhold context or provoke emotional clicks.",
                    "detected_instances": matches[:3]
                })
                raw_score += impact

        # 4. Check Emotional Manipulation & Sensationalism
        for regex, desc, impact in EMOTIONAL_MANIPULATION_PATTERNS:
            matches = re.findall(regex, text_lower)
            if matches:
                flags.append({
                    "category": "Emotional Manipulation",
                    "pattern": desc,
                    "severity": "High" if impact >= 20 else "Medium",
                    "impact": impact,
                    "explanation": f"Contains inflammatory vocabulary '{matches[0]}' aimed at provoking outrage or fear rather than reporting neutral facts.",
                    "detected_instances": matches[:3]
                })
                raw_score += impact

        # 5. Check Unverified Attribution
        for regex, desc, impact in UNVERIFIED_ATTRIBUTION_PATTERNS:
            matches = re.findall(regex, text_lower)
            if matches:
                flags.append({
                    "category": "Attribution Quality",
                    "pattern": desc,
                    "severity": "Medium",
                    "impact": impact,
                    "explanation": f"Attributes assertion vaguely as '{matches[0]}' without naming specific researchers, institutions, or verifiable published studies.",
                    "detected_instances": matches[:3]
                })
                raw_score += impact

        # 6. Check Conspiracy Tropes
        for regex, desc, impact in CONSPIRACY_PATTERNS:
            matches = re.findall(regex, text_lower)
            if matches:
                flags.append({
                    "category": "Conspiracy & Pseudoscience",
                    "pattern": desc,
                    "severity": "Critical",
                    "impact": impact,
                    "explanation": f"Matches documented misinformation trope '{matches[0]}'.",
                    "detected_instances": matches[:3]
                })
                raw_score += impact

        # 7. Check Extreme / Dubious Statistics
        for regex, desc, impact in STATISTICAL_PATTERNS:
            matches = re.findall(regex, text_lower)
            if matches:
                flags.append({
                    "category": "Statistical Integrity",
                    "pattern": desc,
                    "severity": "High",
                    "impact": impact,
                    "explanation": f"Includes extreme statistical figure '{matches[0]}' without citing clinical trial or government dataset.",
                    "detected_instances": matches[:2]
                })
                raw_score += impact

        # Normalize score between 0 and 100
        pattern_score = min(100.0, float(raw_score))
        
        # Determine qualitative risk level
        if pattern_score >= 60:
            risk_level = "High Misinformation Risk"
            risk_color = "red"
        elif pattern_score >= 30:
            risk_level = "Moderate Linguistic Bias / Sensationalism"
            risk_color = "amber"
        elif pattern_score >= 10:
            risk_level = "Low Red Flag Indicators"
            risk_color = "yellow"
        else:
            risk_level = "Clean / Neutral Tone"
            risk_color = "green"

        return {
            "red_flag_score": round(pattern_score, 1),
            "risk_level": risk_level,
            "risk_color": risk_color,
            "total_flags": len(flags),
            "flags": flags,
            "checklist": {
                "clickbait_detected": any(f["category"] == "Clickbait & Curiosity Gap" for f in flags),
                "emotional_manipulation": any(f["category"] == "Emotional Manipulation" for f in flags),
                "vague_sourcing": any(f["category"] == "Attribution Quality" for f in flags),
                "conspiracy_cues": any(f["category"] == "Conspiracy & Pseudoscience" for f in flags),
                "dubious_statistics": any(f["category"] == "Statistical Integrity" for f in flags),
                "excessive_sensationalism": any(f["category"] == "Stylistic Red Flag" for f in flags)
            }
        }
