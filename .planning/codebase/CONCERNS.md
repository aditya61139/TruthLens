# TruthLens Codebase Concerns, Technical Debt & Risk Analysis

This document provides a comprehensive technical audit of the **TruthLens** codebase across backend, frontend, and browser extension layers. It details technical debt, fragility, security vulnerabilities, performance bottlenecks, error-handling gaps, test coverage deficits, and scalability/maintenance risks.

---

## 1. Technical Debt, Fragility & Hardcoded Logic

### 1.1 Dual Database Files and Working Directory Ambiguity
- **Observation**: Two SQLite database files exist in the repository:
  - Root: [`truthlens.db`](file:///P:/TruthLens/truthlens.db) (176 KB)
  - Backend: [`truthlens.db`](file:///P:/TruthLens/backend/truthlens.db) (245 KB)
- **Root Cause**: In [`config.py`](file:///P:/TruthLens/backend/app/core/config.py#L30-L31):
  ```python
  BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
  DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/truthlens.db")
  ```
  Depending on how the server is launched (from root via `python backend/app/main.py` vs. from `backend/` via [`start.bat`](file:///P:/TruthLens/start.bat#L8) or [`run_backend.bat`](file:///P:/TruthLens/run_backend.bat)), or how `DATABASE_URL` is parsed by SQLAlchemy under Windows with mixed slashes, queries target different database files.
- **Risk**: Data desynchronization, stale caches, lost verification history, and confusion during development or deployment.

### 1.2 Dual `.env` Files
- **Observation**: There is a `.env` in `P:\TruthLens\.env` and another in `P:\TruthLens\backend\.env`.
- **Root Cause**: [`pydantic_settings`](file:///P:/TruthLens/backend/app/core/config.py#L45) searches for `.env` in the active working directory, while [`routes_config.py`](file:///P:/TruthLens/backend/app/api/routes_config.py#L54) explicitly writes to `settings.BASE_DIR / ".env"`.
- **Risk**: Keys updated dynamically via the Web UI may be written to one file while the running process or developer scripts read the other.

### 1.3 Fragile Rule-Based Matching & Regex Heuristics
- **Settled Facts Pattern Lexicon**:
  In [`factcheck_service.py`](file:///P:/TruthLens/backend/app/services/factcheck_service.py#L308-L356), the system relies on approximately 15 positive regex patterns ([`SETTLED_FACT_PATTERNS`](file:///P:/TruthLens/backend/app/services/factcheck_service.py#L309)) and 8 negative patterns ([`SETTLED_CONTRADICTION_PATTERNS`](file:///P:/TruthLens/backend/app/services/factcheck_service.py#L339)).
  - *Fragility*: Slight grammatical shifts (e.g., *"Does water boil at 100 degrees?"* or *"At 100C water boils"*) will miss the settled knowledge engine completely.
  - *Duplicate code*: Lines 439 and 440 of [`factcheck_service.py`](file:///P:/TruthLens/backend/app/services/factcheck_service.py#L439-L440) contain redundant consecutive `return None` statements.
- **Directional & Antonym Detection**:
  In [`stance_service.py`](file:///P:/TruthLens/backend/app/services/stance_service.py#L29-L51), [`DIRECTIONAL_ANTONYMS`](file:///P:/TruthLens/backend/app/services/stance_service.py#L29) maps words like `"east"` $\leftrightarrow$ `"west"`, `"rises"` $\leftrightarrow$ `"sets"`, `"freeze"` $\leftrightarrow$ `"boil"`.
  - *Fragility*: If an article mentions *"The wind was blowing east to west"*, or *"East Coast storm causes flooding in the west"*, the system can falsely flag the document as `CONTRADICTS`.
- **Numeric Inconsistency Detection**:
  [`StanceDetector.detect_stance`](file:///P:/TruthLens/backend/app/services/stance_service.py#L140-L151) extracts all digits and flags `CONTRADICTS` if sets do not intersect:
  ```python
  if not set(claim_nums).intersection(set(doc_nums)):
      sim = fuzz.token_set_ratio(claim_lower, combined_doc)
      if sim > 65:
          return ("CONTRADICTS", 80.0, ...)
  ```
  - *Fragility*: A claim stating *"5 people were evacuated"* evaluated against an article published on *"May 12"* stating *"five people were evacuated"* triggers a false contradiction because digit `5` is not in `['12']`.
- **Curated Offline Fact-Check DB**:
  [`OFFLINE_FACT_CHECKS`](file:///P:/TruthLens/backend/app/services/factcheck_service.py#L75-L172) contains exactly 8 hardcoded claims. Keyword matching ([`match_offline_database`](file:///P:/TruthLens/backend/app/services/factcheck_service.py#L520)) requires $\ge 2$ keyword matches from a static list, creating an illusion of broad offline capability that only covers a trivial set of demo queries.

### 1.4 Brittle Web Scraping Implementations
- **DuckDuckGo HTML Scraping**:
  In [`google_search_service.py`](file:///P:/TruthLens/backend/app/services/google_search_service.py#L91-L174) ([`search_open_web`](file:///P:/TruthLens/backend/app/services/google_search_service.py#L91)), search results are scraped from `https://html.duckduckgo.com/html/?q=...` by parsing CSS classes (`result__a`, `result__snippet`, `web-result`).
  - *Fragility*: DuckDuckGo regularly alters DOM class names, serves bot challenge pages (CAPTCHAs), or blocks datacenter / cloud IP ranges with HTTP 403.
- **Google News RSS Feeds & Redirect URL Masking**:
  In [`news_service.py`](file:///P:/TruthLens/backend/app/services/news_service.py#L56-L137) ([`fetch_news_consensus`](file:///P:/TruthLens/backend/app/services/news_service.py#L56)), articles are fetched from Google News RSS.
  - *Fragility*: Links returned by Google News RSS are obfuscated Google redirect URLs (e.g., `news.google.com/rss/articles/CBMi...`). In [`routes_verify.py`](file:///P:/TruthLens/backend/app/api/routes_verify.py#L120-L121), the pipeline passes `ev.get("source_site")` to [`PublisherCredibilityService.get_publisher_info`](file:///P:/TruthLens/backend/app/services/credibility_service.py#L34). Because the domain appears as `news.google.com`, publisher credibility lookups for the actual underlying news organization (e.g., Reuters, BBC, AP) fail and return unranked status.

### 1.5 Subdomain Splitting Bug for ccTLDs
- In [`credibility_service.py`](file:///P:/TruthLens/backend/app/services/credibility_service.py#L45-L50):
  ```python
  if not pub and "." in domain:
      parts = domain.split(".")
      if len(parts) > 2:
          main_domain = ".".join(parts[-2:])
          pub = db.query(PublisherCredibility).filter(PublisherCredibility.domain == main_domain).first()
  ```
  - *Bug*: For domains with multi-part country code top-level domains (ccTLDs) such as `bbc.co.uk`, `parts` is `['bbc', 'co', 'uk']`. `parts[-2:]` produces `co.uk`, completely discarding the second-level domain `bbc` and failing the database match.

### 1.6 Mock / Fake Fallback Metrics
- In [`routes_feedback.py`](file:///P:/TruthLens/backend/app/api/routes_feedback.py#L53):
  ```python
  user_satisfaction_rate = round((helpful_count / total_feedback * 100.0), 1) if total_feedback > 0 else 98.4
  ```
  - *Observation*: If no feedback has been submitted, the system fabricates an artificial `98.4%` satisfaction rate for marketing/presentation purposes rather than returning `0.0` or `null`.

### 1.7 Python 3.12+ Deprecation Issues
- `datetime.datetime.utcnow()` is used in [`models.py`](file:///P:/TruthLens/backend/app/db/models.py#L21), [`routes_verify.py`](file:///P:/TruthLens/backend/app/api/routes_verify.py#L187), [`cache_service.py`](file:///P:/TruthLens/backend/app/services/cache_service.py#L31), and [`seed_data.py`](file:///P:/TruthLens/backend/app/db/seed_data.py#L181). In Python 3.12+, `utcnow()` is formally deprecated in favor of `datetime.datetime.now(datetime.timezone.utc)`.

---

## 2. Security Concerns

### 2.1 Unauthenticated Remote API Key Overwrite & Arbitrary File Modification
- **Location**: [`routes_config.py`](file:///P:/TruthLens/backend/app/api/routes_config.py#L39-L77) ([`POST /api/config/set-key`](file:///P:/TruthLens/backend/app/api/routes_config.py#L39))
- **Vulnerability**:
  - The endpoint requires **no authentication, API token, session, or role verification**.
  - Any HTTP client or malicious web page can POST:
    ```json
    { "google_api_key": "attacker_supplied_key" }
    ```
  - The handler overwrites `settings.GOOGLE_API_KEY`, `settings.GEMINI_API_KEY`, and `os.environ` in memory, and writes it directly to disk in `.env`.
- **Severity**: **Critical**. Allows unauthorized key hijacking, Denial of Service (by setting a bogus key), or quota theft.

### 2.2 Insecure CORS Configuration
- **Location**: [`main.py`](file:///P:/TruthLens/backend/app/main.py#L33-L39)
- **Code**:
  ```python
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["*"],
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )
  ```
- **Vulnerability**:
  - `allow_origins=["*"]` combined with `allow_credentials=True` violates CORS specifications. Standard browsers reject `Access-Control-Allow-Origin: *` when credentials are included.
  - Furthermore, this wildcard allows any website visited in a user's browser to execute requests against `http://127.0.0.1:8000`, including triggering [`/api/config/set-key`](file:///P:/TruthLens/backend/app/api/routes_config.py#L39) or wiping history via [`DELETE /api/history/{id}`](file:///P:/TruthLens/backend/app/api/routes_history.py#L97).

### 2.3 Server-Side Request Forgery (SSRF) in URL Verification
- **Location**: [`extractor.py`](file:///P:/TruthLens/backend/app/services/extractor.py#L157-L190) ([`ClaimExtractor.extract_from_url`](file:///P:/TruthLens/backend/app/services/extractor.py#L157))
- **Vulnerability**:
  - The endpoint [`POST /api/verify`](file:///P:/TruthLens/backend/app/api/routes_verify.py#L30) accepts a user-provided `url`.
  - It connects using `httpx.AsyncClient(timeout=10.0, follow_redirects=True)` without validating the host IP address.
  - An attacker can submit:
    - `http://127.0.0.1:8000/api/config/status` (Local API reconnaissance)
    - `http://169.254.169.254/latest/meta-data/` (AWS/GCP cloud metadata exfiltration)
    - `http://192.168.1.1/` (Internal router/firewall interface probing)
  - With `follow_redirects=True`, attackers can bypass naive domain checks using DNS rebinding or redirect services.

### 2.4 Stored / Reflected XSS in Browser Extension Content Script
- **Location**: [`extension/content.js`](file:///P:/TruthLens/extension/content.js#L49-L68) ([`showTruthLensResult`](file:///P:/TruthLens/extension/content.js#L38))
- **Code**:
  ```javascript
  overlay.innerHTML = `
    <div class="truthlens-card">
      ...
      <p class="truthlens-claim">"${result.extracted_claim}"</p>
      <p class="truthlens-summary">${result.summary}</p>
      ...
    </div>
  `;
  ```
- **Vulnerability**:
  - `result.extracted_claim` and `result.summary` are interpolated directly into `overlay.innerHTML` without HTML entity encoding or DOM sanitization.
  - If a user highlights an adversarial string containing `<img src=x onerror=...>` or an LLM response outputs malicious HTML/JavaScript, arbitrary script executes in the security context of the webpage the user is currently viewing.
  - Since [`manifest.json`](file:///P:/TruthLens/extension/manifest.json#L24) specifies `"matches": ["<all_urls>"]`, this vulnerability can be leveraged to steal session tokens, cookies, or credentials on sensitive domains (e.g., banking, email).
  - Additionally, the extension does not use a Shadow DOM, exposing its UI to style and script manipulation by the host page.

### 2.5 Unauthenticated Destructive History Deletion
- **Location**: [`routes_history.py`](file:///P:/TruthLens/backend/app/api/routes_history.py#L97-L104) ([`DELETE /api/history/{history_id}`](file:///P:/TruthLens/backend/app/api/routes_history.py#L97))
- **Vulnerability**:
  - Any client can delete any arbitrary history record by ID without authentication or ownership checks.

### 2.6 Unbounded Input Size & Lack of Validation
- **Location**: [`routes_verify.py`](file:///P:/TruthLens/backend/app/api/routes_verify.py#L19-L29), [`routes_feedback.py`](file:///P:/TruthLens/backend/app/api/routes_feedback.py#L12-L19)
- **Vulnerability**:
  - Pydantic models `VerifyRequest` and `FeedbackRequest` define `text: str` and `comments: Optional[str]` without `max_length` bounds.
  - An attacker can transmit multi-megabyte payloads, driving high CPU utilization during regex scanning and bloating SQLite table storage.

---

## 3. Performance Bottlenecks

### 3.1 SQLite Database Locking Under Concurrent Requests
- **Locations**:
  - [`database.py`](file:///P:/TruthLens/backend/app/db/database.py#L5-L8)
  - [`cache_service.py`](file:///P:/TruthLens/backend/app/services/cache_service.py#L41,L57)
  - [`routes_verify.py`](file:///P:/TruthLens/backend/app/api/routes_verify.py#L190)
- **Bottlenecks**:
  1. **Missing WAL Mode**: SQLite defaults to standard rollback journal mode, locking the entire database during write operations.
  2. **No Busy Timeout**: `engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})` does not configure `timeout=30` or `PRAGMA busy_timeout=5000`.
  3. **Writes on Read Operations**: Every cache hit executes:
     ```python
     exact_entry.access_count += 1
     db.commit()
     ```
     Under concurrent queries, multiple concurrent reads attempt to open write transactions simultaneously to bump `access_count`, triggering immediate `sqlite3.OperationalError: database is locked` exceptions.

### 3.2 Cache Eviction Deficit & $O(N)$ In-Memory Full Table Scan
- **Location**: [`cache_service.py`](file:///P:/TruthLens/backend/app/services/cache_service.py#L45-L54)
- **Bottlenecks**:
  1. **Full Active Table Scan**:
     ```python
     active_entries = db.query(QueryCache).filter(QueryCache.expires_at > now).all()
     for entry in active_entries:
         score = fuzz.token_set_ratio(normalized, entry.normalized_query)
     ```
     On every cache miss, **all** unexpired rows are pulled from disk into Python memory and iterated over using RapidFuzz. If the cache holds 10,000 items, each miss performs 10,000 Levenshtein/token distance calculations in Python.
  2. **No Expiration Cleanup Job**: Expired cache entries are never purged from [`QueryCache`](file:///P:/TruthLens/backend/app/db/models.py#L5). The table grows monotonically until manual intervention.

### 3.3 Gemini Concurrency Serialization Bottleneck
- **Location**: [`gemini_rate_limiter.py`](file:///P:/TruthLens/backend/app/services/gemini_rate_limiter.py#L38,L84)
- **Bottleneck**:
  ```python
  class GeminiRateLimiter:
      _lock: asyncio.Lock = asyncio.Lock()

      @classmethod
      async def execute_with_retry(cls, call_fn: Callable, *args, **kwargs) -> Any:
          async with cls._lock:
              await cls.acquire()
              for attempt in range(retries + 1):
                  result = await asyncio.to_thread(call_fn, *args, **kwargs)
                  ...
                  await asyncio.sleep(backoff)
  ```
  - `async with cls._lock` encloses the **entire** execution lifecycle (acquire, network invocation, and all exponential backoff retry sleeps).
  - While one request waits for a 3-5 second Gemini network response or sleeps during a 429 retry (1.5s - 3.0s), **all other concurrent queries are blocked**. Concurrency across the entire server for AI verification is strictly throttled to $1$.

### 3.4 Sequential API Calls in Article Mode
- **Location**: [`routes_verify.py`](file:///P:/TruthLens/backend/app/api/routes_verify.py#L270-L307) ([`verify_article`](file:///P:/TruthLens/backend/app/api/routes_verify.py#L230))
- **Bottleneck**:
  - The handler extracts up to 6 claims and iterates through them sequentially:
    ```python
    for c in candidate_claims:
        search_res = await GoogleSearchService.search_live_web(c_text, c_search_query)
        fc_ev = await FactCheckService.verify_claim_evidence(c_text)
        synth = await SynthesisService.synthesize(...)
    ```
  - Up to 12-18 remote HTTP calls occur in series rather than utilizing `asyncio.gather()`, leading to response times exceeding 20-30 seconds.

### 3.5 External API Rate Quota Ceilings
- **Google Custom Search API**: The free tier provides only **100 queries/day**. In an active environment, this quota is consumed in minutes.
- **Gemini Free Tier**: Capped at 15 Requests Per Minute (RPM) and 1,000,000 Tokens Per Minute (TPM).
- **DuckDuckGo Scraping**: Frequently blocked within 5-10 requests from identical IP addresses.

---

## 4. Error Handling & Robustness

### 4.1 Blind Exception Swallowing Across Service Layers
- In multiple services, network errors, timeouts, and HTTP errors are completely suppressed with bare `except Exception: return []`:
  - [`GoogleSearchService.search_open_web`](file:///P:/TruthLens/backend/app/services/google_search_service.py#L110-L111)
  - [`GoogleSearchService.search_google_custom_search`](file:///P:/TruthLens/backend/app/services/google_search_service.py#L231-L232)
  - [`FactCheckService.search_google_fact_check`](file:///P:/TruthLens/backend/app/services/factcheck_service.py#L516-L517)
  - [`NewsCrossReferenceService.fetch_news_consensus`](file:///P:/TruthLens/backend/app/services/news_service.py#L79-L80,L134-L135)
  - [`routes_config.py`](file:///P:/TruthLens/backend/app/api/routes_config.py#L75-L76)
- **Impact**: Upstream authentication failures (e.g. invalid Google API key), quota exhaustion (HTTP 429), or network timeouts fail silently. The system interprets API failures as "no evidence found" and degrades claim verifications to "Unverified" without alerting administrators or explaining the outage to the user.

### 4.2 Multi-Process Rate Limiter Desynchronization
- **Location**: [`gemini_rate_limiter.py`](file:///P:/TruthLens/backend/app/services/gemini_rate_limiter.py#L37-L40)
- **Issue**: `_timestamps` and `_lock` are in-memory class variables local to a single Python process.
- **Risk**: If the application is run in production with multiple Uvicorn workers (`uvicorn --workers 4`), each worker maintains its own independent rate limiter. Upstream limits (15 RPM) are multiplied by the worker count ($4 \times 15 = 60$ RPM), causing frequent upstream 429 quota exhaustion.

### 4.3 Brittle LLM Output JSON Deserialization
- **Location**: [`gemini_service.py`](file:///P:/TruthLens/backend/app/services/gemini_service.py#L287-L305)
- **Issue**:
  - The service strips markdown code blocks and attempts `json.loads()`, falling back to regex extraction `re.search(r'(\{.*\})', raw_text, re.DOTALL)`.
  - If the model hits `max_output_tokens=2048` mid-JSON or returns malformed syntax, the regex match fails or returns invalid JSON, causing the entire evaluation to fail.

### 4.4 Model Degradation Loop Latency
- **Location**: [`gemini_service.py`](file:///P:/TruthLens/backend/app/services/gemini_service.py#L166-L181,L265-L281)
- **Issue**:
  - `get_candidate_models()` tests a list of 7 model identifiers (`gemini-3.1-flash-live-preview`, `gemini-3-flash-preview`, `gemini-3.6-flash`, etc.).
  - If a model returns 404/unsupported, `_call_gemini()` iterates through candidate models sequentially. Each failed model invocation incurs network latency and rate limiter acquisitions before finding a working model.

---

## 5. Testing Gaps

### 5.1 Test Coverage Inventory
The existing test suite in [`backend/tests`](file:///P:/TruthLens/backend/tests) consists of four files:
- [`test_credibility.py`](file:///P:/TruthLens/backend/tests/test_credibility.py) (60 lines): Tests domain extraction, publisher lookup in SQLite, rating normalization.
- [`test_extractor.py`](file:///P:/TruthLens/backend/tests/test_extractor.py) (34 lines): Tests text cleanup, claim extraction heuristics, URL detection.
- [`test_pattern_analyzer.py`](file:///P:/TruthLens/backend/tests/test_pattern_analyzer.py) (25 lines): Tests clickbait, sensationalism, and attribution detection.
- [`test_verification_pipeline.py`](file:///P:/TruthLens/backend/tests/test_verification_pipeline.py) (459 lines): Comprehensive integration tests covering settled facts, time-sensitive queries, rate limiter, and endpoints.

### 5.2 Critical Testing Deficits

| Subsystem | Current Test State | Identified Risk |
| :--- | :--- | :--- |
| **Frontend (React/Vite)** | **0 Tests** (No test runner, no Vitest/Jest/Cypress configuration in [`package.json`](file:///P:/TruthLens/frontend/package.json)) | UI crashes on unexpected API payloads, regression in state management, broken modals. |
| **Browser Extension** | **0 Tests** (No service worker, popup, or content script tests) | Injected script errors, DOM corruption on host websites, broken background messaging. |
| **Test Database Isolation** | **Failed Isolation** ([`test_verification_pipeline.py`](file:///P:/TruthLens/backend/tests/test_verification_pipeline.py#L17-L26) uses active engine and disk `truthlens.db`) | Tests mutate local development data; concurrent test runs cause database lock errors. |
| **External API Mocking** | **Unmocked External Requests** | Tests execute live HTTP requests to Google services and DuckDuckGo; tests fail when offline or rate-limited. |
| **SSRF & Security Tests** | **0 Tests** | No test cases verifying blocking of loopback (`127.0.0.1`), metadata IP (`169.254.169.254`), or private subnets. |
| **Concurrency & Locking** | **0 Tests** | No multi-threaded or concurrent async load tests verifying SQLite stability under write contention. |
| **Config Overwrite Safety** | **0 Tests** | No tests for [`POST /api/config/set-key`](file:///P:/TruthLens/backend/app/api/routes_config.py#L39) error paths, file write race conditions, or unauthorized access. |

---

## 6. Scalability & Maintenance Risks

### 6.1 Database Architecture Limitations
- **SQLite Single-File Storage**: SQLite is unsuited for multi-user horizontal scaling or distributed deployments (Kubernetes, serverless, multi-worker containers).
- **Recommendation**: Transition to PostgreSQL with connection pooling (e.g., PgBouncer or SQLAlchemy asyncpg pool) to support concurrent writes, ACID transactions, and row-level locking.

### 6.2 Absence of Distributed Caching & Message Brokering
- The caching layer is tightly coupled to SQLite via SQLAlchemy models.
- **Recommendation**: Extract caching to **Redis** or **KeyDB** with native TTL expiration, eliminating the $O(N)$ in-memory Python scan and avoiding disk writes on cache reads.

### 6.3 Hardcoded Infrastructure & Localhost Dependencies
- **Browser Extension**:
  - Hardcoded API base: `http://localhost:8000/api/verify` in [`background.js`](file:///P:/TruthLens/extension/background.js#L21) and [`popup.js`](file:///P:/TruthLens/extension/popup.js#L1).
  - Hardcoded frontend link: `http://localhost:5173` in [`content.js`](file:///P:/TruthLens/extension/content.js#L62).
  - *Risk*: Extension cannot be deployed to Chrome Web Store or point to a staging/production server without manual source code modification.
- **Frontend Vite Health Check**:
  - In [`client.ts`](file:///P:/TruthLens/frontend/src/api/client.ts#L132), `fetch('/health')` lacks the `/api` prefix and bypasses the proxy configuration in [`vite.config.ts`](file:///P:/TruthLens/frontend/vite.config.ts#L11-L15). In production static hosting, `/health` will return a 404 or index HTML fallback.

---

## 7. Actionable Remediation Roadmap

```mermaid
flowchart TD
    subgraph Phase 1: Critical Security & Integrity
        S1["Secure /api/config/set-key with admin authentication"]
        S2["Sanitize extension content.js to prevent XSS (Use textContent / Shadow DOM)"]
        S3["Fix CORS in main.py (Disallow wildcard origin with credentials)"]
        S4["Add SSRF IP validation filter to ClaimExtractor.extract_from_url"]
    end

    subgraph Phase 2: Concurrency & Database Stability
        P1["Enable SQLite WAL mode & busy_timeout=5000 in database.py"]
        P2["Decouple access_count write from cache read path"]
        P3["Implement cache cleanup job and replace O(N) scan with indexed lookup"]
        P4["Narrow GeminiRateLimiter lock to permit concurrent requests"]
    end

    subgraph Phase 3: Reliability & Test Coverage
        R1["Replace silent exception swallowing with structured logging & error propagation"]
        R2["Mock external HTTP requests in pytest suite; isolate test DB to :memory:"]
        R3["Add Vitest test suite for frontend React components"]
        R4["Parameterize extension backend endpoint via chrome.storage"]
    end

    Phase 1 --> Phase 2 --> Phase 3
```

1. **Phase 1: Immediate Security Hotfixes**
   - Add authentication middleware or token verification to [`/api/config/set-key`](file:///P:/TruthLens/backend/app/api/routes_config.py#L39).
   - In [`extension/content.js`](file:///P:/TruthLens/extension/content.js#L49-L68), replace `innerHTML` string interpolation with `textContent` or use `DOMPurify` within a Shadow DOM.
   - Restrict CORS origins in [`main.py`](file:///P:/TruthLens/backend/app/main.py#L33-L39) to authorized domains, and remove `allow_origins=["*"]` when credentials are enabled.
   - Enforce IP address resolution checks in [`extractor.py`](file:///P:/TruthLens/backend/app/services/extractor.py#L157) to reject loopback, link-local, and private subnets before initiating requests.

2. **Phase 2: Database & Concurrency Optimization**
   - Configure SQLite WAL mode and busy timeouts:
     ```python
     @event.listens_for(engine, "connect")
     def set_sqlite_pragma(dbapi_connection, connection_record):
         cursor = dbapi_connection.cursor()
         cursor.execute("PRAGMA journal_mode=WAL")
         cursor.execute("PRAGMA busy_timeout=5000")
         cursor.close()
     ```
   - In [`cache_service.py`](file:///P:/TruthLens/backend/app/services/cache_service.py#L41), remove `db.commit()` on read hits or batch access counts asynchronously.
   - Narrow the scope of `GeminiRateLimiter._lock` to request timestamp reservation rather than locking across the entire network roundtrip.

3. **Phase 3: Resiliency & Test Automation**
   - Log explicit exception details across [`google_search_service.py`](file:///P:/TruthLens/backend/app/services/google_search_service.py), [`factcheck_service.py`](file:///P:/TruthLens/backend/app/services/factcheck_service.py), and [`news_service.py`](file:///P:/TruthLens/backend/app/services/news_service.py).
   - Add Vitest and React Testing Library to [`frontend/package.json`](file:///P:/TruthLens/frontend/package.json).
   - Update [`test_verification_pipeline.py`](file:///P:/TruthLens/backend/tests/test_verification_pipeline.py#L17) to use an in-memory SQLite database and mock all external HTTP calls with `respx` or `unittest.mock`.
