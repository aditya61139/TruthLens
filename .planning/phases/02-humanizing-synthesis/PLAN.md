# Phase 2 Plan: Humanizing Verdicts & Plain English Synthesis

## Objective
Transform robotic ratings, formulaic summaries, and technical error messages into warm, empathetic, intuitive, and human-friendly journalistic briefings. Upgrade both the Gemini AI prompts and the offline heuristic synthesis engine so that verdicts are immediately clear to everyday users.

---

## Tasks & Specifications

### 1. Humanized Gemini Prompting (`HUMAN-01`, `ENH-01`)
- **Files**: [`backend/app/services/gemini_service.py`](file:///p:/TruthLens/backend/app/services/gemini_service.py)
- **Changes**:
  - Update system and user prompts to instruct Gemini to write in clear, objective, plain English (style of Reuters / AP fact-checkers).
  - Explicitly forbid robotic AI jargon ("As an AI...", "STANCE: CONTRADICTS with similarity score...", "The retrieved evidence indicates...").
  - Require a dedicated `plain_english_takeaway` (1-2 punchy sentences summarizing the bottom line) and structured `key_evidence_bullets` in the JSON response.
  - Require conversational explanations in `quick_summary.what_happened` and `quick_summary.full_context`.

### 2. Upgraded Heuristic Fallback Synthesis (`HUMAN-01`, `ENH-01`)
- **Files**: [`backend/app/services/synthesis_service.py`](file:///p:/TruthLens/backend/app/services/synthesis_service.py)
- **Changes**:
  - Replace dry, repetitive template strings (`"Current reporting and factual records from {top_str} assess this claim as {truth_value.upper()}"`) with natural, varied, human-crafted explanations:
    - **True**: *"Accredited news and reference documentation confirm that this claim is accurate. Reports from {top_sources} corroborate the core facts."*
    - **False**: *"This claim is false. Verified reporting and primary documentation from {top_sources} directly contradict this assertion. There is no factual evidence supporting it."*
    - **Misleading**: *"This claim is misleading. While it may touch upon a real event or factual element, key context has been omitted or distorted, leading to a false impression."*
    - **Satire**: *"This content originated from a known satirical comedy source and was never intended as genuine news."*
    - **Unverified**: *"This claim is currently unverified. Neither accredited fact-checkers nor major news outlets have confirmed or debunked it yet."*
  - Enrich `explanation` dictionary with `plain_english_takeaway` and `takeaway` fields.
  - Upgrade `generate_360_briefing` to generate fluid, conversational paragraphs rather than mechanical fill-in-the-blank sentences.

### 3. Empathetic & Helpful Error Messaging (`HUMAN-02`)
- **Files**:
  - [`backend/app/services/gemini_rate_limiter.py`](file:///p:/TruthLens/backend/app/services/gemini_rate_limiter.py)
  - [`backend/app/services/synthesis_service.py`](file:///p:/TruthLens/backend/app/services/synthesis_service.py)
  - [`backend/app/api/routes_verify.py`](file:///p:/TruthLens/backend/app/api/routes_verify.py)
- **Changes**:
  - Rate Limiting / Quota Exhaustion: Instead of scary error tracebacks, inform the user: *"We're experiencing high verification volume right now. TruthLens has verified your claim using our local fact-checking consensus and verified news databases."*
  - Unreachable / Paywalled URL: *"We couldn't access this webpage. It may be paywalled, require a login, or be temporarily unavailable. You can copy and paste the article text directly into TruthLens."*
  - Missing Input: *"Please enter a statement, news headline, or article link to begin verification."*

### 4. Frontend Integration & "Plain English TL;DR" Display (`ENH-01`)
- **Files**:
  - [`frontend/src/components/VerdictCard.tsx`](file:///p:/TruthLens/frontend/src/components/VerdictCard.tsx)
  - [`frontend/src/components/QuickSummaryBriefing.tsx`](file:///p:/TruthLens/frontend/src/components/QuickSummaryBriefing.tsx)
  - [`frontend/src/types/index.ts`](file:///p:/TruthLens/frontend/src/types/index.ts)
- **Changes**:
  - Update `Explanation` TypeScript interface to include `plain_english_takeaway?: string`.
  - Add a dedicated, highly readable **"Plain English Takeaway"** callout box directly below the verdict in `VerdictCard.tsx`.
  - Ensure fallback warnings and informational banners use friendly, reassuring language.

### 5. Automated Tests & Verification (`VERIFY`)
- **Files**: [`backend/tests/test_humanized_synthesis.py`](file:///p:/TruthLens/backend/tests/test_humanized_synthesis.py)
- **Changes**:
  - Verify that both Gemini and local deterministic fallbacks produce non-empty, conversational `plain_english_takeaway` and humanized `summary` strings without robotic phrases.
  - Verify helpful error handling for empty inputs and paywalled URLs.
  - Run `python -m pytest` and `npm run build`.
