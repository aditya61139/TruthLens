import re
import socket
import ipaddress
import urllib.parse
import datetime
from typing import List, Dict, Any, Optional, Tuple
from dateutil import parser as date_parser
import httpx
from bs4 import BeautifulSoup
import trafilatura

CLEANUP_PREFIXES = [
    r"^(breaking news|breaking|alert|urgent|exclusive|must read|viral|forwarded as received|rt\s*@[a-zA-Z0-9_]+):?\s*",
    r"^(did you know that|have you heard that|is it true that|i heard that|people are saying that)\s*",
    r"^(fact check:|claim:|check this out:|look at this:)\s*",
    r"^(rumor has it that|unbelievable:|shocking:)\s*",
    r"^(can you tell me if|please verify if|verify if|is it true that|tell me if)\s*"
]

TIME_SENSITIVE_KEYWORDS = [
    r"\b(recent|recently|currently|today|yesterday|this week|this month|just now|just happened|breaking|latest|now|ongoing|live)\b",
    r"\b(flash flood|flood|floods|flooding|earthquake|earthquakes|landslide|landslides|tsunami|tsunamis|wildfire|wildfires|tornado|tornadoes|hurricane|hurricanes|cyclone|cyclones|explosion|explosions|eruption|shooting|shootings|plane crash|train crash|protest|protests|strike|strikes|resigned|assassinated|arrested|attack|attacks|missile|missiles|disaster|relief|victims)\b",
    r"^(is there|are there|was there|did\s+[a-zA-Z]+\s+happen|has there been|what happened in)\b"
]

QUESTION_PATTERNS = [
    (r"^is there\s+(an|a)?\s*(recent|new)?\s*", ""),
    (r"^are there\s+(any)?\s*(recent|new)?\s*", ""),
    (r"^was there\s+(an|a)?\s*(recent|new)?\s*", ""),
    (r"^has there been\s+(an|a)?\s*(recent|new)?\s*", ""),
    (r"^did\s+(an|a)?\s*", ""),
    (r"^(is|are|was|were)\s+", ""),
    (r"\?+$", "")
]

STOP_WORDS_QUERY = {
    "is", "there", "a", "an", "the", "near", "in", "around", "at", "to", "for", "of",
    "on", "by", "with", "from", "about", "did", "was", "were", "are", "been", "has", "have", "had"
}

class ClaimExtractor:
    @staticmethod
    def is_url(text: str) -> bool:
        text = text.strip()
        return text.startswith("http://") or text.startswith("https://") or (text.startswith("www.") and "." in text)

    @classmethod
    def is_time_sensitive(cls, text: str) -> bool:
        """Detects whether a claim refers to an ongoing, recent, or breaking event."""
        text_lower = text.lower().strip()
        for pattern in TIME_SENSITIVE_KEYWORDS:
            if re.search(pattern, text_lower, re.I):
                return True
        return False

    @classmethod
    def detect_query_mode(cls, text: str) -> str:
        """
        Classifies input into:
        - Mode A: 'Claim Verification' (direct statement/assertion to fact check)
        - Mode B: 'Event Query' (question about a recent event or ongoing situation)
        - Mode C: 'Hybrid' (specific numerical/causal claim tied to an ongoing/recent event)
        """
        text_clean = text.lower().strip()

        # Check for Question / Event Inquiry patterns (Mode B)
        event_query_patterns = [
            r"^(is there|are there|was there|were there|has there been|have there been)\b",
            r"^(what happened|what is happening|what's happening|what's going on)\b",
            r"^(any updates on|any news on|what is the status of|what are the latest updates on)\b",
            r"^(can you tell me about|tell me about|how did the|why did the)\b",
            r"\?$"
        ]
        
        is_question = any(re.search(pat, text_clean) for pat in event_query_patterns)
        is_recent_or_event = cls.is_time_sensitive(text)

        # Check for Hybrid mode: Contains a specific claim/assertion AND event context
        has_specific_numbers = bool(re.search(r"\b(\d+|hundreds|thousands|lakhs|crores|millions|dozens|all|none|zero)\b", text_clean))
        has_definitive_claim_verb = bool(re.search(r"\b(killed|died|injur|casualt|destroy|collaps|ban|refus|caus|responsib|fail|scam|steal|stolen|sent|fund|aid|coverup|lie|alleg|accus|fault|blam|delay|deni|withheld|negligen|corrupt|not sent|no relief|without)\b", text_clean))
        has_negation_assertion = bool(re.search(r"\b(not|never|didn't|hasn't|hadn't|failed to|refused to|denied)\b", text_clean))

        if is_recent_or_event and not is_question and (has_specific_numbers or has_definitive_claim_verb or has_negation_assertion):
            return "Hybrid"

        if is_question and is_recent_or_event:
            return "Event Query"

        if is_question:
            # If asking general question about event
            if any(w in text_clean for w in ["flood", "earthquake", "cyclone", "war", "conflict", "election", "crash", "strike", "fire", "attack", "protest"]):
                return "Event Query"

        return "Claim Verification"

    @classmethod
    def detect_event_category(cls, text: str) -> Tuple[str, str]:
        """
        Returns (emoji, label) for event category.
        Examples:
        🌊 Natural Disaster — Flooding
        🌍 Geopolitics — Armed Conflict
        🏛️ Politics — Election / Governance
        💰 Economy — Financial Markets
        🔬 Science — Discovery / Research
        ⚖️ Law — Court Ruling / Justice
        """
        t = text.lower()
        if any(w in t for w in ["flood", "flash flood", "inundat", "submerge", "dam burst", "monsoon flood"]):
            return "🌊", "Natural Disaster — Flooding"
        if any(w in t for w in ["earthquake", "quake", "tremor", "aftershock", "seismic"]):
            return "🌋", "Natural Disaster — Earthquake"
        if any(w in t for w in ["cyclone", "hurricane", "typhoon", "tornado", "storm"]):
            return "🌀", "Natural Disaster — Storm / Cyclone"
        if any(w in t for w in ["wildfire", "forest fire", "bushfire", "fire outbreak"]):
            return "🔥", "Natural Disaster — Wildfire"
        if any(w in t for w in ["war", "conflict", "missile", "airstrike", "gaza", "israel", "ukraine", "russia", "military", "troops"]):
            return "🌍", "Geopolitics — Armed Conflict"
        if any(w in t for w in ["election", "vote", "parliament", "congress", "minister", "prime minister", "president", "policy", "bill", "treaty"]):
            return "🏛️", "Politics — Governance & Election"
        if any(w in t for w in ["stock", "market", "crash", "inflation", "gdp", "economy", "recession", "bank", "crypto", "currency"]):
            return "💰", "Economy — Financial Markets"
        if any(w in t for w in ["court", "supreme court", "verdict", "judge", "ruling", "arrest", "sentenced", "lawsuit", "trial"]):
            return "⚖️", "Law — Court Ruling & Justice"
        if any(w in t for w in ["iphone", "apple", "samsung", "android", "smartphone", "gpu", "nvidia", "intel", "amd", "software", "windows", "macbook", "gadget", "launch", "chip", "ios", "google pixel"]):
            return "📱", "Technology — Devices & Releases"
        if any(w in t for w in ["movie", "film", "cinema", "hollywood", "bollywood", "actor", "actress", "album", "song", "celebrity", "grammy", "oscar"]):
            return "🎬", "Entertainment & Media"
        if any(w in t for w in ["vaccine", "cure", "cancer", "virus", "who", "cdc", "health", "doctor", "medicine", "disease", "covid", "pandemic"]):
            return "🏥", "Health & Medicine"
        if any(w in t for w in ["cricket", "football", "fifa", "olympics", "championship", "tournament", "nba", "ipl", "match", "world cup"]):
            return "🏆", "Sports & Athletics"
        if any(w in t for w in ["nasa", "space", "telescope", "planet", "discovery", "mars", "biology", "physics", "ai", "quantum"]):
            return "🔬", "Science — Discovery & Technology"
        return "📰", "General Breaking News"

    @classmethod
    def extract_event_geo_region(cls, text: str, evidence: List[Dict[str, Any]] = None) -> str:
        """
        Extracts specific geographic regions, states, cities, or countries from
        the user query and retrieved evidence, replacing generic 'Regional / National'.
        """
        combined = text.lower()
        if evidence:
            for ev in evidence[:5]:
                combined += " " + (ev.get("title", "") + " " + ev.get("explanation", "")).lower()

        # Known regional mappings (Country / Province / City)
        geo_patterns = [
            (r"\b(nepal|kathmandu|bagmati|koshi|gandaki|lalitpur|bhaktapur)\b", "Kathmandu Valley & Provinces, Nepal" if "kathmandu" in combined or "bagmati" in combined else "Nepal"),
            (r"\b(assam|brahmaputra|guwahati|dhemaji|cachar)\b", "Assam, India"),
            (r"\b(kerala|wayanad)\b", "Wayanad & Kerala, India"),
            (r"\b(tibet|lhasa|yarlung tsangpo)\b", "Tibet Autonomous Region"),
            (r"\b(turkey|t[uü]rkiye|gaziantep|kahramanmara[sş])\b", "Southeastern Türkiye"),
            (r"\b(syria|aleppo|damascus)\b", "Syria"),
            (r"\b(gaza|israel|palestine|west bank|tel aviv|jerusalem)\b", "Gaza Strip & Israel"),
            (r"\b(ukraine|kyiv|kharkiv|donetsk|crimea)\b", "Ukraine"),
            (r"\b(russia|moscow|kursk)\b", "Russia"),
            (r"\b(valencia|spain|barcelona|madrid)\b", "Valencia & Eastern Spain"),
            (r"\b(japan|tokyo|noto|ishikawa)\b", "Ishikawa Prefecture & Japan"),
            (r"\b(taiwan|taipei|hualien)\b", "Hualien & Eastern Taiwan"),
            (r"\b(pakistan|balochistan|punjab|karachi|lahore)\b", "Pakistan"),
            (r"\b(bangladesh|dhaka|sylhet|feni)\b", "Feni & Eastern Bangladesh"),
            (r"\b(florida|tampa|orlando|helene|milton)\b", "Florida, United States"),
            (r"\b(california|los angeles|san francisco)\b", "California, United States"),
            (r"\b(india|delhi|mumbai|chennai|kolkata)\b", "India"),
        ]

        for pat, region_name in geo_patterns:
            if re.search(pat, combined, re.I):
                return region_name

        # Fallback: check query for capitalized proper nouns or entities
        words = [w.strip() for w in re.findall(r"\b[A-Z][a-z]+\b", text) if w.lower() not in {"is", "there", "what", "where", "when", "why", "how", "recent", "flash", "flood", "earthquake"}]
        if words:
            return ", ".join(words[:2])

        return "Affected Region"

    @classmethod
    def format_event_title(cls, claim_text: str, category_label: str, region: str) -> str:
        """
        Formats a clean, journalistic event title rather than raw 'Report: ...'.
        """
        cleaned = claim_text.strip()
        for pat, repl in QUESTION_PATTERNS:
            cleaned = re.sub(pat, repl, cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r"^(is there\s+(a|an)?|what happened in\s+|did\s+(a|an)?|any updates on\s+)", "", cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r"[?!.]+$", "", cleaned).strip()

        # Title-case keywords
        words = cleaned.split()
        if len(words) <= 7:
            title_core = " ".join([w.capitalize() if w.lower() not in {"in", "on", "at", "to", "for", "of", "and", "a", "an", "the", "near"} else w.lower() for w in words])
            if region and region not in title_core and "Affected" not in region:
                return f"{title_core} in {region}"
            return title_core

        return f"{category_label.split('—')[-1].strip()} in {region}" if region and "Affected" not in region else f"{category_label}: {cleaned[:50]}"

    @classmethod
    def extract_event_temporal_info(
        cls,
        evidence: List[Dict[str, Any]],
        claim_text: str = "",
        current_date: Optional[datetime.datetime] = None
    ) -> Dict[str, Any]:
        """
        Analyzes evidence timestamps, review dates, and article text to determine:
        - most_recent_date (YYYY-MM-DD and formatted display)
        - most_recent_time (exact time string only if available in sources, otherwise None)
        - date_range (e.g. 'September 27–29, 2024')
        - status ('🔴 Ongoing' | '🟡 Developing' | '🟢 Resolved')
        - status_reason (human-readable justification based on temporal distance and resolution cues)
        """
        if current_date is None:
            current_date = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        elif current_date.tzinfo is not None:
            current_date = current_date.astimezone(datetime.timezone.utc).replace(tzinfo=None)

        all_dates: List[datetime.datetime] = []
        found_time: Optional[str] = None

        time_pattern = re.compile(r"\b(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm|NPT|npt|UTC|utc|GMT|gmt|IST|ist|EST|est))\b")

        for ev in evidence:
            date_str = ev.get("date_published") or ev.get("review_date") or ""
            text_corpus = f"{ev.get('title', '')} {ev.get('explanation', '')} {date_str}"

            # Check for exact time mention
            if not found_time:
                time_match = time_pattern.search(text_corpus)
                if time_match:
                    found_time = time_match.group(1).strip()

            # Parse date strings
            if date_str and date_str.lower() not in ["recent", "latest", "date not available"]:
                try:
                    dt = date_parser.parse(date_str, fuzzy=True)
                    # Exclude unrealistic future dates
                    if dt <= current_date + datetime.timedelta(days=2):
                        all_dates.append(dt)
                except Exception:
                    pass

            # Search text corpus for ISO or Month Day dates
            date_regex = re.findall(r"\b(20\d{2}[-/]\d{1,2}[-/]\d{1,2})\b", text_corpus)
            for d in date_regex:
                try:
                    dt = date_parser.parse(d)
                    if dt <= current_date + datetime.timedelta(days=2):
                        all_dates.append(dt)
                except Exception:
                    pass

            month_regex = re.findall(
                r"\b((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?(?:,?\s*20\d{2})?)\b",
                text_corpus,
                flags=re.IGNORECASE
            )
            for m in month_regex:
                try:
                    dt = date_parser.parse(m, default=datetime.datetime(current_date.year, 1, 1))
                    if dt <= current_date + datetime.timedelta(days=2):
                        all_dates.append(dt)
                except Exception:
                    pass

        has_resolution_cues = False
        resolution_keywords = [
            r"\b(receded|water receded|rescue concluded|search called off|cleared debris|reopened highway|reopened roads|final death toll|death toll reached|weeks after|months after|recovery phase)\b"
        ]
        for ev in evidence:
            full_snippet = f"{ev.get('title', '')} {ev.get('explanation', '')}".lower()
            if any(re.search(kw, full_snippet) for kw in resolution_keywords):
                has_resolution_cues = True
                break

        if all_dates:
            most_recent_dt = max(all_dates)
            earliest_dt = min(all_dates)

            most_recent_iso = most_recent_dt.strftime("%Y-%m-%d")
            most_recent_display = most_recent_dt.strftime("%B %d, %Y")

            # Format date range
            if (most_recent_dt - earliest_dt).days <= 1:
                date_range = most_recent_display
            elif earliest_dt.year == most_recent_dt.year and earliest_dt.month == most_recent_dt.month:
                date_range = f"{earliest_dt.strftime('%B %d')}–{most_recent_dt.strftime('%d, %Y')}"
            elif earliest_dt.year == most_recent_dt.year:
                date_range = f"{earliest_dt.strftime('%B %d')} – {most_recent_dt.strftime('%B %d, %Y')}"
            else:
                date_range = f"{earliest_dt.strftime('%B %Y')} – {most_recent_dt.strftime('%B %Y')}"

            # Calculate days elapsed
            days_ago = (current_date.date() - most_recent_dt.date()).days

            if days_ago > 21 or has_resolution_cues:
                status = "🟢 Resolved"
                if days_ago > 30:
                    status_reason = f"Event occurred over {days_ago // 30} month(s) ago; floodwaters have receded and recovery operations are completed."
                else:
                    status_reason = f"Event occurred {days_ago} days ago; emergency rescue phase has concluded."
            elif days_ago <= 3 and not has_resolution_cues:
                status = "🔴 Ongoing"
                status_reason = "Active emergency event occurring within the last 72 hours; emergency services deployed."
            else:
                status = "🟡 Developing"
                status_reason = f"Recent event from {days_ago} days ago with ongoing relief and damage assessment."

        else:
            # Fallback when no explicit dates were parseable
            most_recent_iso = current_date.strftime("%Y-%m-%d")
            most_recent_display = "Recent / Date not specified in reports"
            date_range = "Recent"
            status = "🟢 Resolved" if has_resolution_cues else "🟡 Developing"
            status_reason = "Situation reported in recent records; detailed timeline under monitoring."

        return {
            "most_recent_date": most_recent_iso,
            "most_recent_date_display": most_recent_display,
            "most_recent_time": found_time,
            "date_range": date_range,
            "status": status,
            "status_reason": status_reason
        }

    @classmethod
    def normalize_search_query(cls, text: str) -> str:
        """
        Converts conversational question-form claims (e.g. 'is there a recent flash flood near tibet?')
        into clean, search-engine-friendly entity queries (e.g. 'flash flood Tibet').
        """
        cleaned = text.strip()
        # Remove question framing
        for pat, repl in QUESTION_PATTERNS:
            cleaned = re.sub(pat, repl, cleaned, flags=re.IGNORECASE).strip()

        # Remove punctuation
        cleaned = re.sub(r"[^\w\s-]", "", cleaned)

        # Extract tokens excluding noise
        tokens = [w for w in cleaned.split() if w.lower() not in STOP_WORDS_QUERY and len(w) > 1]
        
        # Remove generic recency word from the search query tokens so search engine finds topical results
        filtered_tokens = [w for w in tokens if w.lower() not in ["recent", "recently", "currently", "latest"]]
        
        if filtered_tokens:
            return " ".join(filtered_tokens)
        return " ".join(tokens) if tokens else cleaned

    @classmethod
    def validate_safe_url(cls, url: str) -> Tuple[bool, str]:
        """Validates that a URL uses HTTP/HTTPS and does not resolve to private, loopback, or cloud metadata IPs (SSRF protection)."""
        try:
            parsed = urllib.parse.urlparse(url)
            if parsed.scheme not in ("http", "https"):
                return False, f"Unsupported URL scheme '{parsed.scheme}'. Only HTTP and HTTPS are permitted."
            
            hostname = parsed.hostname
            if not hostname:
                return False, "Invalid URL: missing hostname."

            # Block obvious cloud metadata and localhost names directly
            if hostname.lower() in ("localhost", "127.0.0.1", "::1", "metadata.google.internal"):
                return False, "Access to local or cloud metadata endpoints is prohibited."

            # Resolve DNS and verify every returned IP address
            addr_info = socket.getaddrinfo(hostname, None)
            for entry in addr_info:
                ip_str = entry[4][0]
                ip = ipaddress.ip_address(ip_str)
                if ip.is_loopback or ip.is_private or ip.is_link_local or ip.is_reserved or ip.is_multicast:
                    return False, f"Access to private or restricted network address ({ip_str}) is prohibited."

            return True, ""
        except Exception as e:
            return False, f"Failed to validate URL host: {str(e)}"

    @classmethod
    async def extract_from_url(cls, url: str) -> Dict[str, Any]:
        """Fetch article title and main body text from URL safely using trafilatura."""
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url

        is_safe, error_msg = cls.validate_safe_url(url)
        domain = urllib.parse.urlparse(url).netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]

        if not is_safe:
            return {
                "url": url,
                "domain": domain,
                "title": "",
                "text": "",
                "error": error_msg
            }

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 TruthLens/1.0"
        }

        try:
            current_url = url
            html_content = ""
            redirect_count = 0
            
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=False, headers=headers) as client:
                while redirect_count < 3:
                    resp = await client.get(current_url)
                    if resp.status_code in (301, 302, 303, 307, 308):
                        next_url = resp.headers.get("Location")
                        if not next_url:
                            break
                        if not next_url.startswith("http"):
                            next_url = urllib.parse.urljoin(current_url, next_url)
                        is_safe_redirect, redirect_err = cls.validate_safe_url(next_url)
                        if not is_safe_redirect:
                            return {
                                "url": next_url,
                                "domain": domain,
                                "title": "",
                                "text": "",
                                "error": f"Redirect blocked: {redirect_err}"
                            }
                        current_url = next_url
                        redirect_count += 1
                        continue

                    if resp.status_code != 200:
                        return {
                            "url": current_url,
                            "domain": domain,
                            "title": "",
                            "text": "",
                            "error": f"HTTP {resp.status_code}"
                        }
                    html_content = resp.text
                    break
        except Exception as e:
            return {
                "url": url,
                "domain": domain,
                "title": "",
                "text": "",
                "error": str(e)
            }

        extracted_text = trafilatura.extract(html_content, include_comments=False, include_tables=False) or ""
        
        soup = BeautifulSoup(html_content, "html.parser")
        title = ""
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
        elif soup.find("h1"):
            title = soup.find("h1").get_text().strip()

        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            title = og_title["content"].strip()
            
        og_desc = soup.find("meta", property="og:description")
        desc = og_desc["content"].strip() if (og_desc and og_desc.get("content")) else ""

        full_content = extracted_text if extracted_text else desc
        if not full_content:
            full_content = title

        return {
            "url": url,
            "domain": domain,
            "title": title,
            "text": full_content,
            "error": None
        }

    @classmethod
    def clean_text(cls, text: str) -> str:
        """Removes social media artifacts, hashtags, excess whitespace, and noisy prefixes."""
        cleaned = text.strip()
        cleaned = re.sub(r"https?://\S+", "", cleaned)
        cleaned = re.sub(r"#\w+", "", cleaned)
        for prefix in CLEANUP_PREFIXES:
            cleaned = re.sub(prefix, "", cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    @classmethod
    def extract_core_claim(cls, text: str) -> str:
        """Extracts the primary checkable claim proposition from raw input."""
        cleaned = cls.clean_text(text)
        if not cleaned:
            return text.strip()

        # If it's a question (e.g. 'is there a recent flash flood near tibet?'), transform to clean assertion
        if cleaned.endswith("?") or re.match(r"^(is|are|was|were|has|did|does|can)\b", cleaned, re.I):
            # Inverted copula question: "Is [subject] [predicate]?" -> "[Subject] is [predicate]"
            copula_match = re.match(
                r"^(is|are|was|were)\s+([a-zA-Z0-9\s\-_]+?)\s+(made\s+of|composed\s+of|consists?\s+of|contains?|a|an|the|part\s+of|caused\s+by|true|false|round|flat)\b(.*)$",
                cleaned,
                re.I
            )
            if copula_match:
                verb, subject, pred_lead, rest = copula_match.groups()
                rest_clean = re.sub(r"\?+$", "", rest).strip()
                transformed = f"{subject} {verb.lower()} {pred_lead} {rest_clean}".strip()
                transformed = re.sub(r"\s+", " ", transformed)
                if transformed:
                    return transformed[0].upper() + transformed[1:]

            # Auxiliary question: "Does [subject] [verb] [rest]?" -> "[Subject] [verb]s [rest]"
            aux_match = re.match(
                r"^does\s+([a-zA-Z0-9\s\-_]+?)\s+(consist\s+of|contain|have|boil|freeze|orbit|rotate)\b(.*)$",
                cleaned,
                re.I
            )
            if aux_match:
                subject, base_verb, rest = aux_match.groups()
                rest_clean = re.sub(r"\?+$", "", rest).strip()
                verb_parts = base_verb.split()
                first_verb = verb_parts[0]
                if not first_verb.endswith("s"):
                    first_verb += "s"
                inflected_verb = " ".join([first_verb] + verb_parts[1:])
                transformed = f"{subject} {inflected_verb} {rest_clean}".strip()
                transformed = re.sub(r"\s+", " ", transformed)
                if transformed:
                    return transformed[0].upper() + transformed[1:]

            transformed = cleaned
            for pat, repl in QUESTION_PATTERNS:
                transformed = re.sub(pat, repl, transformed, flags=re.IGNORECASE).strip()
            if transformed:
                return transformed[0].upper() + transformed[1:]

        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", cleaned) if len(s.strip()) > 10]
        if not sentences:
            return cleaned

        scored_sentences = []
        for s in sentences:
            score = 0
            if re.search(r"\b(confirmed|discovered|announced|passed|banned|caused|cures|killed|signed|voted|proved|secretly|invented|created|flooded|struck|hit)\b", s, re.I):
                score += 3
            if re.search(r"\b(\d+|percent|%|million|billion|trillion|years|dollar|euro)\b", s, re.I):
                score += 2
            capital_words = len(re.findall(r"\b[A-Z][a-z]+\b", s))
            score += min(capital_words, 4)
            if re.search(r"\b(i think|i believe|in my opinion|i feel|maybe|perhaps|probably)\b", s, re.I):
                score -= 3
            scored_sentences.append((score, s))

        scored_sentences.sort(key=lambda x: x[0], reverse=True)
        return scored_sentences[0][1] if scored_sentences else cleaned

    @classmethod
    def extract_all_claims(cls, text: str, max_claims: int = 8) -> List[Dict[str, Any]]:
        """Splits full article or multi-paragraph text into distinct checkable candidate claims."""
        cleaned = text.strip()
        raw_sentences = re.split(r"(?<=[.!?])\s+|\n+", cleaned)
        candidates = []

        seen_claims = set()
        for idx, raw_s in enumerate(raw_sentences):
            s = cls.clean_text(raw_s)
            if len(s) < 20 or len(s) > 280:
                continue
            
            is_checkable = False
            reasons = []

            if re.search(r"\b(claims?|stated|reported|found|proved|revealed|discovered|banned|cured|developed|announced|signed|passed|cost|spent|flooded|struck)\b", s, re.I):
                is_checkable = True
                reasons.append("Contains action/factual assertion verb")

            if re.search(r"\b(\d+%|\$\d+|\d+\s*(million|billion|people|deaths|cases|dollars|miles|years))\b", s, re.I):
                is_checkable = True
                reasons.append("Contains measurable statistic/quantity")

            if re.search(r"\b(NASA|WHO|CDC|FDA|UN|President|Government|Court|Congress|Parliament|Study|Scientists|Researchers|Vaccine|Virus|Ministry)\b", s, re.I):
                is_checkable = True
                reasons.append("Cites prominent institution or subject")

            if re.search(r"^(what|why|how|who|where|when|can|is it|do you)\b", s, re.I):
                continue
            if re.search(r"\b(click here|subscribe|read more|leave a comment|follow us|share this)\b", s, re.I):
                continue

            normalized_key = re.sub(r"[^a-zA-Z0-9]", "", s.lower())[:50]
            if is_checkable and normalized_key not in seen_claims:
                seen_claims.add(normalized_key)
                candidates.append({
                    "claim_index": len(candidates) + 1,
                    "claim_text": s,
                    "context": raw_s,
                    "reasons": reasons
                })
                if len(candidates) >= max_claims:
                    break

        if not candidates and raw_sentences:
            for idx, raw_s in enumerate(raw_sentences[:3]):
                s = cls.clean_text(raw_s)
                if len(s) >= 15:
                    candidates.append({
                        "claim_index": len(candidates) + 1,
                        "claim_text": s,
                        "context": raw_s,
                        "reasons": ["Extracted from article lead"]
                    })

        return candidates
