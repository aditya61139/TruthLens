# TruthLens Architecture Documentation

## 1. System Overview

TruthLens is an AI-powered fake news detection and claim verification system engineered for high accuracy, low latency, and zero-cost operation out of the box. The system verifies factual assertions, analyzes multi-paragraph articles, inspects viral rumors, and provides incident briefings for breaking events.

### Core Architectural Principles

1. **Multi-Tiered Verification Hierarchy**: Queries resolve at the earliest authoritative tier without incurring unnecessary external network calls or upstream API costs:
   - *Tier 0*: RapidFuzz SQLite Cache ($<5\text{ ms}$, exact SHA-256 or $\ge 85\%$ token similarity).
   - *Tier 1*: Settled Knowledge & Contradiction Tier ($<15\text{ ms}$, deterministic catalog of fundamental scientific, astronomical, physical, and geographic principles; 0 LLM calls).
   - *Tier 2*: Accredited Fact-Check Retrieval (Google Fact Check Tools API + curated local repository).
   - *Tier 3*: Live Open Web Search Grounding (Google Custom Search API, DuckDuckGo HTML scraping, Google News RSS).
   - *Tier 4*: RAG Stance Synthesis (At most ONE Google Gemini call, protected by client-side sliding window rate limiting).
2. **Deterministic Fallbacks (Zero-Cost Default)**: When Google API keys are not provided or quotas are exceeded, TruthLens seamlessly falls back to rule-based stance classification, local NLP red-flag heuristics, and publisher credibility index weighting without crashing.
3. **Two-Dimensional Verdict Architecture**: Claims are evaluated along two orthogonal dimensions:
   - **Claim Truth Value**: `True`, `False`, `Likely True`, `Likely False`, `Misleading`, `Satire`, `Unverifiable`.
   - **Knowledge Certainty**: `Settled Knowledge`, `Under Active Debate`, `Emerging / Current Event`, `Insufficient Evidence`.
4. **Tri-Mode Ingestion Engine**:
   - **Mode A (Claim Verification)**: Direct declarative assertion to fact-check.
   - **Mode B (Event Query)**: Open-ended question regarding an ongoing disaster or current event.
   - **Mode C (Hybrid)**: Specific quantitative or causal assertion tied to an active event.
5. **Clause-Level Consistency Guard Rail**: Prevents high-level LLM hallucinations; if any individual clause is debunked, the compound verdict is strictly forbidden from evaluating as `True`.

```
                      ┌────────────────────────────────────────┐
                      │             User Ingestion             │
                      │  Web Dashboard / Extension / Article   │
                      └───────────────────┬────────────────────┘
                                          │
                                          ▼
                      ┌────────────────────────────────────────┐
                      │     Input Extraction & Mode Det.       │
                      │   (ClaimExtractor: Mode A / B / C)     │
                      └───────────────────┬────────────────────┘
                                          │
                                          ▼
                      ┌────────────────────────────────────────┐
                      │    Cache Lookup (Exact SHA + Fuzzy)    │
                      │         (QueryCache - SQLite)          │
                      └───────┬────────────────────────┬───────┘
                     HIT (<5ms)│                        │ MISS
                              ▼                        ▼
                      ┌───────────────┐        ┌────────────────────────────────────────┐
                      │ Cached Result │        │ Settled Knowledge / Contradiction Tier │
                      └───────────────┘        │      (Settled Fact / Falsehood)        │
                                               └───────┬────────────────────────┬───────┘
                                              MATCH    │                        │ NO MATCH
                                                       ▼                        ▼
                                               ┌───────────────┐        ┌────────────────────────────────────────┐
                                               │ Settled Fact  │        │ Multi-Source Fact Check & Web Search   │
                                               │ (0 LLM Calls) │        │ (Google Fact Check, DDG, News RSS)     │
                                               └───────────────┘        └───────────────────┬────────────────────┘
                                                                                            │
                                                                                            ▼
                                                                                ┌────────────────────────────────────────┐
                                                                                │ NLP Pattern & Publisher Credibility    │
                                                                                │ (Red Flags + 250+ Media Outlets DB)    │
                                                                                └───────────────────┬────────────────────┘
                                                                                            │
                                                                                            ▼
                                                                                ┌────────────────────────────────────────┐
                                                                                │ Stance Detection & Evidence Reranking  │
                                                                                │ (Antonyms, Entails, Contradicts)       │
                                                                                └───────────────────┬────────────────────┘
                                                                                            │
                                                                                            ▼
                                                                                ┌────────────────────────────────────────┐
                                                                                │ Unified RAG Synthesis & Guard Rail     │
                                                                                │ (Gemini 3 Flash Live or Local Fallback)│
                                                                                └───────────────────┬────────────────────┘
                                                                                            │
                                                                                            ▼
                                                                                ┌────────────────────────────────────────┐
                                                                                │ Confidence Meter & 360° Incident Brief │
                                                                                │ (Save Cache, Log History, Return JSON) │
                                                                                └────────────────────────────────────────┘
```

---

## 2. End-to-End Verification Pipeline (Data Flow)

### Step 1: Claim Ingestion & Extraction
- **Input Types**: Raw text, URL, conversational query, or full article text.
- **Component**: [`ClaimExtractor`](file:///P:/TruthLens/backend/app/services/extractor.py#L36-L322)
- **Processing Steps**:
  1. Detects if input is a URL. If so, fetches the webpage using `httpx` and extracts body content using `trafilatura` and `BeautifulSoup`.
  2. Cleans text by stripping social media noise, hashtags, and viral forward banners (`r"^(breaking news|alert|urgent|did you know that)..."`).
  3. Classifies query mode via `detect_query_mode`:
     - **Mode A (Claim Verification)**: Declarative statements (`"Water boils at 100C"`).
     - **Mode B (Event Query)**: Inquiries regarding current occurrences (`"Is there a recent flash flood in India?"`).
     - **Mode C (Hybrid)**: Specific assertions combined with ongoing situations (`"500 people died in the Assam floods"`).
  4. Identifies event categories (`detect_event_category`) with emoji tags (e.g., 🌊 Natural Disaster — Flooding, 🌍 Geopolitics — Armed Conflict, 🏛️ Politics — Governance).
  5. Normalizes query into clean search tokens via `normalize_search_query` by removing question words and stopwords for search indexing.

### Step 2: Cache Lookup (Exact & Fuzzy Deduplication)
- **Component**: [`CacheService`](file:///P:/TruthLens/backend/app/services/cache_service.py#L11-L148)
- **Mechanism**:
  1. Computes normalized text (lowercase, alphanumeric only) and generates a SHA-256 hash.
  2. Queries `query_cache` table for active (non-expired, TTL 72 hours) exact hash matches.
  3. If no exact match, iterates through active cache entries using `rapidfuzz.fuzz.token_set_ratio`. If similarity $\ge 85.0\%$, returns the cached verification immediately with `cached: true` and `is_fuzzy_match: true`.
  4. Increments `access_count` on hit.

### Step 3: Settled Knowledge & Contradiction Tier
- **Component**: [`FactCheckService.check_settled_fact`](file:///P:/TruthLens/backend/app/services/factcheck_service.py#L358-L440)
- **Characteristics**:
  - Resolves universally known scientific, geographical, and astronomical facts with **0 Gemini API calls** and $<15\text{ ms}$ execution time.
  - Matches positive settled facts (e.g., *"earth orbits the sun"*, *"water freezes at 0C"*, *"Paris is capital of France"*) $\rightarrow$ Returns `True` with $98\%$ confidence.
  - Matches direct contradictions (e.g., *"sun rises in the west"*, *"earth is flat"*, *"water boils at 50C"*) $\rightarrow$ Returns `False` with $97\%$ confidence.
  - Automatically attaches curated educational and primary references (NASA, NIST, NOAA, Stanford Solar Center, Encyclopedia Britannica, NIH).

### Step 4: Multi-Source Evidence Retrieval
- **Components**: [`FactCheckService`](file:///P:/TruthLens/backend/app/services/factcheck_service.py#L546-L564), [`GoogleSearchService`](file:///P:/TruthLens/backend/app/services/google_search_service.py#L14-L88), [`NewsCrossReferenceService`](file:///P:/TruthLens/backend/app/services/news_service.py#L22-L138).
- **Execution Order**:
  1. If claim is time-sensitive / breaking: executes live web search first, then checks fact-check repositories.
  2. If general claim: queries Google Fact Check Tools API (`claims:search`) and offline curated database (`OFFLINE_FACT_CHECKS`).
  3. Web Search Fallback Tiering:
     - Tier A: Google Custom Search JSON API (if `GOOGLE_SEARCH_ENGINE_ID` configured).
     - Tier B: Open Web Index via DuckDuckGo HTML parser.
     - Tier C: Google News RSS Search.
  4. **Strict Semantic Relevance Filtering**: News articles and web results must pass `NewsCrossReferenceService.calculate_relevance` (minimum threshold $55.0\%$) using token overlap ratios and RapidFuzz scoring. Irrelevant keyword padding is eliminated.

### Step 5: Publisher Credibility Weighting
- **Component**: [`PublisherCredibilityService`](file:///P:/TruthLens/backend/app/services/credibility_service.py#L7-L103)
- **Data Source**: SQLite table `publisher_credibility` seeded with 250+ media outlets.
- **Enrichment**:
  - Extracts domain from URLs or textual source citations.
  - Matches domains, subdomains, and organizational aliases.
  - Assigns credibility score (0–100), trust tier (e.g., *Top-Tier Credible*, *Mainstream*, *Conspiracy/Fake*), factual reporting rating (*Very High*, *High*, *Mixed*, *Low*), and media bias rating (*Center*, *Lean Left*, *Right*, *Extreme*).
  - Official educational (`.edu`) and government (`.gov`, `.gov.uk`, `.gov.in`) domains receive automatic $92+$ credibility.

### Step 6: Misinformation Pattern & Red Flag NLP
- **Component**: [`MisinformationPatternAnalyzer`](file:///P:/TruthLens/backend/app/services/pattern_analyzer.py#L37-L179)
- **Evaluated Dimensions**:
  1. *ALL CAPS Ratio*: Detects shouting/alarmism (caps ratio $>30\%$).
  2. *Excessive Punctuation*: Multiple exclamation and question marks (`!!!`, `???`).
  3. *Clickbait Phrasing*: Curiosity gap hooks (*"you won't believe"*, *"miracle cure"*).
  4. *Emotional Manipulation*: Fearmongering and inflammatory language (*"bloodbath"*, *"catastrophic"*).
  5. *Unverified Attribution*: Vague consensus framing (*"scientists say"*, *"experts confirm"* without named institutional affiliation).
  6. *Conspiracy Tropes*: Pseudoscience cues (*"deep state"*, *"big pharma is hiding"*, *"false flag"*).
  7. *Dubious Statistics*: Extreme unreferenced statistical metrics (*"1000% increase"*, *"millions dead secretly"*).
- Produces normalized `red_flag_score` (0–100), risk level, and an itemized boolean checklist.

### Step 7: Stance Classification & Evidence Reranking
- **Component**: [`ClaimClassifier`](file:///P:/TruthLens/backend/app/services/stance_service.py#L64-L98), [`StanceDetector`](file:///P:/TruthLens/backend/app/services/stance_service.py#L100-L186), [`EvidenceReranker`](file:///P:/TruthLens/backend/app/services/stance_service.py#L188-L245)
- **Execution**:
  - `ClaimClassifier`: Rule-based classification into `SETTLED_FACT`, `CURRENT_EVENT`, `OPINION`, or `CONTESTED`.
  - `StanceDetector`: Evaluates document titles and snippets against claim text:
    - Debunk keywords (`debunked`, `hoax`, `false`, `bogus`) $\rightarrow$ `CONTRADICTS`.
    - Directional / antonym logic (`east` vs `west`, `cure` vs `ineffective`, `flat` vs `round`) $\rightarrow$ `CONTRADICTS` ($95\%$ confidence).
    - Numeric conflicts (divergent metrics on identical subject) $\rightarrow$ `CONTRADICTS`.
    - Corroborating signals (`confirms`, `verified`, high semantic overlap) $\rightarrow$ `ENTAILS`.
    - Neutral reporting $\rightarrow$ `NEUTRAL`.
  - `EvidenceReranker`: Calculates ranking score:
    $$\text{Rank Score} = (\text{Relevance} \times 0.4) + (\text{Credibility} \times 0.3) + (\text{Stance Confidence} \times 0.3) + \text{Stance Bonus}$$
    Prioritizes decisive documents (`ENTAILS` / `CONTRADICTS`) over neutral mentions.

### Step 8: Unified Synthesis & Explainability Engine
- **Component**: [`SynthesisService`](file:///P:/TruthLens/backend/app/services/synthesis_service.py#L354-L819), [`GeminiSynthesisService`](file:///P:/TruthLens/backend/app/services/gemini_service.py#L183-L437)
- **Single-Call Gemini Budget**:
  - Guarantees **at most 1 Gemini API call** per user request to conserve API quotas and minimize latency.
  - Protected by [`GeminiRateLimiter`](file:///P:/TruthLens/backend/app/services/gemini_rate_limiter.py#L31-L155):
    - Sliding-window enforcement (15 RPM free-tier safe ceiling).
    - Asynchronous mutex lock (`asyncio.Lock`) preventing race conditions.
    - Minimum 500 ms inter-call delay spacing.
    - Fast-fail on HTTP 401 (Auth) and HTTP 404 (Model Not Found) without wasteful retry loops.
    - Exponential backoff for HTTP 429 and transient HTTP 503 errors.
- **Consistency Guard Rail (`apply_consistency_guard_rail`)**:
  - Inspects clause-by-clause assertion mapping and retrieved evidence stances.
  - If any clause is marked `debunked` or any authoritative evidence marks `CONTRADICTS`, the truth value cannot be `True`. Overrides to `False` or `Misleading`.
- **360° Incident Briefing (`quick_summary`)**:
  - Generates comprehensive eight-factor journalistic briefing:
    1. *What Happened* (Core event summary)
    2. *Full Context & Background* (Structural/historical context)
    3. *Timeline of Key Events* (Chronological sequence)
    4. *Impact & Key Numbers* (Structured dictionary: deaths, displaced, areas affected, damage, rescue operations)
    5. *Key Parties & Roles* (Involved agencies and authorities)
    6. *Key Data Points* (Quantitative metrics)
    7. *Perspectives* (Official positions and stakeholder stances)
    8. *Current Status & Key Takeaway* (Bottom-line verdict)
- **Canonical 5-Tier Source Classification**:
  - `[🟢 Primary Source]` (Government registries, scientific publications, WHO, NASA, legal statutes)
  - `[🔵 Major News Outlet]` (Reuters, AP News, BBC, NYT, Washington Post)
  - `[🟡 Fact-Checker]` (Snopes, PolitiFact, FactCheck.org, AFP Fact Check)
  - `[🟠 Domain Expert / Academic]` (Universities, scientific journals, Britannica)
  - `[⚪ Other / General]` (General websites, Wikipedia)

### Step 9: Multi-Factor Confidence Meter
- Confidence is calculated from source evidence authority, stance consensus, and red-flag penalties:
  - Strong corroboration from primary/fact-check sources: $85\text{--}99\%$.
  - Solely local stance consensus / news coverage: $65\text{--}85\%$.
  - High linguistic red-flag score ($\ge 70$): caps confidence or degrades score.
  - Unverified assertions with no primary documentation: strictly bounded at $\le 45\%$.

### Step 10: Persistence & Response
- Successful syntheses are persisted to `query_cache` (with TTL) and `claim_history`.
- In Article Mode, deterministic synthesis is enforced (`allow_gemini_call=False`) to avoid quota exhaustion when evaluating batches of claims, calculating an aggregate **Article Trust Score (0–100)**.

---

## 3. Technology Stack & Key Dependencies

```
┌────────────────────────────────────────────────────────────────────────┐
│                               TruthLens                                │
├─────────────────────────┬────────────────────────┬─────────────────────┤
│      Backend API        │     Web Dashboard      │  Chrome Extension   │
├─────────────────────────┼────────────────────────┼─────────────────────┤
│ • FastAPI (v0.110+)     │ • React 18.2           │ • Manifest V3       │
│ • Uvicorn               │ • TypeScript 5.2       │ • Background Worker │
│ • SQLAlchemy 2.0        │ • Vite 5.1             │ • Content Scripts   │
│ • SQLite3               │ • Tailwind CSS 3.4     │ • Injected Overlay  │
│ • Pydantic v2           │ • Lucide React         │ • Browser Action UI │
│ • RapidFuzz 3.6         │ • html-to-image        │                     │
│ • Google GenAI SDK      │ • Vite Proxy           │                     │
│ • Trafilatura & BS4     │                        │                     │
│ • HTTPX (Async HTTP)    │                        │                     │
└─────────────────────────┴────────────────────────┴─────────────────────┘
```

---

## 4. Component Architecture & Interactions

### Backend Component Diagram

```
FastAPI Router Entrypoints
 ├── routes_verify.py ───────► ClaimExtractor (trafilatura, bs4)
 │                            ├── CacheService (rapidfuzz, SQLite)
 │                            ├── FactCheckService (Google Fact Check API)
 │                            ├── GoogleSearchService (DuckDuckGo, Custom Search)
 │                            ├── NewsCrossReferenceService (News RSS, rapidfuzz)
 │                            ├── PublisherCredibilityService (SQLite 250+ records)
 │                            ├── MisinformationPatternAnalyzer (Regex Lexicons)
 │                            ├── StanceDetector & EvidenceReranker
 │                            └── SynthesisService
 │                                 ├── GeminiSynthesisService (google-genai)
 │                                 │    └── GeminiRateLimiter (15 RPM, mutex)
 │                                 └── Consistency Guard Rail
 ├── routes_credibility.py ──► PublisherCredibilityService
 ├── routes_history.py ──────► SQLite ClaimHistory & TrendingClaim models
 ├── routes_feedback.py ─────► SQLite UserFeedback & SystemStats calculations
 └── routes_config.py ───────► Runtime Settings & .env persistence
```

### Frontend Component Hierarchy

```
App.tsx (Root Controller, activeTab router, health check loop, modal toggles)
 ├── Navbar.tsx (Status beacon, tab navigation, API key trigger)
 ├── Verification Tab (activeTab === 'verify')
 │    ├── ClaimInput.tsx (Search input, URL extract toggle, example chips, cache bypass)
 │    ├── EventBriefingHeader.tsx (Shown for Mode B Event Queries & Mode C Hybrids)
 │    ├── VerdictCard.tsx (Theme gradient, truth value banner, certainty tag, actions)
 │    │    └── ConfidenceMeter.tsx (Radial SVG gauge, contributing factors)
 │    ├── ExplainabilityPanel.tsx (Why bullets, clause-by-clause mapping)
 │    ├── PatternChecklist.tsx (Red-flag score, risk badge, itemized breakdown)
 │    ├── QuickSummaryBriefing.tsx (8-section 360° incident briefing)
 │    └── EvidenceTrail.tsx (Ranked source cards, 5-tier tags, search metadata)
 ├── ArticleMode.tsx (Multi-claim extraction, overall trust score, claim accordion)
 ├── TrendingDashboard.tsx (Monitored viral hoaxes, category filters, search volume)
 ├── CredibilityLookup.tsx (250+ media organization directory, search, tier filters)
 ├── ClaimHistory.tsx (Searchable SQLite history, detail drawer, entry deletion)
 └── Modals
      ├── ShareableCard.tsx (High-res branded PNG verdict export via html-to-image)
      ├── FeedbackModal.tsx (Helpful / Incorrect feedback submission)
      └── ApiKeysModal.tsx (Runtime Google API Key entry and activation)
```

### Chrome Extension (Manifest V3) Architecture

1. **Manifest (`manifest.json`)**:
   - `permissions`: `contextMenus`, `activeTab`, `storage`.
   - `host_permissions`: `http://localhost:8000/*`, `http://127.0.0.1:8000/*`.
   - `background`: `"service_worker": "background.js"`.
   - `content_scripts`: Matches all URLs, injecting `content.js` and `content.css`.
   - `action`: Browser toolbar popup with `popup.html`.
2. **Execution Flow**:
   - User selects text on any webpage $\rightarrow$ Right-clicks $\rightarrow$ Selects *"Verify with TruthLens"*.
   - Service worker [`background.js`](file:///P:/TruthLens/extension/background.js#L9-L46) receives context menu event.
   - `background.js` posts message `TRUTHLENS_LOADING` to active tab content script.
   - `background.js` issues asynchronous POST request to `http://localhost:8000/api/verify`.
   - On response, sends `TRUTHLENS_RESULT` or `TRUTHLENS_ERROR` to tab.
   - Content script [`content.js`](file:///P:/TruthLens/extension/content.js#L38-L68) injects or updates a floating DOM overlay `#truthlens-injected-overlay` presenting verdict badge, confidence score, summary, and direct link back to dashboard.

---

## 5. Architectural Quality Attributes

| Quality Attribute | Architectural Strategy |
| :--- | :--- |
| **Availability & Fault Tolerance** | Deterministic local fallback pipeline operates without API keys or when upstream LLM APIs fail. 401/404 errors fail fast without blocking the event loop. |
| **Latency & Performance** | Cache lookups resolve in $<5\text{ ms}$. Settled facts resolve in $<15\text{ ms}$. Only ONE LLM call is ever made per verification. Long evidence texts are truncated before prompt construction. |
| **Extensibility** | Modular services with clean single responsibilities (`extractor`, `pattern_analyzer`, `factcheck`, `google_search`, `news`, `stance`, `synthesis`). SQLite database seeded via standard ORM migrations/scripts. |
| **Accuracy & Guard Rails** | Clause-level consistency check prevents compound claim hallucination. Directional antonym detection identifies inverted scientific assertions. |
| **Usability & Explainability** | Transparent evidence trail with clickable URLs, 360° incident briefing, clause-by-clause mapping, and shareable social media verdict cards. |
