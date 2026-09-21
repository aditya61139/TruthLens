# Phase 1 Plan: Stability, Security & Pruning Technical Debt

## Objective
Harden the TruthLens backend against security vulnerabilities, eliminate path ambiguities (database and `.env`), resolve deprecations, remove fragile scraping/mock metrics, and ensure 100% clean test execution.

---

## Tasks & Specifications

### 1. Database Unification & SQLite WAL Concurrency (`CLEAN-01`)
- **Files**: [`backend/app/core/config.py`](file:///p:/TruthLens/backend/app/core/config.py), [`backend/app/db/database.py`](file:///p:/TruthLens/backend/app/db/database.py)
- **Changes**:
  - Normalize database path using `BASE_DIR.as_posix()` so Windows slashes don't cause URI parsing issues.
  - Enable SQLite Write-Ahead Logging (`PRAGMA journal_mode=WAL;`), synchronous NORMAL mode (`PRAGMA synchronous=NORMAL;`), and busy timeout (`PRAGMA busy_timeout=5000;`) via SQLAlchemy connection event hooks.
  - Ensure single canonical database at `P:\TruthLens\truthlens.db`.

### 2. Unified Environment & Config Resolution (`CLEAN-02`)
- **Files**: [`backend/app/core/config.py`](file:///p:/TruthLens/backend/app/core/config.py), [`backend/app/api/routes_config.py`](file:///p:/TruthLens/backend/app/api/routes_config.py)
- **Changes**:
  - Explicitly set `SettingsConfigDict(env_file=str(BASE_DIR / ".env"), extra="allow")` so working directory changes never load different `.env` files.
  - Delete any remaining `backend/.env` file.

### 3. Fix ccTLD Subdomain Parsing Bug (`CLEAN-05`)
- **Files**: [`backend/app/services/credibility_service.py`](file:///p:/TruthLens/backend/app/services/credibility_service.py)
- **Changes**:
  - Replace rigid `parts[-2:]` logic with progressive subdomain stripping loop (`for i in range(1, len(parts) - 1)`).
  - Enables proper resolution for domains with multi-part ccTLDs such as `bbc.co.uk`, `theguardian.co.uk`, etc.

### 4. Resolve Python 3.12+ `datetime.utcnow()` Deprecations (`CLEAN-06`)
- **Files**:
  - [`backend/app/db/models.py`](file:///p:/TruthLens/backend/app/db/models.py)
  - [`backend/app/api/routes_verify.py`](file:///p:/TruthLens/backend/app/api/routes_verify.py)
  - [`backend/app/api/routes_feedback.py`](file:///p:/TruthLens/backend/app/api/routes_feedback.py)
  - [`backend/app/services/cache_service.py`](file:///p:/TruthLens/backend/app/services/cache_service.py)
  - [`backend/app/db/seed_data.py`](file:///p:/TruthLens/backend/app/db/seed_data.py)
- **Changes**:
  - Replace `datetime.datetime.utcnow()` with `datetime.datetime.now(datetime.timezone.utc)`.

### 5. Prune Fragile Scraping & Mock Statistics (`CLEAN-03`, `CLEAN-04`)
- **Files**: [`backend/app/services/google_search_service.py`](file:///p:/TruthLens/backend/app/services/google_search_service.py), [`backend/app/api/routes_feedback.py`](file:///p:/TruthLens/backend/app/api/routes_feedback.py)
- **Changes**:
  - Deprecate/remove brittle DuckDuckGo HTML scraping in `search_open_web`. Gracefully route requests through Google Search / Google News RSS feeds to avoid CAPTCHA blocks and silent 403 crashes.
  - Remove hardcoded 98.4% user satisfaction rate in `routes_feedback.py`. Return `None` when no feedback exists, paired with `total_feedback: 0`.

### 6. Secure CORS and Config Endpoints (`SEC-01`)
- **Files**: [`backend/app/main.py`](file:///p:/TruthLens/backend/app/main.py), [`backend/app/api/routes_config.py`](file:///p:/TruthLens/backend/app/api/routes_config.py)
- **Changes**:
  - Fix CORS conflict: disallow `allow_origins=["*"]` with `allow_credentials=True`. Use regex matching localhost, local IP, and chrome-extension origins.
  - Add localhost check (`request.client.host in ("127.0.0.1", "::1", "localhost")`) and key length validation to `POST /api/config/set-key` to prevent arbitrary external websites from hijacking server API keys.

### 7. SSRF Protection & Bounded Schemas (`SEC-02`, `SEC-04`)
- **Files**: [`backend/app/services/extractor.py`](file:///p:/TruthLens/backend/app/services/extractor.py), [`backend/app/api/routes_verify.py`](file:///p:/TruthLens/backend/app/api/routes_verify.py), [`backend/app/api/routes_feedback.py`](file:///p:/TruthLens/backend/app/api/routes_feedback.py)
- **Changes**:
  - Implement IP resolution and private/loopback/cloud metadata check in `ClaimExtractor.extract_from_url`. Block `127.0.0.0/8`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `169.254.169.254`, and IPv6 loopback/link-local.
  - Add Pydantic `Field(..., max_length=...)` bounds to `VerifyRequest`, `ArticleVerifyRequest`, and `FeedbackRequest`.

### 8. Verification & Test Suite (`VERIFY`)
- Run `python -m pytest` on backend to ensure all 43+ tests pass.
- Add test coverage for SSRF blocking, ccTLD domain matching, and bounded payload validation.
