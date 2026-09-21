# TruthLens — Project Context & Vision

## 1. Executive Summary
**TruthLens** is an AI-powered verification platform that detects misinformation, debunks viral claims, and provides transparent, evidence-backed fact-checking in real time.

This project lifecycle focuses on:
1. **Humanizing the Code & User Experience**: Writing clean, idiomatic, empathetic code and crafting human-friendly, jargon-free verdict explanations.
2. **Eliminating Fragility & Resolving Errors**: Unifying dual-database and dual-`.env` path drift, fixing ccTLD domain parsing, resolving deprecation warnings, and securing vulnerable endpoints.
3. **Redesigning the Visual Identity**: Implementing the **Midnight Slate & Trust Emerald** color palette (`#0b0f19`, `#111827`, `#10b981`, `#f59e0b`, `#ef4444`) with high-legibility typography and subtle glassmorphic styling.
4. **Pruning Risky & Dead Features**: Removing brittle DuckDuckGo HTML scraping, eliminating fabricated mock statistics (e.g., 98.4% fake user satisfaction), and tightening security (SSRF prevention, CORS, and extension XSS prevention).
5. **Robust Feature Enhancements**: Adding clear plain-English "Why This Matters" summaries, structured source credibility badges, and deterministic fallback resilience when external API keys are unavailable.

---

## 2. Core Themes & Target Architecture

### Humanization & UX Copy
- **From**: Mechanical/robotic outputs like `"STANCE: CONTRADICTS with similarity score 0.72"`.
- **To**: Intuitive, conversational briefings: *"This claim is contradicted by official findings from Reuters and the WHO. Here is what actually happened..."*
- **Code Quality**: Readable, self-documenting service layers, typed interfaces, unified error handling, and helpful debug logs.

### Visual Aesthetic — Midnight Slate & Trust Emerald
- **Base Background**: Deep midnight slate (`#0b0f19` to `#111827`) with dark slate card surfaces (`#1e293b` / `#0f172a`).
- **Verdict Accents**:
  - **Verified / True**: Trust Emerald (`#10b981` / `#059669`).
  - **Misleading / Mixed**: Warning Amber (`#f59e0b` / `#d97706`).
  - **False / Fabricated**: Alert Crimson (`#ef4444` / `#dc2626`).
  - **Unverified / Satire**: Neutral Indigo/Violet (`#6366f1` / `#8b5cf6`).
- **Typography & Polish**: Inter/system font stack, high-contrast text hierarchy, refined glass cards with subtle borders (`rgba(255, 255, 255, 0.08)`).

### Stability & Security Architecture
- **Single Source of Truth Database**: Unified SQLite database location with WAL mode enabled for smooth concurrent access.
- **Single `.env` Root Configuration**: Deterministic environment loading across all run scripts and services.
- **Defensive Networking**: SSRF validation with private/loopback IP blocking for URL verification; graceful fallback when external search APIs reach quota limits.
- **Secure Browser Extension**: Entity-encoded or DOM-node constructed popups preventing arbitrary script execution on host pages.

---

## 3. Technology Stack Reference
- **Backend**: Python 3.10+, FastAPI, SQLAlchemy 2.0, SQLite (WAL mode), Pydantic v2, RapidFuzz, `google-genai` SDK.
- **Frontend**: Vite 5, React 18, TypeScript 5, Tailwind CSS 3.4, Lucide React, `html-to-image`.
- **Extension**: Chrome Extension Manifest V3 (Service Worker + Content Script + Popup).
