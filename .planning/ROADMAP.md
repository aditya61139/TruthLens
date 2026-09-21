# TruthLens Project Roadmap

## Milestone: v1.1 Refactor, Modernize & Humanize

### Phase 1: Stability, Security & Pruning Technical Debt
**Focus**: Resolve existing runtime bugs, unify database/config paths, patch security vulnerabilities, and prune fragile scrapers.
- [ ] Task 1.1: Unify SQLite database to single root `truthlens.db` and enable WAL mode (`CLEAN-01`).
- [ ] Task 1.2: Consolidate `.env` resolution and prune duplicated environment files (`CLEAN-02`).
- [ ] Task 1.3: Fix ccTLD domain parsing bug in `PublisherCredibilityService` (`CLEAN-05`).
- [ ] Task 1.4: Replace deprecated `datetime.utcnow()` with `datetime.now(timezone.utc)` (`CLEAN-06`).
- [ ] Task 1.5: Remove brittle DuckDuckGo HTML scraping and remove fabricated 98.4% mock stat (`CLEAN-03`, `CLEAN-04`).
- [ ] Task 1.6: Secure CORS configuration and restrict config mutation endpoints (`SEC-01`).
- [ ] Task 1.7: Add SSRF protection in URL extraction (`SEC-02`) and input length bounds (`SEC-04`).
- [ ] Task 1.8: Run backend pytest suite to verify all fixes pass cleanly.

### Phase 2: Humanizing Verdicts & Plain English Synthesis
**Focus**: Transform robotic ratings and error tracebacks into empathetic, natural, intuitive briefings.
- [ ] Task 2.1: Revamp synthesis prompts in `gemini_service.py` and `synthesis_service.py` to produce a conversational "TL;DR in Plain English" (`HUMAN-01`, `ENH-01`).
- [ ] Task 2.2: Upgrade heuristic fallback synthesis to generate human-readable, objective explanations when offline or unauthenticated (`HUMAN-01`).
- [ ] Task 2.3: Humanize user-facing error messages, rate limit notifications, and offline banners (`HUMAN-02`).
- [ ] Task 2.4: Refactor service code for clean documentation and readability (`HUMAN-03`).
- [ ] Task 2.5: Verify humanized verdict generation with unit and pipeline tests.

### Phase 3: Visual Palette & UI Modernization ("Midnight Slate & Trust Emerald")
**Focus**: Redesign the UI to reflect a credible, modern journalism and intelligence dashboard.
- [ ] Task 3.1: Update Tailwind configuration and root styles for the Midnight Slate & Trust Emerald palette (`PAL-01`).
- [ ] Task 3.2: Redesign `VerdictCard.tsx` with refined verdict badges, crisp glassmorphic surfaces, and clear visual hierarchy (`PAL-02`).
- [ ] Task 3.3: Modernize `ConfidenceMeter.tsx` with smooth emerald/amber/crimson progress bars and confidence descriptions (`PAL-02`).
- [ ] Task 3.4: Polish navigation header, status indicators, and modal dialogues (`PAL-03`).
- [ ] Task 3.5: Update `ShareableCard.tsx` export styling for high-definition social cards (`PAL-02`).
- [ ] Task 3.6: Test and verify frontend build (`npm run build`).

### Phase 4: Chrome Extension Security & End-to-End Verification
**Focus**: Harden the Chrome extension against XSS and conduct full-system validation.
- [ ] Task 4.1: Secure `extension/content.js` to eliminate raw `innerHTML` interpolation and sanitize DOM nodes (`SEC-03`).
- [ ] Task 4.2: Update extension popup styling to align with the Midnight Slate & Trust Emerald theme.
- [ ] Task 4.3: Add automated tests for SSRF validation, ccTLD parsing, and rate-limiting fallbacks.
- [ ] Task 4.4: Conduct end-to-end verification across backend, web app, and extension.
