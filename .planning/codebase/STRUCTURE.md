# TruthLens Codebase Structure & Directory Map

## 1. Complete Repository Layout Tree

```
TruthLens/
├── .env                                  # Root environment variables (Google API keys, etc.)
├── .env.example                          # Example environment configuration template
├── README.md                             # Project overview, setup guide, and feature summary
├── pytest.ini                            # Pytest configuration (test discovery path = backend)
├── run_backend.bat                       # Windows batch script to launch Uvicorn backend server
├── run_frontend.bat                      # Windows batch script to launch Vite frontend dev server
├── start.bat                             # Windows batch script to start both backend & frontend
├── truthlens.db                          # Primary SQLite database file
│
├── .planning/                            # Planning & codebase documentation
│   └── codebase/
│       ├── ARCHITECTURE.md               # End-to-end architecture and pipeline documentation
│       └── STRUCTURE.md                  # Detailed codebase layout and module map (this file)
│
├── backend/                              # Python FastAPI Backend Service
│   ├── .env                              # Local backend environment configuration
│   ├── requirements.txt                  # Python package dependencies
│   ├── truthlens.db                      # Backend SQLite database replica
│   │
│   ├── app/                              # Core application package
│   │   ├── __init__.py                   # Package marker
│   │   ├── main.py                       # FastAPI application factory, lifespan, CORS, routers
│   │   │
│   │   ├── core/                         # Core configurations & settings
│   │   │   ├── __init__.py
│   │   │   └── config.py                 # Pydantic Settings class & environment configuration
│   │   │
│   │   ├── db/                           # Database layer (SQLAlchemy ORM & SQLite)
│   │   │   ├── __init__.py
│   │   │   ├── database.py               # Engine, SessionLocal factory, get_db dependency
│   │   │   ├── models.py                 # SQLAlchemy ORM models (QueryCache, History, etc.)
│   │   │   └── seed_data.py              # 250+ initial publishers, trending claims, initial history
│   │   │
│   │   ├── api/                          # REST API route controllers
│   │   │   ├── __init__.py
│   │   │   ├── routes_verify.py          # /api/verify and /api/verify/article endpoints
│   │   │   ├── routes_credibility.py     # /api/sources and /api/sources/{domain} endpoints
│   │   │   ├── routes_history.py         # /api/history, /api/history/{id}, /api/trending
│   │   │   ├── routes_feedback.py        # /api/feedback and /api/stats endpoints
│   │   │   └── routes_config.py          # /api/config/status and /api/config/set-key endpoints
│   │   │
│   │   └── services/                     # Business logic and verification engines
│   │       ├── __init__.py
│   │       ├── cache_service.py          # RapidFuzz exact & fuzzy cache manager
│   │       ├── credibility_service.py    # Media organization credibility lookup & scoring
│   │       ├── extractor.py              # Claim & URL text extractor, query mode classifier
│   │       ├── factcheck_service.py      # Google Fact Check Tools API & settled facts catalog
│   │       ├── gemini_rate_limiter.py    # Sliding window rate limiter & mutex serialization
│   │       ├── gemini_service.py         # Google GenAI SDK client, RAG prompt, model fallbacks
│   │       ├── google_search_service.py  # Multi-tier web search (Custom Search, DDG, News RSS)
│   │       ├── news_service.py           # Google News RSS parser with semantic relevance scoring
│   │       ├── pattern_analyzer.py       # Linguistic red flags & clickbait pattern analyzer
│   │       ├── stance_service.py         # Stance detector, antonym logic, evidence reranker
│   │       └── synthesis_service.py      # Master verdict synthesizer, 360° incident briefing
│   │
│   └── tests/                            # Automated test suite (Pytest)
│       ├── __init__.py
│       ├── test_credibility.py           # Publisher lookup and scoring tests
│       ├── test_extractor.py             # URL extraction and text cleaning tests
│       ├── test_pattern_analyzer.py      # Linguistic red-flag pattern tests
│       └── test_verification_pipeline.py # 20+ pipeline, rate limiting, and settled knowledge tests
│
├── frontend/                             # React 18 + TypeScript Web Application
│   ├── index.html                        # HTML5 template and entry point
│   ├── package.json                      # NPM dependencies and build scripts
│   ├── package-lock.json                 # Pinned NPM dependency tree
│   ├── postcss.config.js                 # PostCSS configuration (Tailwind & Autoprefixer)
│   ├── tailwind.config.js                # Tailwind CSS styling and theme configuration
│   ├── tsconfig.json                     # TypeScript compiler settings for frontend app
│   ├── tsconfig.node.json                # TypeScript settings for Vite build environment
│   ├── vite.config.ts                    # Vite dev server configuration and backend proxy (/api)
│   │
│   ├── public/                           # Static assets served at root
│   │
│   └── src/                              # Frontend source code
│       ├── main.tsx                      # React root rendering bootstrap
│       ├── App.tsx                       # Primary layout, tab switching, and state coordinator
│       ├── index.css                     # Global styles, Tailwind imports, glassmorphism utilities
│       │
│       ├── api/                          # Typed API client
│       │   └── client.ts                 # Fetch wrapper for all backend REST endpoints
│       │
│       ├── types/                        # TypeScript type definitions
│       │   └── index.ts                  # VerificationResult, SourceEvidence, QuickSummary, etc.
│       │
│       └── components/                   # UI Component Library
│           ├── Navbar.tsx                # Navigation header, backend health beacon, API keys button
│           ├── ClaimInput.tsx            # Multi-mode input bar (text/URL), chips, cache toggle
│           ├── VerdictCard.tsx           # Color-coded verdict banner, 2D verdict tag, actions
│           ├── ConfidenceMeter.tsx       # Radial SVG gauge, certainty percentage, factor pills
│           ├── ExplainabilityPanel.tsx   # Factual breakdown why-bullets & clause-level mapping
│           ├── PatternChecklist.tsx      # Red-flag risk gauge and itemized misinformation checklist
│           ├── QuickSummaryBriefing.tsx  # 360° incident briefing with 8 structured subsections
│           ├── EventBriefingHeader.tsx   # Mode B/C header displaying event category emoji & status
│           ├── EvidenceTrail.tsx         # Cited source cards, canonical 5-tier tags, search metadata
│           ├── ShareableCard.tsx         # Social card modal with high-res PNG export (html-to-image)
│           ├── ArticleMode.tsx           # Multi-paragraph & URL claim extraction and trust scorer
│           ├── TrendingDashboard.tsx     # Viral hoaxes dashboard with category filter & volume tags
│           ├── CredibilityLookup.tsx     # Directory of 250+ publishers with search & bias filters
│           ├── ClaimHistory.tsx          # Local history table with search, category filter, deletion
│           ├── FeedbackModal.tsx         # User feedback dialog (helpful / incorrect submission)
│           └── ApiKeysModal.tsx          # Runtime Google API key configuration modal
│
└── extension/                            # Google Chrome Extension (Manifest V3)
    ├── README.md                         # Extension installation and usage instructions
    ├── manifest.json                     # Chrome Extension Manifest V3 configuration
    ├── background.js                     # Background service worker (context menu & API fetch)
    ├── content.js                        # Injected content script (floating inline badge)
    ├── content.css                       # Styles for injected floating badge
    ├── popup.html                        # Extension toolbar popup UI
    └── popup.js                          # Extension toolbar popup logic & API client
```

---

## 2. Detailed Module Breakdown & Responsibilities

### Root Configuration & Control Files

| File | Purpose | Key Details |
| :--- | :--- | :--- |
| [`.env`](file:///P:/TruthLens/.env) / [`.env.example`](file:///P:/TruthLens/.env.example) | Environment variables | Holds `GOOGLE_API_KEY`, optional overrides (`GOOGLE_FACTCHECK_API_KEY`, `GOOGLE_SEARCH_API_KEY`, `GOOGLE_SEARCH_ENGINE_ID`, `NEWS_API_KEY`), model selection (`GEMINI_MODEL`), and `DATABASE_URL`. |
| [`run_backend.bat`](file:///P:/TruthLens/run_backend.bat) | Backend launcher | Runs `python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000` from `backend/`. |
| [`run_frontend.bat`](file:///P:/TruthLens/run_frontend.bat) | Frontend launcher | Runs `npm.cmd run dev` from `frontend/` on port 5173. |
| [`start.bat`](file:///P:/TruthLens/start.bat) | Complete launcher | Starts both backend and frontend concurrently in separate terminal windows. |
| [`pytest.ini`](file:///P:/TruthLens/pytest.ini) | Test runner config | Configures pytest root `testpaths = backend/tests`. |
| [`truthlens.db`](file:///P:/TruthLens/truthlens.db) | SQLite database | Root database storing cached queries, history, publishers, and feedback. |

---

### Backend Service (`backend/app/`)

#### 1. Core & Configuration (`backend/app/core/`)
- **[`config.py`](file:///P:/TruthLens/backend/app/core/config.py)**:
  - Uses Pydantic's `BaseSettings` to manage environment variables.
  - Automatically aliases `GOOGLE_API_KEY` to `GEMINI_API_KEY`, `GOOGLE_FACTCHECK_API_KEY`, and `GOOGLE_SEARCH_API_KEY` if specific keys are omitted.
  - Exposes rate limiting constants: `GEMINI_MAX_RPM = 15`, `GEMINI_MAX_RETRIES = 2`, `GEMINI_INITIAL_BACKOFF_SEC = 1.5`, `GEMINI_MIN_INTER_CALL_DELAY_SEC = 0.5`.
  - Configures cache TTL (`CACHE_TTL_HOURS = 72`) and fuzzy threshold (`FUZZY_MATCH_THRESHOLD = 85.0`).

#### 2. Database Layer (`backend/app/db/`)
- **[`database.py`](file:///P:/TruthLens/backend/app/db/database.py)**:
  - Initializes SQLAlchemy `engine` with `check_same_thread: False` for SQLite concurrency.
  - Defines `SessionLocal` factory and the `get_db` FastAPI dependency for request-scoped database sessions.
- **[`models.py`](file:///P:/TruthLens/backend/app/db/models.py)**:
  - Defines 5 SQLAlchemy ORM models:
    - `QueryCache`: Stores query hash, normalized query, extracted claim, verdict, confidence, JSON payloads for sources, red flags, explanation, credibility, access count, and expiration date.
    - `ClaimHistory`: Historical log of verified claims with search volume, red-flag scores, and timestamps.
    - `TrendingClaim`: Curated viral claims and debunks displayed in trending dashboard.
    - `PublisherCredibility`: Reference database of media outlets (domain, category, bias, factual reporting, credibility score 0–100, country).
    - `UserFeedback`: Community verdict feedback (helpful / incorrect, suggested verdict, comments).
- **[`seed_data.py`](file:///P:/TruthLens/backend/app/db/seed_data.py)**:
  - Automatically runs during FastAPI startup (`lifespan`).
  - Seeds 250+ publisher profiles across 4 tiers (Top Tier Fact Checkers, High Credibility Mainstream, Known Satire, Known Misinformation/Conspiracy).
  - Seeds 8 verified trending claims spanning science, health, technology, climate, and politics.
  - Populates initial claim history if the database is newly initialized.

#### 3. API Routers (`backend/app/api/`)
- **[`routes_verify.py`](file:///P:/TruthLens/backend/app/api/routes_verify.py)**:
  - `POST /api/verify`: Main endpoint for single claim verification. Implements cache checking, URL extraction, mode detection, settled knowledge checks, fact-check search, live web search, publisher credibility lookup, red-flag analysis, and unified synthesis.
  - `POST /api/verify/article`: Batch endpoint for multi-claim articles. Extracts checkable candidate claims, runs deterministic verification on each, and computes aggregate `Article Trust Score (0–100)`.
- **[`routes_credibility.py`](file:///P:/TruthLens/backend/app/api/routes_credibility.py)**:
  - `GET /api/sources`: Lists and searches publisher credibility database with optional query, category, and bias filters.
  - `GET /api/sources/{domain}`: Looks up specific domain or media outlet details.
- **[`routes_history.py`](file:///P:/TruthLens/backend/app/api/routes_history.py)**:
  - `GET /api/history`: Returns searchable verification history ordered by recency.
  - `DELETE /api/history/{history_id}`: Deletes a specific history record.
  - `GET /api/trending`: Returns viral trending claims along with topic category and verdict distribution statistics.
- **[`routes_feedback.py`](file:///P:/TruthLens/backend/app/api/routes_feedback.py)**:
  - `POST /api/feedback`: Records user satisfaction or corrections on verifications.
  - `GET /api/stats`: Computes aggregate system metrics (total queries, cache entries, cache hits, satisfaction rate, verdict distributions).
- **[`routes_config.py`](file:///P:/TruthLens/backend/app/api/routes_config.py)**:
  - `GET /api/config/status`: Reports active model, presence of API keys, and activated engine capabilities.
  - `POST /api/config/set-key`: Dynamically updates `GOOGLE_API_KEY` at runtime and persists to `.env`.

#### 4. Services Layer (`backend/app/services/`)
- **[`cache_service.py`](file:///P:/TruthLens/backend/app/services/cache_service.py)**:
  - Computes normalized query strings and SHA-256 hashes.
  - Executes exact hash lookups, followed by fuzzy token set similarity (`fuzz.token_set_ratio >= 85.0%`).
  - Serializes and deserializes structured JSON fields (`sources`, `red_flags`, `explanation`, `credibility`).
- **[`credibility_service.py`](file:///P:/TruthLens/backend/app/services/credibility_service.py)**:
  - Extracts clean domains from URLs or raw strings, handling subdomains.
  - Queries `publisher_credibility` table and maps scores into qualitative trust tiers.
  - Grants automatic high trust ($92+$) to official educational (`.edu`, `.ac.uk`) and government (`.gov`, `.mil`, `.gov.uk`, `.gov.in`) domains.
- **[`extractor.py`](file:///P:/TruthLens/backend/app/services/extractor.py)**:
  - `is_url` and `is_time_sensitive`: Detects URL inputs and temporal disaster markers.
  - `detect_query_mode`: Classifies input into Mode A (Claim Verification), Mode B (Event Query), or Mode C (Hybrid).
  - `detect_event_category`: Maps event context to emoji and category label.
  - `normalize_search_query`: Strips question phrasing and stopwords to generate clean search queries.
  - `extract_from_url`: Uses `trafilatura` and `BeautifulSoup` to extract page titles and readable body text.
  - `clean_text` and `extract_core_claim`: Cleans social media artifacts and extracts high-information candidate sentences.
  - `extract_all_claims`: Segments long articles into distinct checkable claims based on action verbs, statistics, and entities.
- **[`factcheck_service.py`](file:///P:/TruthLens/backend/app/services/factcheck_service.py)**:
  - `check_settled_fact`: Matches universal scientific, astronomical, physical, and geographical facts (both positive facts and negative contradictions) with 0 LLM calls.
  - `search_google_fact_check`: Queries Google Fact Check Tools API (`factchecktools.googleapis.com`).
  - `match_offline_database`: Matches local catalog of viral hoaxes and debunks.
  - `normalize_rating`: Normalizes over 40 free-form ratings (e.g., *"pants on fire"*, *"two pinocchios"*, *"debunked"*) into standard verdicts.
- **[`gemini_rate_limiter.py`](file:///P:/TruthLens/backend/app/services/gemini_rate_limiter.py)**:
  - Manages in-memory sliding window deque to restrict calls below 15 RPM.
  - Serializes concurrent calls with `asyncio.Lock`.
  - Enforces minimum 500 ms inter-call delay spacing.
  - Implements exponential backoff for HTTP 429 and 503 errors.
  - Fails fast on HTTP 401 (Auth) and 404 (Model Not Found) without retries.
- **[`gemini_service.py`](file:///P:/TruthLens/backend/app/services/gemini_service.py)**:
  - Integrates `google-genai` SDK with candidate model fallback (`gemini-3.1-flash-live-preview`, `gemini-3-flash-preview`, etc.).
  - Executes RAG synthesis with structured system instructions, few-shot examples, and strict JSON output formatting.
  - Extracts and parses Google Search Grounding metadata and web citations.
  - Performs robust markdown stripping and regex JSON fallback parsing.
- **[`google_search_service.py`](file:///P:/TruthLens/backend/app/services/google_search_service.py)**:
  - Executes multi-tier web searches: Google Custom Search JSON API $\rightarrow$ DuckDuckGo HTML scraping $\rightarrow$ Google News RSS search.
  - Extracts titles, URLs, and snippets, calculating semantic relevance to the claim.
- **[`news_service.py`](file:///P:/TruthLens/backend/app/services/news_service.py)**:
  - Queries Google News RSS feeds with search query terms.
  - Computes combined semantic relevance using token intersection ratios and RapidFuzz scoring.
  - Classifies news headlines as Debunking, Confirming, or General Reporting.
- **[`pattern_analyzer.py`](file:///P:/TruthLens/backend/app/services/pattern_analyzer.py)**:
  - Evaluates linguistic patterns across 6 categories: Clickbait, Emotional Manipulation, Vague Attribution, Conspiracy Tropes, Extreme Statistics, and Stylistic Shouting.
  - Produces itemized flags with severity, impact points, and qualitative risk tiers.
- **[`stance_service.py`](file:///P:/TruthLens/backend/app/services/stance_service.py)**:
  - `ClaimClassifier`: Categorizes claims into `SETTLED_FACT`, `CURRENT_EVENT`, `OPINION`, or `CONTESTED`.
  - `StanceDetector`: Evaluates document stance (`ENTAILS`, `CONTRADICTS`, `NEUTRAL`) using antonym rules, numeric conflict detection, and keyword triggers.
  - `EvidenceReranker`: Weights relevance ($40\%$), publisher credibility ($30\%$), and stance confidence ($30\%$), giving priority bonuses to decisive evidence.
- **[`synthesis_service.py`](file:///P:/TruthLens/backend/app/services/synthesis_service.py)**:
  - Master orchestrator combining evidence, red flags, publisher scores, and settled facts.
  - Enforces the single Gemini call budget rule.
  - Generates the 360° incident briefing (`quick_summary`) across 8 subsections.
  - Implements the Consistency Guard Rail (`apply_consistency_guard_rail`) to override verdicts if any clause is debunked.
  - Categorizes all citations into the 5 canonical source tiers.

---

### Frontend Application (`frontend/src/`)

#### 1. Entry & Global State
- **[`main.tsx`](file:///P:/TruthLens/frontend/src/main.tsx)**: Mounts React DOM tree into `#root`.
- **[`App.tsx`](file:///P:/TruthLens/frontend/src/App.tsx)**:
  - Coordinates global view state (`activeTab`: `'verify' | 'article' | 'trending' | 'sources' | 'history'`).
  - Manages primary verification result state (`verificationResult: VerificationResult | null`).
  - Handles backend health polling loop (every 30 seconds via `/health`).
  - Controls modal visibility (`ShareableCard`, `FeedbackModal`, `ApiKeysModal`).
- **[`index.css`](file:///P:/TruthLens/frontend/src/index.css)**: Tailwind directives, custom glassmorphism styles (`.glass-panel`), and custom scrollbars.

#### 2. API Client & Types
- **[`api/client.ts`](file:///P:/TruthLens/frontend/src/api/client.ts)**:
  - Typed Fetch API wrapper for all backend endpoints.
  - Handles query parameters, JSON serialization, and structured error propagation.
- **[`types/index.ts`](file:///P:/TruthLens/frontend/src/types/index.ts)**:
  - Data contracts: `VerdictType`, `PublisherCredibility`, `EventMeta`, `ImpactNumbers`, `QuickSummary`, `SourceEvidence`, `RedFlagItem`, `MisinformationAnalysis`, `ClaimClauseBreakdown`, `ExplainabilityData`, `VerificationResult`, `ArticleAnalysisResult`, `TrendingClaimItem`, `HistoryItem`, `SystemStats`.

#### 3. UI Components (`frontend/src/components/`)
- **[`Navbar.tsx`](file:///P:/TruthLens/frontend/src/components/Navbar.tsx)**: Branded navigation bar, online/offline backend status beacon, navigation tabs, and Google API Key modal button.
- **[`ClaimInput.tsx`](file:///P:/TruthLens/frontend/src/components/ClaimInput.tsx)**: Primary search input bar with URL auto-detection, bypass cache toggle, and one-click sample query chips.
- **[`VerdictCard.tsx`](file:///P:/TruthLens/frontend/src/components/VerdictCard.tsx)**: Color-coded verdict banner with two-dimensional verdict displays, category pill, copy link, and modal triggers.
- **[`ConfidenceMeter.tsx`](file:///P:/TruthLens/frontend/src/components/ConfidenceMeter.tsx)**: Animated radial SVG gauge displaying confidence percentage and itemized contributing factor pills.
- **[`ExplainabilityPanel.tsx`](file:///P:/TruthLens/frontend/src/components/ExplainabilityPanel.tsx)**: Key factual breakdown bullets and interactive Clause-by-Clause Assertion Mapping cards.
- **[`PatternChecklist.tsx`](file:///P:/TruthLens/frontend/src/components/PatternChecklist.tsx)**: Red-flag score meter, qualitative risk level, and itemized checklist of detected linguistic triggers.
- **[`QuickSummaryBriefing.tsx`](file:///P:/TruthLens/frontend/src/components/QuickSummaryBriefing.tsx)**: 360° incident briefing displaying What Happened, Context, Timeline, Impact Numbers, Key Parties, Data Points, Perspectives, and Key Takeaways.
- **[`EventBriefingHeader.tsx`](file:///P:/TruthLens/frontend/src/components/EventBriefingHeader.tsx)**: Mode B and Mode C banner showing event category emoji, region, date range, and developing status badge.
- **[`EvidenceTrail.tsx`](file:///P:/TruthLens/frontend/src/components/EvidenceTrail.tsx)**: Ranked evidence cards with 5-tier source badges, fact-checker verdicts, stances, publication dates, and search execution metadata.
- **[`ShareableCard.tsx`](file:///P:/TruthLens/frontend/src/components/ShareableCard.tsx)**: Generates and exports high-resolution, branded PNG verdict cards using `html-to-image` for social sharing.
- **[`ArticleMode.tsx`](file:///P:/TruthLens/frontend/src/components/ArticleMode.tsx)**: Multi-paragraph and URL analyzer that extracts claims, verifies each, calculates overall trust score, and renders an interactive claim accordion.
- **[`TrendingDashboard.tsx`](file:///P:/TruthLens/frontend/src/components/TrendingDashboard.tsx)**: Viral claims monitoring dashboard with search volume indicators and category filters.
- **[`CredibilityLookup.tsx`](file:///P:/TruthLens/frontend/src/components/CredibilityLookup.tsx)**: Searchable directory of 250+ media organizations with trust scores, factual ratings, and bias classifications.
- **[`ClaimHistory.tsx`](file:///P:/TruthLens/frontend/src/components/ClaimHistory.tsx)**: Local verification history log with search, verdict filters, and deletion controls.
- **[`FeedbackModal.tsx`](file:///P:/TruthLens/frontend/src/components/FeedbackModal.tsx)**: Dialog allowing users to mark verifications as helpful or incorrect and submit corrections.
- **[`ApiKeysModal.tsx`](file:///P:/TruthLens/frontend/src/components/ApiKeysModal.tsx)**: In-app modal to input and activate Google API keys at runtime.

---

### Chrome Extension (`extension/`)

| File | Purpose | Key Details |
| :--- | :--- | :--- |
| [`manifest.json`](file:///P:/TruthLens/extension/manifest.json) | Extension Manifest | Manifest V3 specification; declares permissions (`contextMenus`, `activeTab`, `storage`), host permissions for localhost:8000, and specifies background service worker and content scripts. |
| [`background.js`](file:///P:/TruthLens/extension/background.js) | Service Worker | Creates `"Verify with TruthLens"` context menu on text selection; receives selection clicks, communicates with content script, and executes asynchronous verification requests to `http://localhost:8000/api/verify`. |
| [`content.js`](file:///P:/TruthLens/extension/content.js) | Injected Content Script | Listens for messages from `background.js`; dynamically creates and injects a floating card overlay (`#truthlens-injected-overlay`) on the host webpage displaying verdict, confidence, and summary. |
| [`content.css`](file:///P:/TruthLens/extension/content.css) | Overlay Stylesheet | Isolated floating card styling with dark theme, responsive badges, and close button. |
| [`popup.html`](file:///P:/TruthLens/extension/popup.html) | Extension Toolbar Popup | HTML UI for quick claim verification directly from the browser action icon. |
| [`popup.js`](file:///P:/TruthLens/extension/popup.js) | Toolbar Popup Controller | Reads user input, calls backend API, and renders formatted verdict cards within the popup window. |
| [`README.md`](file:///P:/TruthLens/extension/README.md) | Extension Documentation | Guide for loading the unpacked extension in Google Chrome (`chrome://extensions`). |

---

## 3. Entrypoints & Initialization Cycles

```
                                  INITIALIZATION SEQUENCES
                                  
  FastAPI Backend (run_backend.bat)         React Frontend (run_frontend.bat)
  ─────────────────────────────────         ─────────────────────────────────
  1. Load Settings (config.py)              1. Vite loads index.html
  2. Create SQLite tables (Base.metadata)   2. main.tsx mounts App.tsx
  3. Run lifespan (seed_database)           3. App.tsx initiates checkHealth()
     - Seed 250+ publishers                 4. Health check pings GET /health
     - Seed 8 trending claims               5. Renders activeTab ('verify')
     - Seed initial claim history           6. Sets 30s recurring health timer
  4. Mount CORS & API Routers
  5. Listen on 127.0.0.1:8000
```

---

## 4. State Management Across Modules

### Backend State
- **Session Scoping**: SQLAlchemy database sessions are created per request via `Depends(get_db)` and automatically closed on response completion.
- **In-Memory Rate Limiter**: Shared sliding window deque (`_timestamps`) and mutex (`_lock`) live in `GeminiRateLimiter` class state.
- **Runtime Configuration**: API keys can be dynamically set via `POST /api/config/set-key`, mutating `settings` in memory and persisting to the `.env` file on disk.

### Frontend State
- **Primary Screen State**: Managed via React `useState` hooks in [`App.tsx`](file:///P:/TruthLens/frontend/src/App.tsx#L21-L32) (`activeTab`, `verificationResult`, `isLoading`, `error`).
- **Tab Selection**: Stateless URL routing; active tab state drives conditional rendering of tab views (`verify`, `article`, `trending`, `sources`, `history`).
- **Modal State**: Managed via boolean states (`showShareModal`, `showFeedbackModal`, `showApiKeysModal`).
- **Component Local State**: Form inputs, accordion open/close indices, and copied clipboard states are encapsulated within individual components.

### Chrome Extension State
- **Background Worker**: Ephemeral event-driven service worker in Manifest V3. State is passed via Chrome message passing (`chrome.tabs.sendMessage`).
- **DOM Injection**: Directly manages lifecycle of `#truthlens-injected-overlay` in the DOM tree of whatever web page the user is viewing.

---

## 5. Build, Test, and Execution Commands

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm

### Backend Commands
```bash
# Navigate to backend directory
cd P:\TruthLens\backend

# Install dependencies
python -m pip install -r requirements.txt

# Run FastAPI server with auto-reload
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Run complete automated test suite
python -m pytest
```

### Frontend Commands
```bash
# Navigate to frontend directory
cd P:\TruthLens\frontend

# Install dependencies
npm.cmd install

# Start Vite development server
npm.cmd run dev

# Build production bundle
npm.cmd run build
```

### Running the Chrome Extension
1. Open Google Chrome and navigate to `chrome://extensions/`.
2. Enable **Developer mode** toggle in the top-right corner.
3. Click **Load unpacked**.
4. Select `P:\TruthLens\extension`.
