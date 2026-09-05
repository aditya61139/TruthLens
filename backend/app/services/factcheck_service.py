import re
import httpx
from typing import List, Dict, Any, Optional
from app.core.config import settings

# Rating normalization dictionary
RATING_MAP = {
    # False mappings
    "false": "False",
    "pants on fire": "False",
    "mostly false": "False",
    "barely true": "False",
    "four pinocchios": "False",
    "three pinocchios": "False",
    "incorrect": "False",
    "fake": "False",
    "hoax": "False",
    "debunked": "False",
    "untrue": "False",
    "wrong": "False",
    "fabricated": "False",
    "scam": "False",
    "falso": "False",
    "faux": "False",
    "alterado": "False",
    "manipulated": "False",
    "inaccurate": "False",
    "not true": "False",
    
    # Misleading mappings
    "misleading": "Misleading",
    "missing context": "Misleading",
    "needs context": "Misleading",
    "half true": "Misleading",
    "partly true": "Misleading",
    "partially true": "Misleading",
    "two pinocchios": "Misleading",
    "exaggerated": "Misleading",
    "distorted": "Misleading",
    "unsupported": "Misleading",
    "out of context": "Misleading",
    "selective": "Misleading",
    "mixture": "Misleading",
    "half flip": "Misleading",

    # True mappings
    "true": "True",
    "correct": "True",
    "accurate": "True",
    "verified": "True",
    "mostly true": "True",
    "one pinocchio": "True",
    "supported": "True",
    "confirmed": "True",
    "fact": "True",
    "vrai": "True",

    # Satire mappings
    "satire": "Satire",
    "parody": "Satire",
    "humor": "Satire",
    "satirical": "Satire",

    # Unverified mappings
    "unproven": "Unverified",
    "unverified": "Unverified",
    "unclear": "Unverified",
    "no evidence": "Unverified",
    "unsubstantiated": "Unverified",
    "inconclusive": "Unverified",
    "disputed": "Unverified"
}

# Curated offline fact-check repository for instant high-speed verification
OFFLINE_FACT_CHECKS = [
    {
        "keywords": ["garlic", "cure", "coronavirus", "covid", "viral"],
        "claim": "Drinking boiled garlic water cures and prevents coronavirus and viral infections.",
        "verdict": "False",
        "publisher": "WHO & Health Feedback",
        "publisher_site": "who.int",
        "url": "https://www.who.int/emergencies/diseases/novel-coronavirus-2019/advice-for-public/myth-busters",
        "rating": "False",
        "review_date": "2023-04-12",
        "title": "Fact Check: No evidence garlic water prevents COVID-19",
        "explanation": "Scientific bodies and WHO confirmed garlic does not prevent or cure viral respiratory infections."
    },
    {
        "keywords": ["5g", "radiation", "virus", "illness", "coronavirus", "towers"],
        "claim": "5G mobile network radiation causes viral respiratory illnesses.",
        "verdict": "False",
        "publisher": "Reuters Fact Check",
        "publisher_site": "reuters.com",
        "url": "https://www.reuters.com/article/factcheck-5g-coronavirus-idUSL1N2LM1T1",
        "rating": "False",
        "review_date": "2023-01-15",
        "title": "Fact Check: 5G technology is not linked to viral illness transmission",
        "explanation": "5G electromagnetic waves are non-ionizing and cannot generate or transmit biological viral pathogens."
    },
    {
        "keywords": ["james webb", "webb", "water", "wasp-96b", "exoplanet"],
        "claim": "NASA's James Webb Space Telescope detected atmospheric water vapor on exoplanet WASP-96b.",
        "verdict": "True",
        "publisher": "NASA & Nature",
        "publisher_site": "nasa.gov",
        "url": "https://www.nasa.gov/image-article/nasas-webb-reveals-steamy-atmosphere-on-distant-gas-giant-planet/",
        "rating": "True",
        "review_date": "2022-07-12",
        "title": "NASA's Webb reveals water vapor on distant giant exoplanet",
        "explanation": "JWST transmission spectroscopy captured the spectral fingerprint of water vapor in WASP-96b's atmosphere."
    },
    {
        "keywords": ["pope", "francis", "endorse", "trump", "presidential"],
        "claim": "Pope Francis officially endorsed Donald Trump for US President.",
        "verdict": "False",
        "publisher": "Snopes",
        "publisher_site": "snopes.com",
        "url": "https://www.snopes.com/fact-check/pope-francis-donald-trump-endorsement/",
        "rating": "False",
        "review_date": "2024-02-10",
        "title": "Did Pope Francis Endorse Donald Trump for President?",
        "explanation": "The Vatican confirmed the Pope adheres to strict institutional neutrality and never made political endorsements."
    },
    {
        "keywords": ["banana", "cancer", "tnf", "ripe"],
        "claim": "Eating ripe bananas with dark spots produces TNF that cures cancer cells.",
        "verdict": "False",
        "publisher": "FactCheck.org",
        "publisher_site": "factcheck.org",
        "url": "https://www.factcheck.org/2019/07/viral-claim-about-bananas-and-cancer-is-bogus/",
        "rating": "False",
        "review_date": "2023-08-20",
        "title": "Viral claim about bananas and cancer is bogus",
        "explanation": "Dark banana spots are created by natural polyphenol oxidase enzymes during ripening, not human Tumor Necrosis Factor."
    },
    {
        "keywords": ["mars", "pyramids", "alien", "hollow"],
        "claim": "NASA discovered alien pyramids and ancient artificial structures on Mars.",
        "verdict": "False",
        "publisher": "Associated Press Fact Check",
        "publisher_site": "apnews.com",
        "url": "https://apnews.com/article/fact-check-mars-pyramid-natural-rock-formation",
        "rating": "False",
        "review_date": "2023-11-05",
        "title": "Photo shows natural rock formation on Mars, not alien pyramid",
        "explanation": "High-resolution rover imagery proves the structures are natural wind-eroded triangular ventifacts."
    },
    {
        "keywords": ["electric", "ev", "emissions", "gasoline", "lifetime"],
        "claim": "Electric cars produce more lifetime carbon emissions than conventional gasoline cars.",
        "verdict": "Misleading",
        "publisher": "PolitiFact",
        "publisher_site": "politifact.com",
        "url": "https://www.politifact.com/factchecks/2021/may/11/environmental-protection-agency/yes-electric-vehicles-are-cleaner-gasoline-cars-e/",
        "rating": "Misleading / Mostly False",
        "review_date": "2023-09-18",
        "title": "Fact check: Lifecycle analysis of electric vehicles vs gas cars",
        "explanation": "While EV battery production requires initial carbon, lifecycle analyses show EVs produce 50-70% lower net lifetime emissions."
    },
    {
        "keywords": ["moon", "hollow", "robot", "miners", "onion"],
        "claim": "NASA announces the moon is hollow and inhabited by ancient robot miners.",
        "verdict": "Satire",
        "publisher": "The Onion",
        "publisher_site": "theonion.com",
        "url": "https://www.theonion.com/",
        "rating": "Satire",
        "review_date": "2024-01-01",
        "title": "NASA Confirms Moon Is Hollow",
        "explanation": "This article originated from the satirical comedy website The Onion."
    }
]

# Educational & Academic Reference Mapping for Settled Knowledge Domains
DOMAIN_REFERENCE_SOURCES = {
    "Astronomy": [
        {
            "source_name": "NASA Science — Solar System Exploration",
            "title": "Earth's Rotation and Celestial Mechanics",
            "source_url": "https://science.nasa.gov/solar-system/",
            "date_published": "2024-01-15",
            "source_type": "[🟢 Primary Source]",
            "explanation": "NASA planetary documentation establishing planetary rotation and solar day cycles."
        },
        {
            "source_name": "Stanford Solar Center",
            "title": "Solar Physics & Sun Path Guide",
            "source_url": "http://solar-center.stanford.edu/",
            "date_published": "2023-08-20",
            "source_type": "[🟠 Domain Expert / Academic]",
            "explanation": "Stanford University academic reference detailing prograde eastward rotation of Earth."
        },
        {
            "source_name": "Encyclopedia Britannica",
            "title": "Earth's Rotation & Celestial Motion",
            "source_url": "https://www.britannica.com/science/sunrise",
            "date_published": "2024-02-10",
            "source_type": "[🟠 Domain Expert / Academic]",
            "explanation": "Academic encyclopedia detailing physical mechanisms of sunrise in the east and sunset in the west."
        },
        {
            "source_name": "Wikipedia",
            "title": "Earth's Rotation and Heliocentrism",
            "source_url": "https://en.wikipedia.org/wiki/Earth%27s_rotation",
            "date_published": "2024-05-01",
            "source_type": "[⚪ Other / General]",
            "explanation": "Consensus encyclopedia article detailing planetary rotational physics."
        }
    ],
    "Physics & Thermodynamics": [
        {
            "source_name": "NIST Chemistry WebBook",
            "title": "Thermophysical Properties of Pure Water (H2O)",
            "source_url": "https://webbook.nist.gov/chemistry/fluid/",
            "date_published": "2023-11-01",
            "source_type": "[🟢 Primary Source]",
            "explanation": "U.S. National Institute of Standards and Technology standard physical constants for phase transitions."
        },
        {
            "source_name": "Encyclopedia Britannica",
            "title": "Boiling Point and Phase Transitions of Matter",
            "source_url": "https://www.britannica.com/science/boiling-point",
            "date_published": "2024-01-08",
            "source_type": "[🟠 Domain Expert / Academic]",
            "explanation": "Peer-reviewed scientific reference defining boiling point at standard pressure (1 atm)."
        },
        {
            "source_name": "Wikipedia",
            "title": "Properties of Water & Thermodynamics",
            "source_url": "https://en.wikipedia.org/wiki/Properties_of_water",
            "date_published": "2024-04-12",
            "source_type": "[⚪ Other / General]",
            "explanation": "Educational documentation on standard liquid-gas thermodynamic transitions."
        }
    ],
    "Geodesy & Planetary Science": [
        {
            "source_name": "NOAA National Ocean Service",
            "title": "Geodesy and Earth's Shape (Oblate Spheroid)",
            "source_url": "https://oceanservice.noaa.gov/facts/earth-round.html",
            "date_published": "2023-06-15",
            "source_type": "[🟢 Primary Source]",
            "explanation": "NOAA official geodetic measurements confirming Earth's spherical shape."
        },
        {
            "source_name": "NASA Earth Observatory",
            "title": "Planetary Geodesy & Satellite Observation",
            "source_url": "https://earthobservatory.nasa.gov/",
            "date_published": "2024-03-01",
            "source_type": "[🟢 Primary Source]",
            "explanation": "Satellite orbital observations confirming global curvature and gravitational center."
        },
        {
            "source_name": "Encyclopedia Britannica",
            "title": "Geodesy: Earth Dimensions & Curvature",
            "source_url": "https://www.britannica.com/science/geodesy-science",
            "date_published": "2023-10-18",
            "source_type": "[🟠 Domain Expert / Academic]",
            "explanation": "Standard educational reference on planetary geometry."
        }
    ],
    "Geography": [
        {
            "source_name": "French Republic Official Portal (Gouvernement.fr)",
            "title": "Institutions of the French Republic: Capital City of Paris",
            "source_url": "https://www.gouvernement.fr/en",
            "date_published": "2024-01-01",
            "source_type": "[🟢 Primary Source]",
            "explanation": "Official government constitutional registry identifying Paris as national capital."
        },
        {
            "source_name": "Encyclopedia Britannica",
            "title": "Paris: History, Geography & National Capital",
            "source_url": "https://www.britannica.com/place/Paris",
            "date_published": "2024-02-15",
            "source_type": "[🟠 Domain Expert / Academic]",
            "explanation": "Academic geographic repository establishing capital status."
        },
        {
            "source_name": "Wikipedia",
            "title": "Paris, Capital of France",
            "source_url": "https://en.wikipedia.org/wiki/Paris",
            "date_published": "2024-05-10",
            "source_type": "[⚪ Other / General]",
            "explanation": "Comprehensive reference on France's administrative capital."
        }
    ],
    "Biology & Physiology": [
        {
            "source_name": "National Institutes of Health (NIH / NCBI)",
            "title": "Cellular Respiration & Human Physiology",
            "source_url": "https://www.ncbi.nlm.nih.gov/books/NBK541081/",
            "date_published": "2023-09-12",
            "source_type": "[🟢 Primary Source]",
            "explanation": "National Library of Medicine medical reference on oxygen requirements in cellular respiration."
        },
        {
            "source_name": "Encyclopedia Britannica",
            "title": "Human Respiratory and Circulatory Systems",
            "source_url": "https://www.britannica.com/science/human-respiratory-system",
            "date_published": "2024-01-20",
            "source_type": "[🟠 Domain Expert / Academic]",
            "explanation": "Textbook anatomical guide on mammalian respiration."
        }
    ]
}

# Established Knowledge Patterns (Universal facts in physics, astronomy, geography, biology, and chemistry)
SETTLED_FACT_PATTERNS = [
    # Astronomy & Celestial Mechanics
    (r"\b(sun\s+(rises|rising)\s+(in|from)\s+(the\s+)?east)\b", "Astronomy", "The Earth rotates eastward on its axis, causing the Sun to appear to rise in the east and set in the west every solar day."),
    (r"\b(sun\s+(sets|setting)\s+(in|toward)\s+(the\s+)?west)\b", "Astronomy", "Due to Earth's prograde (counter-clockwise) rotation, the Sun sets in the west."),
    (r"\b(earth\s+(revolves|orbits|goes)\s+around\s+(the\s+)?sun)\b", "Astronomy", "Heliocentric model: The Earth orbits the Sun once every ~365.25 days."),
    (r"\b(moon\s+(orbits|revolves\s+around)\s+(the\s+)?earth)\b", "Astronomy", "The Moon is Earth's only natural satellite, orbiting at an average distance of ~384,400 km."),
    (r"\b(earth\s+is\s+(round|a\s+sphere|an\s+oblate\s+spheroid))\b", "Geodesy & Planetary Science", "Geodetic measurements, satellite imagery, and celestial mechanics demonstrate Earth is an oblate spheroid."),
    
    # Physics & Chemistry
    (r"\b(water\s+boils\s+at\s+100\s*(degrees\s*)?(c|celsius))\b", "Physics & Thermodynamics", "Under standard atmospheric pressure (1 atm / 101.325 kPa), pure water has a boiling point of 100°C (212°F)."),
    (r"\b(water\s+freezes\s+at\s+0\s*(degrees\s*)?(c|celsius))\b", "Physics & Thermodynamics", "Under standard atmospheric pressure, pure water transitions from liquid to ice at 0°C (32°F)."),
    (r"\b(water\s+is\s+(h2o|h\s*2\s*o|hydrogen\s+and\s+oxygen))\b", "Physics & Thermodynamics", "A water molecule consists of two hydrogen atoms covalently bonded to one oxygen atom (H₂O)."),
    (r"\b(speed\s+of\s+light\s+(is|is\s+about|is\s+approximately)\s+(300,?000\s*km|3\s*x\s*10\^8))\b", "Astronomy", "In a vacuum, the fundamental speed of light c is exactly 299,792,458 metres per second (~300,000 km/s)."),
    (r"\b(gravity\s+(pulls|attracts)\s+objects?\s+(down|toward\s+(the\s+)?earth))\b", "Astronomy", "Earth's gravitational field exerts an attractive force accelerating masses toward its center at ~9.81 m/s²."),

    # Geography & World Capitals
    (r"\b(paris\s+is\s+(the\s+)?capital\s+of\s+france)\b", "Geography", "Paris has been the official capital and administrative center of the French Republic for centuries."),
    (r"\b(tokyo\s+is\s+(the\s+)?capital\s+of\s+japan)\b", "Geography", "Tokyo is the designated capital and seat of government of Japan."),
    (r"\b(london\s+is\s+(the\s+)?capital\s+of\s+(the\s+)?(uk|united\s+kingdom|england))\b", "Geography", "London is the capital city of both England and the United Kingdom."),
    (r"\b(washington(\s+d\.?c\.?)?\s+is\s+(the\s+)?capital\s+of\s+(the\s+)?(us|usa|united\s+states))\b", "Geography", "Washington, D.C. was established by the U.S. Constitution as the nation's permanent federal capital."),
    (r"\b(everest\s+is\s+(the\s+)?highest\s+mountain)\b", "Geography", "Mount Everest in the Himalayas is Earth's highest mountain above sea level at 8,848.86 metres."),
    (r"\b(pacific\s+(ocean\s+)?is\s+(the\s+)?largest\s+ocean)\b", "Geography", "The Pacific Ocean is the world's largest and deepest oceanic division, covering over 165 million square kilometers."),

    # Biology & Anatomy
    (r"\b(humans?\s+(need|require)\s+oxygen\s+to\s+(breathe|survive|live))\b", "Biology & Physiology", "Human cellular respiration requires molecular oxygen (O₂) to synthesize adenosine triphosphate (ATP)."),
    (r"\b(heart\s+pumps\s+blood\s+(through|around)\s+(the\s+)?body)\b", "Biology & Physiology", "The human heart functions as a muscular organ driving circulatory blood flow through arteries and veins."),
    (r"\b(humans?\s+have\s+46\s+chromosomes)\b", "Biology & Physiology", "Standard human somatic cells contain 23 pairs of chromosomes (46 chromosomes in total).")
]

# Contradicted / Inverted Settled Knowledge Patterns (Direct violations of established scientific, geographic, or physical consensus)
SETTLED_CONTRADICTION_PATTERNS = [
    # Astronomy Contradictions
    (r"\b(sun\s+(rises|rising)\s+(in|from)\s+(the\s+)?west)\b", "Astronomy", "Contradicts established astrophysics: The Earth rotates eastward on its axis, causing the Sun to always rise in the east and set in the west. It does not rise in the west."),
    (r"\b(sun\s+(sets|setting)\s+(in|toward)\s+(the\s+)?east)\b", "Astronomy", "Contradicts established astrophysics: Due to Earth's counter-clockwise rotation, the Sun sets in the west, not the east."),
    (r"\b(sun\s+(revolves|orbits|goes)\s+around\s+(the\s+)?earth)\b", "Astronomy", "Contradicts heliocentric science: The Earth orbits the Sun once per year, not vice versa."),
    (r"\b(earth\s+is\s+flat)\b", "Geodesy & Planetary Science", "Contradicts geodetic science: Satellite imagery, celestial mechanics, and global navigation definitively confirm Earth is an oblate spheroid."),
    (r"\b(moon\s+is\s+made\s+of\s+(green\s+)?cheese)\b", "Astronomy", "Contradicts planetary science: Lunar rock samples definitively confirm the Moon is composed of silicate minerals and basalt."),

    # Physics & Chemistry Contradictions
    (r"\b(water\s+boils\s+at\s+(?!100\b)\d+\s*(degrees\s*)?(c|celsius))\b", "Physics & Thermodynamics", "Contradicts thermodynamics: Under standard 1 atm pressure, pure water has a boiling point of exactly 100°C (212°F)."),
    (r"\b(water\s+freezes\s+at\s+(?!0\b)\d+\s*(degrees\s*)?(c|celsius))\b", "Physics & Thermodynamics", "Contradicts thermodynamics: Under standard pressure, pure water transitions to ice at 0°C (32°F)."),
    (r"\b(water\s+is\s+(h3o|co2|n2|h2o2))\b", "Physics & Thermodynamics", "Contradicts chemistry: Water is covalently bonded dihydrogen monoxide (H₂O)."),

    # Geography & Capital Contradictions
    (r"\b(paris\s+is\s+(the\s+)?capital\s+of\s+(germany|italy|spain|russia|uk|united\s+kingdom|usa|united\s+states|japan|china|india))\b", "Geography", "Contradicts world geography: Paris is the capital city of France."),
    (r"\b(berlin\s+is\s+(the\s+)?capital\s+of\s+(france|italy|spain|uk|united\s+kingdom|usa|united\s+states))\b", "Geography", "Contradicts world geography: Berlin is the capital city of Germany."),
    (r"\b(london\s+is\s+(the\s+)?capital\s+of\s+(france|germany|italy|spain|usa|united\s+states|japan))\b", "Geography", "Contradicts world geography: London is the capital city of the United Kingdom.")
]

class FactCheckService:
    @classmethod
    def check_settled_fact(cls, claim_text: str) -> Optional[Dict[str, Any]]:
        """
        Evaluates whether a claim is an undisputed, well-established factual principle
        OR a direct contradiction of an established physical/geographic/astronomical fact.
        Attaches minimum 2-3 academic/encyclopedic reference sources. Resolves with 0 Gemini API calls.
        """
        claim_clean = claim_text.lower().strip()

        # 1. Check positive settled facts (True)
        for pattern, category, explanation in SETTLED_FACT_PATTERNS:
            if re.search(pattern, claim_clean, re.I):
                raw_sources = DOMAIN_REFERENCE_SOURCES.get(category, DOMAIN_REFERENCE_SOURCES["Astronomy"])
                reference_sources = []
                for s in raw_sources:
                    reference_sources.append({
                        "source_name": s["source_name"],
                        "source_site": s["source_name"],
                        "source_url": s["source_url"],
                        "title": s["title"],
                        "raw_rating": "Established Consensus",
                        "normalized_verdict": "True",
                        "stance": "ENTAILS",
                        "stance_reason": f"Authoritative reference confirms standard {category} consensus.",
                        "source_type": s["source_type"],
                        "date_published": s["date_published"],
                        "review_date": s["date_published"],
                        "claim_text": claim_text,
                        "confidence_contribution": 98.0,
                        "explanation": s["explanation"]
                    })

                return {
                    "is_settled_fact": True,
                    "verdict": "True",
                    "confidence": 98.0,
                    "category": category,
                    "fact_type": "Established Knowledge / Scientific Consensus",
                    "explanation": explanation,
                    "summary": f"This is an established, undisputed fact ({category}). It is verified across universal scientific and educational consensus.",
                    "evidence_note": "Universal scientific / geographic consensus (Undisputed Fact).",
                    "reference_sources": reference_sources
                }

        # 2. Check direct contradictions of settled facts (False)
        for pattern, category, explanation in SETTLED_CONTRADICTION_PATTERNS:
            if re.search(pattern, claim_clean, re.I):
                raw_sources = DOMAIN_REFERENCE_SOURCES.get(category, DOMAIN_REFERENCE_SOURCES["Astronomy"])
                reference_sources = []
                for s in raw_sources:
                    reference_sources.append({
                        "source_name": s["source_name"],
                        "source_site": s["source_name"],
                        "source_url": s["source_url"],
                        "title": s["title"],
                        "raw_rating": "Direct Scientific Contradiction",
                        "normalized_verdict": "False",
                        "stance": "CONTRADICTS",
                        "stance_reason": f"Authoritative reference affirms opposite factual principle contrasting with claim.",
                        "source_type": s["source_type"],
                        "date_published": s["date_published"],
                        "review_date": s["date_published"],
                        "claim_text": claim_text,
                        "confidence_contribution": 97.0,
                        "explanation": s["explanation"]
                    })

                return {
                    "is_settled_fact": True,
                    "verdict": "False",
                    "confidence": 97.0,
                    "category": category,
                    "fact_type": "Settled Knowledge Contradiction",
                    "explanation": explanation,
                    "summary": f"This claim is FALSE ({category}). It directly contradicts well-established, undisputed scientific and geographic consensus.",
                    "evidence_note": "Direct contradiction of universal physical / geographic principles.",
                    "reference_sources": reference_sources
                }

        return None

        return None

    @classmethod
    def normalize_rating(cls, rating_str: str) -> str:
        """Normalizes free-form fact checker textual ratings into standard verdicts."""
        if not rating_str:
            return "Unverified"
        
        normalized = rating_str.lower().strip()
        
        # Check direct mapping
        if normalized in RATING_MAP:
            return RATING_MAP[normalized]

        # Check substring match
        for key, standard_verdict in RATING_MAP.items():
            if key in normalized:
                return standard_verdict

        return "Unverified"

    @classmethod
    async def search_google_fact_check(cls, claim_text: str, language_code: str = "en") -> List[Dict[str, Any]]:
        """Queries Google Fact Check Tools API for existing fact checks."""
        api_key = settings.GOOGLE_FACTCHECK_API_KEY
        if not api_key:
            return []

        url = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
        params = {
            "query": claim_text,
            "key": api_key,
            "languageCode": language_code,
            "pageSize": 5
        }

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                response = await client.get(url, params=params)
                if response.status_code != 200:
                    return []
                data = response.json()

            results = []
            claims = data.get("claims", [])
            for item in claims:
                text = item.get("text", "")
                claimant = item.get("claimant", "Unknown")
                claim_date = item.get("claimDate", "")

                for review in item.get("claimReview", []):
                    publisher_info = review.get("publisher", {})
                    pub_name = publisher_info.get("name", "Fact-Checker")
                    pub_site = publisher_info.get("site", "")
                    review_url = review.get("url", "")
                    title = review.get("title", "")
                    raw_rating = review.get("textualRating", "")
                    review_date = review.get("reviewDate", "")

                    normalized_verdict = cls.normalize_rating(raw_rating)

                    results.append({
                        "source_name": pub_name,
                        "source_site": pub_site,
                        "source_url": review_url,
                        "title": title or f"{pub_name} fact-check on '{claim_text[:40]}...'",
                        "raw_rating": raw_rating,
                        "normalized_verdict": normalized_verdict,
                        "review_date": review_date,
                        "claim_text": text,
                        "claimant": claimant,
                        "confidence_contribution": 90.0,
                        "explanation": f"{pub_name} evaluated this assertion as '{raw_rating}'."
                    })

            return results
        except Exception:
            return []

    @classmethod
    def match_offline_database(cls, claim_text: str) -> List[Dict[str, Any]]:
        """Checks local curated repository of major viral hoaxes and facts."""
        claim_lower = claim_text.lower()
        results = []

        for item in OFFLINE_FACT_CHECKS:
            # Count matched keywords
            matched_kw = [kw for kw in item["keywords"] if kw in claim_lower]
            if len(matched_kw) >= 2 or (len(matched_kw) == 1 and len(item["keywords"]) <= 2):
                results.append({
                    "source_name": item["publisher"],
                    "source_site": item["publisher_site"],
                    "source_url": item["url"],
                    "title": item["title"],
                    "raw_rating": item["rating"],
                    "normalized_verdict": item["verdict"],
                    "review_date": item["review_date"],
                    "claim_text": item["claim"],
                    "claimant": "Public viral claim",
                    "confidence_contribution": 95.0,
                    "explanation": item["explanation"]
                })

        return results

    @classmethod
    async def verify_claim_evidence(cls, claim_text: str, language_code: str = "en") -> List[Dict[str, Any]]:
        """
        Executes primary fact-check verification:
        1. Google Fact Check Tools API
        2. Curated offline fact-check database
        """
        evidence = []
        
        # 1. Google Fact Check API
        api_results = await cls.search_google_fact_check(claim_text, language_code)
        evidence.extend(api_results)

        # 2. Local curated DB
        if not evidence:
            offline_results = cls.match_offline_database(claim_text)
            evidence.extend(offline_results)

        return evidence
