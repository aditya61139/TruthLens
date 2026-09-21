# TruthLens Requirements Specification

## 1. Humanizing Code & User Experience (HUMAN)
- [ ] **HUMAN-01**: **Conversational Verdict Explanations** — Refactor synthesis prompts and fallback generators so claim verdicts provide clear, natural, objective "Plain English" explanations without robotic jargon.
- [ ] **HUMAN-02**: **Helpful, Empathetic Error Messaging** — Replace raw exceptions, cryptic codes, and silent failures with clear, user-friendly error banners (e.g. when network is down, API quota is exceeded, or no sources are found).
- [ ] **HUMAN-03**: **Idiomatic & Readable Codebase** — Refactor backend services and frontend components to adhere to clean code principles, clear naming conventions, and intuitive abstraction layers.

## 2. Visual Palette & UI Design (PALETTE)
- [ ] **PAL-01**: **Midnight Slate & Trust Emerald Theme** — Update Tailwind configuration, CSS root variables, and component stylesheets with the refined palette:
  - Deep Midnight Slate background (`#0b0f19` / `#111827`)
  - Crisp Card Surfaces (`#1e293b` / `#0f172a`) with subtle glass borders
  - Trust Emerald (`#10b981`) for True/Verified claims
  - Warning Amber (`#f59e0b`) for Misleading/Questionable claims
  - Alert Crimson (`#ef4444`) for False/Debunked claims
  - Modern Accent Indigo (`#6366f1`) for Unverified/Satire claims
- [ ] **PAL-02**: **Verdict & Meter Polish** — Redesign [`VerdictCard.tsx`](file:///p:/TruthLens/frontend/src/components/VerdictCard.tsx), [`ConfidenceMeter.tsx`](file:///p:/TruthLens/frontend/src/components/ConfidenceMeter.tsx), and [`ShareableCard.tsx`](file:///p:/TruthLens/frontend/src/components/ShareableCard.tsx) to match the new palette with elegant contrast and smooth animations.
- [ ] **PAL-03**: **Navigation & Modal Modernization** — Update Header, API Key modal, and Quick Summary briefings for consistent typography, modern spacing, and clean iconography.

## 3. Error Resolution, Bug Fixes & Code Pruning (CLEANUP)
- [ ] **CLEAN-01**: **Single Database Path** — Unify database location to root `truthlens.db`, eliminate dual-db confusion, and enable SQLite WAL mode (`PRAGMA journal_mode=WAL; PRAGMA busy_timeout=5000;`).
- [ ] **CLEAN-02**: **Unified Configuration & .env** — Consolidate configuration loading to point reliably to a single `.env` file at the project root.
- [ ] **CLEAN-03**: **Prune Brittle DuckDuckGo HTML Scraper** — Remove the fragile regex/HTML scraper from `google_search_service.py` that frequently triggers CAPTCHAs/403s; standardize on Google Search Grounding and resilient structured fallbacks.
- [ ] **CLEAN-04**: **Remove Fabricated Statistics** — Remove hardcoded mock 98.4% user satisfaction metric from `routes_feedback.py`; show actual feedback statistics or an honest zero-state.
- [ ] **CLEAN-05**: **Fix ccTLD Subdomain Parsing** — Correct domain splitting logic in `credibility_service.py` so multi-part TLDs (e.g. `bbc.co.uk`, `theguardian.co.uk`) match correctly in the 250+ publisher database.
- [ ] **CLEAN-06**: **Resolve Python Deprecations** — Replace deprecated `datetime.utcnow()` with `datetime.now(timezone.utc)` across models, routes, and services.

## 4. Security Hardening (SECURITY)
- [ ] **SEC-01**: **Lock Down Config & CORS** — Restrict `POST /api/config/set-key` to local origin or authenticated requests, and correct CORS middleware settings to adhere to standard browser security policies.
- [ ] **SEC-02**: **SSRF Protection on URL Ingestion** — Validate target IP addresses in `ClaimExtractor.extract_from_url` to disallow private (`10.0.0.0/8`, `192.168.0.0/16`, `127.0.0.0/8`) and cloud metadata (`169.254.169.254`) IP spaces.
- [ ] **SEC-03**: **Extension XSS Prevention** — Sanitize and safely inject verdict text using DOM textContent / template elements in `extension/content.js` instead of vulnerable raw `innerHTML` interpolation.
- [ ] **SEC-04**: **Bounded Input Schemas** — Add `max_length` bounds on Pydantic request models (`VerifyRequest`, `FeedbackRequest`) to guard against oversized payloads.

## 5. Feature & Architecture Enhancements (ENHANCE)
- [ ] **ENH-01**: **"Plain English TL;DR" Verdict Block** — Display a prominent, easily digestible summary highlighting the core truth status, why it was rated that way, and key factual citations.
- [ ] **ENH-02**: **Dynamic Fallback Indicator** — When external Google APIs are inactive or out of quota, clearly notify the user that offline verification / heuristic consensus is active.
- [ ] **ENH-03**: **Automated Test Validation** — Expand backend test coverage to verify the unified database, SSRF guards, ccTLD parsing, and run frontend build checks.
