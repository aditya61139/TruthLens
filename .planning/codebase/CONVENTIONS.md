# TruthLens Codebase Conventions & Standards

This document establishes the architecture patterns, coding standards, language idioms, and structural conventions observed across the TruthLens repository (`P:\TruthLens`). It serves as the authoritative guide for maintaining consistency, type safety, and architectural integrity across backend, frontend, extension, and configuration layers.

---

## 1. Architectural Overview & System Topology

TruthLens is organized as a multi-tier fact-checking and incident verification platform composed of three primary subsystems:

1. **Backend (`backend/app/`)**: High-performance FastAPI application built with Python 3.10+ featuring multi-source RAG synthesis, rule-based NLP claim classification, SQLite caching with fuzzy matching (`rapidfuzz`), and a rate-limited integration with Google Gemini 3 Flash Live.
2. **Frontend (`frontend/src/`)**: Modern Single-Page Application (SPA) built with React 18, TypeScript, Vite, and Tailwind CSS, utilizing glassmorphic dark-mode UI, radial SVG confidence meters, and interactive 360° incident briefing panels.
3. **Browser Extension (`extension/`)**: Manifest V3 Chrome extension providing in-page context menu claim verification and popup dashboard access communicating with the local FastAPI backend.

```
P:\TruthLens\
├── backend\
│   ├── app\
│   │   ├── api\               # Route handlers (verify, credibility, history, feedback, config)
│   │   ├── core\              # Application settings & environment configuration
│   │   ├── db\                # SQLAlchemy engine, declarative models, and database seeders
│   │   ├── services\          # Business logic, NLP analyzers, RAG synthesis, rate limiting
│   │   └── main.py            # FastAPI application factory, lifespan, CORS, and routing
│   ├── tests\                 # Pytest test suite (fixtures, unit, and end-to-end pipeline tests)
│   └── requirements.txt       # Python dependencies
├── frontend\
│   ├── src\
│   │   ├── api\               # Client-side API request functions
│   │   ├── components\        # Modular UI components (VerdictCard, ConfidenceMeter, etc.)
│   │   ├── types\             # TypeScript interfaces and verdict domain models
│   │   ├── App.tsx            # Main application layout, navigation tabs, and modal states
│   │   └── main.tsx           # React entry point
│   ├── package.json           # Node.js dependencies and script targets
│   ├── tailwind.config.js     # Tailwind CSS theme, custom colors, and typography
│   ├── tsconfig.json          # TypeScript compiler configuration
│   └── vite.config.ts         # Vite bundler configuration & backend API proxy
├── extension\                 # Chrome Extension (Manifest V3, background worker, content script)
├── .planning\codebase\        # System architecture and quality documentation
├── pytest.ini                 # Pytest root configuration
└── start.bat                  # Unified system launch script
```

---

## 2. Backend Code Conventions (`backend/app/`)

### 2.1 Language Version & Runtime Environment
- **Python Version**: Python 3.10+ (targeted for Python 3.11).
- **Web Framework**: FastAPI (>=0.110.0) running on ASGI server Uvicorn.
- **ORM / Persistence**: SQLAlchemy 2.0+ with SQLite dialect (`sqlite:///{BASE_DIR}/truthlens.db`).

### 2.2 Naming Conventions

| Entity Type | Convention | Examples | Notes |
| :--- | :--- | :--- | :--- |
| **Modules / Files** | `snake_case.py` | `routes_verify.py`, `gemini_rate_limiter.py`, `cache_service.py` | Prefix route modules with `routes_` |
| **Classes** | `PascalCase` | `PublisherCredibilityService`, `GeminiRateLimiter`, `ClaimExtractor` | Descriptive nouns ending in role (`Service`, `Analyzer`, `Limiter`) |
| **Pydantic Schemas** | `PascalCase` ending in `Request` or `Response` | `VerifyRequest`, `ArticleVerifyRequest`, `FeedbackRequest`, `SetKeyRequest` | Explicit purpose in suffix |
| **SQLAlchemy Models** | `PascalCase` | `QueryCache`, `ClaimHistory`, `TrendingClaim`, `PublisherCredibility` | Inherits from declarative `Base` |
| **Functions / Methods** | `snake_case` | `verify_claim`, `extract_core_claim`, `execute_with_retry` | Verb-first naming |
| **Private Methods** | `_snake_case` (single leading underscore) | `_call_gemini_with_model`, `_deserialize_entry`, `_get_trust_tier` | Internal service helper functions |
| **Constants** | `UPPER_SNAKE_CASE` | `PRIMARY_SOURCE_KEYWORDS`, `DIRECTIONAL_ANTONYMS`, `RATING_MAP` | Declared at module scope |
| **Route Endpoints** | `kebab-case` or `snake_case` | `/verify/article`, `/set-key`, `/sources/{domain}` | Pluralized resource nouns where applicable |

### 2.3 Typing and Data Modeling

#### 2.3.1 Type Annotations
All backend functions, methods, and route handlers maintain strict type annotations for parameters and return values:
```python
# Standard typing style
from typing import Optional, List, Dict, Any, Tuple

@classmethod
def check_settled_fact(cls, claim_text: str) -> Optional[Dict[str, Any]]:
    ...
```

#### 2.3.2 Pydantic Schemas vs. SQLAlchemy Models
A strict separation of concerns is maintained between HTTP transport payloads (Pydantic) and database persistence layers (SQLAlchemy):
- **Transport Models (`pydantic.BaseModel`)**: Used for validating incoming HTTP request bodies. Defaults and optional fields are explicitly typed with `Optional[...] = None` or default values.
  ```python
  class VerifyRequest(BaseModel):
      text: str
      url: Optional[str] = None
      language: Optional[str] = "en"
      bypass_cache: Optional[bool] = False
  ```
- **Configuration Models (`pydantic_settings.BaseSettings`)**: Application configuration lives in `app/core/config.py` managed by `BaseSettings` with `SettingsConfigDict(env_file=".env", extra="allow")`. Fallbacks chain environment variables cleanly:
  ```python
  GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", ""))
  ```
- **Database Models (`sqlalchemy.orm.declarative_base`)**: Defined in `app/db/models.py`. Primary keys use indexed auto-increment integers. Unstructured JSON data (such as evidence lists, red flags, and confidence factors) is stored in `Column(Text)` fields and serialized/deserialized manually with `json.dumps()` and `json.loads()`.

### 2.4 Service Pattern & Class-Level Methods
TruthLens organizes business logic into modular service classes located in `backend/app/services/`:
- **Method Scope**: Services predominantly utilize `@classmethod` or `@staticmethod` decorators rather than object instantiation. This eliminates state mutation and ensures clean unit testing.
- **Service Decoupling**:
  - `ClaimExtractor`: URL detection, HTML scraping via `trafilatura`/`bs4`, prefix removal, and tri-mode query classification.
  - `MisinformationPatternAnalyzer`: Deterministic regex scanning for clickbait, sensationalism, dubious stats, and conspiracy language.
  - `PublisherCredibilityService`: Domain parsing, subdomain stripping, and database trust tier resolution.
  - `FactCheckService`: Settled facts evaluation (0 API calls) and Google Fact Check Tools API querying.
  - `GoogleSearchService`: Multi-tier search fallback (Google Custom Search -> Open Web Scraping -> Google News RSS).
  - `GeminiRateLimiter`: In-memory sliding-window concurrency control and exponential backoff retry.
  - `GeminiSynthesisService`: LLM invocation, system prompting, structured JSON extraction, and search grounding.
  - `SynthesisService`: Stance aggregation, 2D verdict formatting, 360° incident briefing compilation, and consistency guard rails.
  - `CacheService`: SHA-256 exact hashing, `rapidfuzz` token-set ratio matching, and entry expiration management.

### 2.5 Async vs. Sync Execution Paradigms
1. **Route Handlers**:
   - Routes performing external network I/O or multi-step synthesis are declared `async def` (e.g., `async def verify_claim(...)`, `async def verify_article(...)`).
   - Pure database queries or lightweight operations are declared as synchronous `def` (e.g., `def list_publishers(...)`, `def get_claim_history(...)`), allowing FastAPI to run them in its internal threadpool without blocking the event loop.
2. **Threadpool Offloading**:
   - The official Google GenAI SDK (`google.genai`) currently uses synchronous client calls. TruthLens offloads blocking SDK calls inside async contexts using `asyncio.to_thread`:
     ```python
     result = await asyncio.to_thread(call_fn, *args, **kwargs)
     ```
3. **Concurrency Serialization**:
   - Single-call budget enforcement and concurrency protection are mediated via `asyncio.Lock` inside `GeminiRateLimiter.execute_with_retry`. Only one active thread/coroutine enters upstream API execution at any given moment.

### 2.6 Error Handling & Custom Exceptions
TruthLens implements a custom exception hierarchy for upstream API communications in `app/services/gemini_rate_limiter.py`:
- `GeminiApiException(Exception)`: Root exception carrying `code`, `message`, `status_code`, and `details`.
  - `GeminiRateLimitException` (HTTP 429): Triggered on local RPM saturation or upstream quota errors.
  - `GeminiNotFoundException` (HTTP 404): Fails fast immediately without retries when a model identifier is invalid.
  - `GeminiAuthException` (HTTP 401/403): Fails fast with actionable developer guidance (e.g., distinguishing OAuth tokens from AI Studio `AIzaSy` keys).

**FastAPI Route Error Handling**:
- Bad user input or missing parameters raise `fastapi.HTTPException` with appropriate status codes (`400`, `404`) and descriptive `detail` messages.
- Synthesis errors (e.g., total upstream outage) do not crash the pipeline; they degrade gracefully to return a structured verdict of `"Error"` or `"Unverified"` with `synthesis["error"]` populated.

### 2.7 Logging Standards
- Loggers are scoped per subsystem using `logging.getLogger("truthlens.<subsystem>")`:
  - `"truthlens.gemini"` for rate limiting and LLM generation.
  - `"truthlens.synthesis"` for claim stance arbitration and verdict generation.
- Log statements include bracketed tags for searchability:
  - `logger.info("[Gemini 3 Flash Live Synthesis] Invoking model '...'")`
  - `logger.warning("[Gemini RateLimiter] Approaching RPM limit...")`
  - `logger.error("[Gemini API Call Error] Attempt 1/3: ...")`

### 2.8 Database Lifecycle & Dependency Injection
- SQLite sessions are created through `SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)`.
- Route dependencies inject sessions using FastAPI's `Depends(get_db)`:
  ```python
  def get_db():
      db = SessionLocal()
      try:
          yield db
      finally:
          db.close()
  ```
- Lifespan context manager in `app/main.py` executes schema creation (`Base.metadata.create_all`) and database seeding (`seed_database`) on startup.

---

## 3. Frontend Code Conventions (`frontend/src/`)

### 3.1 Framework & Build Configuration
- **Core Libraries**: React 18.2, React DOM 18.2.
- **Build Tool**: Vite 5.1 with `@vitejs/plugin-react`.
- **TypeScript**: TypeScript 5.2 configured with `"moduleResolution": "bundler"`, `"jsx": "react-jsx"`, and `"target": "ES2020"`.
- **Styling**: Tailwind CSS 3.4 with PostCSS and Autoprefixer.

### 3.2 TypeScript Conventions
All domain models, verdict types, and component properties are centralized in `src/types/index.ts`:
- **Union Types for Disjoint States**:
  ```typescript
  export type VerdictType = 'True' | 'False' | 'Misleading' | 'Unverified' | 'Satire' | 'Error';
  ```
- **Compound Verdict Modeling**:
  ```typescript
  export interface VerificationResult {
    verdict: VerdictType;
    truth_value?: 'True' | 'False' | 'Likely True' | 'Likely False' | 'Misleading' | 'Satire' | 'Unverifiable' | string;
    knowledge_certainty?: 'Settled Knowledge' | 'Under Active Debate' | 'Emerging / Current Event' | 'Insufficient Evidence' | string;
    final_verdict_display?: string;
    ...
  }
  ```
- **Strict Interface Definition**: Sub-objects (such as `ImpactNumbers`, `QuickSummary`, `RedFlagItem`, and `PublisherCredibility`) have dedicated, strongly typed interfaces.

### 3.3 Component Architecture & React Patterns
- **Functional Components**: Declared with `React.FC<Props>` or directly typed parameters.
- **Props Interfaces**: Defined above each component or in `src/types`. Named `<ComponentName>Props`:
  ```typescript
  interface VerdictCardProps {
    result: VerificationResult;
    onOpenShareModal: () => void;
    onOpenFeedbackModal: () => void;
  }
  export const VerdictCard: React.FC<VerdictCardProps> = ({ ... }) => { ... };
  ```
- **State Management**:
  - Application-level navigation (`activeTab`), backend health status (`isBackendHealthy`), active verification data (`verificationResult`), and modal toggles (`showShareModal`, `showFeedbackModal`, `showApiKeysModal`) are managed cleanly in `App.tsx` via `useState`.
  - Child components communicate changes upward via explicit callback props (`onOpenShareModal`, `onSelectClaim`).
- **Icons**: Sourced exclusively from `lucide-react` to maintain unified stroke weight and aesthetic coherence across all views.

### 3.4 Design System & Styling Conventions
TruthLens adopts a clean, high-contrast dark theme:
- **Base Background**: `bg-slate-950` with slate text hierarchy (`text-slate-100`, `text-slate-400`, `text-slate-500`).
- **Surface Panels**: Glassmorphic translucent cards using `bg-slate-900/60`, subtle borders `border-slate-800/80`, and rounded corners `rounded-xl` or `rounded-2xl`.
- **Verdict Semantic Colors**:
  - `True`: Emerald palette (`text-emerald-400`, `bg-emerald-950/40`, `border-emerald-500/40`).
  - `False`: Rose/Red palette (`text-rose-400`, `bg-rose-950/40`, `border-rose-500/40`).
  - `Misleading`: Amber palette (`text-amber-400`, `bg-amber-950/40`, `border-amber-500/40`).
  - `Satire`: Purple palette (`text-purple-400`, `bg-purple-950/40`, `border-purple-500/40`).
  - `Unverified`: Slate palette (`text-slate-400`, `bg-slate-900/60`, `border-slate-700/60`).
  - `Error`: Amber/Orange warning palette (`text-amber-300`, `bg-amber-950/70`, `border-amber-600/70`).
- **Data Visualization**:
  - Radial SVG circle meter in `ConfidenceMeter.tsx` computes dynamic `strokeDashoffset` based on 0–100 percentage.
  - Source credibility pills use standardized emoji-tagged prefixes (`[🟢 Primary Source]`, `[🔵 Major News Outlet]`, `[🟡 Fact-Checker]`, `[🟠 Domain Expert / Academic]`, `[⚪ Other / General]`).

### 3.5 Client-Side API Communication (`src/api/client.ts`)
- All backend communications use standard `fetch` against the `/api` prefix.
- Vite proxies `/api` requests to `http://127.0.0.1:8000` in development.
- Error handling extracts backend detail messages:
  ```typescript
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Verification failed.' }));
    throw new Error(errorData.detail || `Server error: ${response.status}`);
  }
  ```

---

## 4. Chrome Extension Conventions (`extension/`)

- **Manifest Specification**: Manifest Version 3 (`manifest_version: 3`).
- **Background Context**: Runs as a lightweight Service Worker (`background.js`) handling context menu clicks (`chrome.contextMenus.onClicked`).
- **Content Injection**: Injects `content.js` and `content.css` dynamically across all URLs (`<all_urls>`) to show non-intrusive inline fact-check badges.
- **Backend Communication**: Directly requests `http://localhost:8000/api/verify` using `fetch`.
- **Scripting Idiom**: Standard vanilla ES6+ (no external bundle dependencies or build steps required).

---

## 5. Quality Tooling & Verification Commands

### 5.1 Verification Checklist for Developers

| Check | Tool / Command | Target / Scope |
| :--- | :--- | :--- |
| **Backend Unit & Pipeline Tests** | `pytest` or `python -m pytest` | All test files in `backend/tests/` |
| **Backend Fast Test Run** | `pytest backend/tests/test_extractor.py backend/tests/test_pattern_analyzer.py backend/tests/test_credibility.py` | Local rule-based checks (sub-second) |
| **Frontend Type Checking** | `npm.cmd run build` (inside `frontend/`) | Executes `tsc && vite build` |
| **Frontend Dev Server** | `npm.cmd run dev` (inside `frontend/`) | Starts Vite on `http://localhost:5173` |
| **Backend Dev Server** | `python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000` (inside `backend/`) | Starts FastAPI on `http://127.0.0.1:8000` |
| **Full System Launcher** | `start.bat` | Starts both backend and frontend in separate terminals |

### 5.2 Identified Code Quality Opportunities
- **Static Analysis**: Adding `ruff` or `flake8` + `black` to `backend/` will standardize formatting and catch unused imports.
- **Frontend Linter**: Adding `eslint` and `prettier` to `frontend/` will enforce React Hooks linting and consistent import ordering.
- **Strict TypeScript**: Transitioning `"strict": false` to `"strict": true` in `frontend/tsconfig.json` will provide compile-time null safety guarantees across API responses.
