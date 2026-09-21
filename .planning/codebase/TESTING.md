# TruthLens Testing Architecture & Quality Guide

This document details the test framework configuration, test suite architecture, fixture lifecycle, scenario inventory, and quality assurance workflows across the TruthLens repository (`P:\TruthLens`).

---

## 1. Testing Philosophy & Verification Strategy

TruthLens tests prioritize deterministic, regression-resilient verification across its multi-layer fact-checking pipeline. The core testing tenets are:

1. **Zero-AI Settled Fact Determinism**: Universal scientific, physical, and geographic facts (and their direct contradictions) must resolve with $0$ external Gemini calls, 95%+ confidence, and authoritatively cited sources.
2. **Strict Single-Call AI Budgeting**: A single verification query must never make more than 1 Gemini API call under any circumstance to preserve rate limits and prevent quota exhaustion.
3. **Fail-Fast Error Handling**: Upstream client configuration errors (such as 404 invalid model names or 401 invalid API keys) must fail fast without blind, wasteful retries.
4. **Two-Dimensional Verdict Integrity**: Truth Value (`True`, `False`, `Misleading`, `Unverified`, `Satire`) and Knowledge Certainty (`Settled Knowledge`, `Under Active Debate`, `Emerging / Current Event`, `Insufficient Evidence`) are tested independently.
5. **Clause-Level Guard Rails**: If any clause in an assertion is debunked, the system guard rail strictly prevents an overall `True` verdict.

---

## 2. Test Configuration & Environment

### 2.1 Configuration File (`pytest.ini`)
The pytest configuration is located at the workspace root:
```ini
[pytest]
pythonpath = backend
testpaths = backend/tests
```
- `pythonpath = backend`: Ensures `import app...` resolves seamlessly without requiring `PYTHONPATH=.` or manual editable package installation.
- `testpaths = backend/tests`: Automatically limits discovery to backend test suites.

### 2.2 Testing Dependencies
Declared in `backend/requirements.txt`:
- `pytest>=8.0.0`: Primary test runner and assertion framework.
- `pytest-asyncio>=0.23.5`: Async test runner support for coroutines and async fixtures.
- `httpx>=0.27.0` & `fastapi`: Underlying transport for `starlette.testclient.TestClient`.

---

## 3. Test Suite Inventory

TruthLens backend tests are organized into four specialized test files inside `backend/tests/`:

```
backend/tests/
├── test_credibility.py             # Domain extraction, publisher scoring & rating mapping
├── test_extractor.py               # Text cleaning, core claim extraction & URL parsing
├── test_pattern_analyzer.py        # Misinformation red flags, clickbait & conspiracy NLP
└── test_verification_pipeline.py   # Comprehensive pipeline, rate limiter, tri-mode & RAG tests
```

### 3.1 `test_credibility.py` (Publisher & Fact-Checker Mapping)
- **Scope**: Tests the publisher credibility resolution engine and fact-checker rating normalization dictionary.
- **Key Test Functions**:
  - `test_extract_domain()`: Validates extracting domain names from raw URLs (`https://www.reuters.com/fact-check` -> `reuters.com`) and loose text with embedded links.
  - `test_get_publisher_info(db_session)`: Tests database lookups for known credible publishers (Reuters: score 99, Center bias) vs. high-risk sources (InfoWars: score 12, High-Risk trust tier).
  - `test_normalize_rating()`: Validates standardizing various fact-checker ratings into canonical verdicts (`"Pants on Fire"` -> `"False"`, `"Misleading context"` -> `"Misleading"`, `"Correct Attribution"` -> `"True"`, `"Satire"` -> `"Satire"`).

### 3.2 `test_extractor.py` (Claim Extraction & Cleaning)
- **Scope**: Validates noisy social media text parsing, core claim extraction, URL detection, and multi-claim article segmentation.
- **Key Test Functions**:
  - `test_clean_text()`: Verifies stripping clickbait prefixes (`BREAKING NEWS:`, `ALERT:`), URLs, and hashtags while preserving core assertions.
  - `test_extract_core_claim()`: Ensures the dominant verifiable factual statement is extracted from subjective commentary.
  - `test_extract_all_claims()`: Tests chunking a multi-paragraph article into discrete, checkable claims.
  - `test_is_url()`: Validates detection of web URLs (`https://...`, `http://...`) vs. plain claim statements.

### 3.3 `test_pattern_analyzer.py` (Linguistic Misinformation Heuristics)
- **Scope**: Tests deterministic regex pattern scanning for emotional manipulation, sensationalism, dubious stats, and conspiracy tropes.
- **Key Test Functions**:
  - `test_clean_objective_text()`: Ensures neutral, scientific text (e.g. ESA Euclid telescope launch) produces a red-flag score $<25.0$ and `"green"` or `"yellow"` risk status with 0 clickbait flags.
  - `test_sensationalist_misinformation_text()`: Confirms high red-flag scores ($\ge 60.0$) and `"red"` status on sensationalized, all-caps miracle cure claims, triggering clickbait, conspiracy, and dubious statistics checklist items.
  - `test_vague_attribution_detection()`: Validates flagging anonymous, non-specific authority cues (e.g., *"Scientists say..."* without citing an institution).

### 3.4 `test_verification_pipeline.py` (End-to-End Integration & Regression)
This is the central test suite containing 26 extensive end-to-end integration and regression tests:

| Test Name | Verification Focus / Bug Fix Rationale | Key Assertions |
| :--- | :--- | :--- |
| `test_health_check` | API availability | `status_code == 200`, `status == "healthy"` |
| `test_single_gemini_call_budget_enforcement` | Enforces budget ceiling of $\le 1$ Gemini API call per verification | `gemini_calls_made <= 1` |
| `test_rate_limiter_inter_call_spacing` | Verifies `GeminiRateLimiter` enforces minimum 500ms spacing | `duration >= 0.4s` between successive calls |
| `test_rate_limiter_404_not_found_fails_fast` | Confirms invalid model endpoints raise `GeminiNotFoundException` immediately | `exc_info.value.code == "API_NOT_FOUND"` |
| `test_rate_limiter_401_auth_error_fails_fast` | Confirms invalid API keys fail fast without retrying | `exc_info.value.code == "API_AUTH_ERROR"` |
| `test_time_sensitive_detection_and_query_normalization` | Verifies current event question detection and query normalization | `is_time_sensitive == True`, non-question search query |
| `test_time_sensitive_verification_attempts_web_search` | Confirms breaking events trigger live web search metadata | `web_search["attempted"] == True`, query used, provider |
| `test_settled_fact_sun_rises_in_east` | Validates settled fact resolution with 0 AI calls | `verdict == "True"`, `gemini_calls_made == 0`, `confidence >= 95.0`, $\ge 2$ sources |
| `test_settled_fact_water_boils` | Thermodynamics settled fact | `verdict == "True"`, `confidence >= 95.0`, `gemini_calls_made == 0` |
| `test_settled_fact_paris_capital_france` | Geography settled fact | `verdict == "True"`, `confidence >= 95.0`, `gemini_calls_made == 0` |
| `test_unverified_claim_confidence_coupling` | Prevents unverified claims from having high confidence | `verdict in ["Unverified", "Error"]`, `confidence <= 45.0` |
| `test_news_relevance_filter` | Semantic similarity thresholding on news headlines | Unrelated $<55.0$, direct match $>70.0$ |
| `test_verify_known_false_claim` | Verified debunking of known medical myth (garlic water) | `verdict == "False"`, `confidence >= 80.0`, sources returned |
| `test_verify_known_true_claim` | Verified confirmation of scientific discovery (JWST) | `verdict == "True"`, `confidence >= 80.0` |
| `test_fuzzy_caching_performance` | RapidFuzz token matching for near-duplicate claims | Second query `cached == True`, identical verdict |
| `test_article_mode_verification` | Multi-claim extraction and aggregate Article Trust Score | `overall_trust_score` calculated, `claims` array, verdict distribution |
| `test_publisher_sources_endpoint` | Querying sources endpoint (`/api/sources?q=reuters`) | `total >= 1`, matched publisher list |
| `test_trending_claims_endpoint` | Monitored trending hoaxes (`/api/trending`) | `trending` list $\ge 3$ items, `stats` breakdown |
| `test_community_feedback` | Submitting helpful/incorrect verdict feedback (`/api/feedback`) | `status == "success"` |
| `test_settled_fact_contradiction_sun_rises_in_west` | Settled fact contradiction resolution with 0 AI calls | `verdict == "False"`, `is_settled_fact == True`, `confidence >= 95.0`, `gemini_calls_made == 0` |
| `test_settled_fact_contradiction_earth_is_flat` | Flat earth contradiction resolution with 0 AI calls | `verdict == "False"`, `is_settled_fact == True`, `confidence >= 95.0` |
| `test_claim_classifier_domains` | Categorizes text into `SETTLED_FACT`, `CURRENT_EVENT`, `OPINION`, `CONTESTED` | Local rule-based classifier accuracy |
| `test_stance_detector_antonym_contradiction` | Directional antonym detection (e.g. east vs. west) | `stance == "CONTRADICTS"`, `conf >= 85.0` |
| `test_evidence_reranker_with_stances` | Evidence sorting prioritized by contradiction/entailment | Top reranked item marked with stance |
| `test_two_dimensional_verdict_sun_rises_from_west` | Validates independent 2D verdict representation | `truth_value == "False"`, `knowledge_certainty == "Settled Knowledge"` |
| `test_two_dimensional_verdict_sun_rises_from_east` | Validates independent 2D verdict representation | `truth_value == "True"`, `knowledge_certainty == "Settled Knowledge"` |
| `test_clause_level_consistency_guard_rail_overrides_true` | Guard rail: Debunked clause prevents overall True verdict | Overrides to `False` |
| `test_quick_summary_360_briefing_structure` | Validates all 8 sub-sections of 360° Incident Briefing | `what_happened`, `full_context`, `timeline`, `key_parties`, `key_data`, `perspectives`, `current_status`, `key_takeaway` |
| `test_source_type_classification_tiers` | Categorizes sources into 5 standard tiers | `[🟢 Primary Source]`, `[🔵 Major News Outlet]`, `[🟡 Fact-Checker]`, `[🟠 Domain Expert / Academic]`, `[⚪ Other / General]` |
| `test_settled_fact_sources_and_further_reading` | Validates authoritative references attached to settled facts | $\ge 2$ sources with URLs, publication dates, and tiers |
| `test_tri_mode_input_classification` | Validates Mode A (Claim), Mode B (Event Query), Mode C (Hybrid) | Accurate classification across diverse queries |
| `test_event_category_detection` | Emojis and labels for event categories | Flooding (🌊), Earthquake (🌋), Armed Conflict (🌍) |
| `test_mode_b_event_query_endpoint_structure` | Validates Mode B structured payload | `mode == "Event Query"`, `event_meta`, structured `impact_numbers` |

---

## 4. Test Fixtures & State Management

### 4.1 In-Memory Database Fixture (`test_credibility.py`)
Provides complete database isolation per test function:
```python
@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    session.add(PublisherCredibility(domain="reuters.com", ...))
    session.add(PublisherCredibility(domain="infowars.com", ...))
    session.commit()
    yield session
    session.close()
```

### 4.2 Session-Scoped Pipeline Database Fixture (`test_verification_pipeline.py`)
Initializes and seeds the main test database once per test session:
```python
@pytest.fixture(scope="session", autouse=True)
def init_test_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    yield
```

### 4.3 HTTP Testing Client
The FastAPI application is tested using Starlette's synchronous `TestClient`:
```python
client = TestClient(app)
response = client.post("/api/verify", json=payload)
```
- Requests execute in-process without spawning external sockets.
- Async endpoints are resolved seamlessly through the ASGI test adapter.

### 4.4 Async Execution in Synchronous Tests
When unit-testing async service methods (e.g. `GeminiRateLimiter.execute_with_retry` or `GeminiRateLimiter.acquire`), tests use `asyncio.run(...)`:
```python
def test_rate_limiter_inter_call_spacing():
    async def run_limiter_test():
        start = asyncio.get_event_loop().time()
        await GeminiRateLimiter.acquire()
        await GeminiRateLimiter.acquire()
        duration = asyncio.get_event_loop().time() - start
        assert duration >= 0.4

    asyncio.run(run_limiter_test())
```

---

## 5. Mocking Patterns & Deterministic Execution

### 5.1 Settled Facts Local Catalog
The test suite utilizes TruthLens's local catalog of established knowledge (`SETTLED_FACT_PATTERNS` and `SETTLED_CONTRADICTION_PATTERNS` in `factcheck_service.py`). This allows end-to-end integration tests to execute through the full pipeline without relying on external network requests or burning Gemini quota.

### 5.2 Deterministic Synthesis Fallback
When external API keys are not provided or tests run offline:
- `GeminiSynthesisService.execute_unified_evaluation` cleanly returns `{"success": False, "reason": "No API key configured."}`.
- `SynthesisService.synthesize` catches this and smoothly falls back to local deterministic synthesis based on extracted evidence, stance labels, and pattern heuristics.
- All pipeline assertions continue to pass deterministically.

---

## 6. Coverage Analysis & Testing Opportunities

### 6.1 Backend Strengths
- **Exhaustive Pipeline Testing**: The 26 tests in `test_verification_pipeline.py` comprehensively cover settled facts, contradictions, 2D verdict calculations, rate limiter locks, budget enforcement, and 360° summary structure.
- **Edge Case Coverage**: Unverified claims are explicitly checked to prevent inflated confidence scores ($>45\%$).
- **Regression Locking**: Specific tests exist for previously addressed bugs (e.g. single Gemini call budget, 404/401 fast-fail).

### 6.2 Identified Gaps & Recommendations

1. **External API Mock Isolation**:
   - *Current State*: External web search calls (`GoogleSearchService.search_live_web`) and fact check calls execute against live open web endpoints or fall back to empty evidence when offline.
   - *Recommendation*: Introduce `unittest.mock` / `pytest-mock` patches for `httpx.AsyncClient` to mock exact HTTP responses for Google Custom Search and Google Fact Check Tools API under varying network conditions.

2. **Frontend Unit & Component Testing**:
   - *Current State*: `frontend/package.json` does not configure a test runner (no Vitest, Jest, or React Testing Library). Verification currently relies on `tsc && vite build`.
   - *Recommendation*: Install `vitest`, `@testing-library/react`, and `@testing-library/jest-dom` to test rendering of `VerdictCard`, radial `ConfidenceMeter`, and modal interactions.

3. **Chrome Extension Automation**:
   - *Current State*: Extension functionality is verified manually by unpacking into Chromium.
   - *Recommendation*: Add end-to-end headless browser testing (e.g. via Playwright) to test context menu selection and content script badge injection.

---

## 7. Test Execution Commands & Procedures

### 7.1 Running Tests Locally

```bash
# Execute entire test suite from project root
python -m pytest

# Verbose execution showing individual test names
python -m pytest -v

# Run a specific test module
python -m pytest backend/tests/test_verification_pipeline.py

# Run only fast, local rule-based unit tests
python -m pytest backend/tests/test_extractor.py backend/tests/test_pattern_analyzer.py backend/tests/test_credibility.py

# Run tests matching a specific expression (e.g., settled facts)
python -m pytest -k "settled_fact"

# Run tests showing stdout print statements
python -m pytest -s
```

### 7.2 Build Verification & Type Safety

```bash
# Frontend type check & production build verification
cd frontend
npm.cmd run build
```
