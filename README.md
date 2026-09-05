# TruthLens — AI-Powered Fake News & Misinformation Detection System

TruthLens is a production-grade AI verification system that detects fake news, debunks viral misinformation, and checks factual claims in real time. It combines transparent evidence trails from accredited fact-checkers with local linguistic pattern heuristics and publisher credibility ratings.

---

## 🔑 API Keys & Real-Time Google Web Search

TruthLens works out of the box with built-in heuristics, local datasets, and news aggregation. To enable **real-time Google Web Search Grounding** and **Google Fact Check Tools API**:

### Option A: Set via `.env` file
Add your key to `P:\TruthLens\.env` or `P:\TruthLens\backend\.env`:
```env
# Universal Google API Key (from Google AI Studio: https://aistudio.google.com/app/apikey)
GOOGLE_API_KEY=your_google_api_key_here

# (Optional specific overrides)
GOOGLE_FACTCHECK_API_KEY=your_factcheck_key
GOOGLE_SEARCH_API_KEY=your_custom_search_key
GOOGLE_SEARCH_ENGINE_ID=your_custom_search_engine_id
```

### Option B: 1-Click via the Web Dashboard
1. Open the TruthLens UI at `http://localhost:5173`.
2. Click the **"Google API Keys"** button in the top navigation bar.
3. Paste your Google API Key and click **"Activate Key"** — live Google Search Grounding and Gemini Synthesis activate immediately!

---

## 🌟 Key Features

1. **Multi-Layer Fact Verification Engine**:
   - **Google Search Grounding**: Performs live Google Web Search to fetch real-time web facts and citations for breaking events.
   - **Google Fact Check Tools API**: Queries indexed fact checks across Snopes, PolitiFact, Reuters, AFP, FactCheck.org, WHO.
   - **Settled Knowledge Tier**: Automatically identifies universal scientific, geographic, and astronomical facts (e.g. *"sun rises in the east"*, *"water boils at 100°C"*).
   - **Strict Semantic Relevance Filtering**: Discards loose keyword matches and prevents padding with unrelated news stories.
   - **Fuzzy SQLite Cache (`rapidfuzz`)**: Re-running identical or near-duplicate queries ($>85\%$ token similarity) resolves in $<5$ms without making external network calls.

2. **Transparent Evidence Trail**:
   - Color-coded verdict banner: `True`, `False`, `Misleading`, `Unverified`, `Satire`.
   - Separate multi-factor **Confidence Meter** (0–100%).
   - Clickable source citations with publisher name, original rating, and publication date.

3. **Misinformation Pattern & Red Flag NLP**:
   - Rule-based detection of clickbait phrasing, emotional/outrage manipulation, missing source attribution, fabricated statistics, and conspiracy tropes.
   - Itemized checklist with detected trigger words and severity levels.

4. **Publisher Credibility Index**:
   - Curated reference database of 250+ media organizations with bias ratings, factual reporting tiers, and trust scores.

5. **Article / Batch Mode**:
   - Paste a multi-paragraph article or URL to extract all checkable claims, verify each in parallel, and calculate an aggregate **Article Trust Score (0–100)**.

6. **Trending Misinformation & Analytics**:
   - Live dashboard of viral hoaxes and claims monitored across health, science, tech, and politics.

7. **Shareable Verdict Cards**:
   - Export branded, high-resolution PNG verdict cards or copy card images directly for social media sharing.

8. **Chrome Browser Extension (Manifest V3)**:
   - Highlight text on any website $\rightarrow$ Right-click $\rightarrow$ **"Verify with TruthLens"** for an instant inline badge.

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10+
- Node.js 18+ and npm

### 2. Backend Setup
```bash
# In the root directory:
cd backend
python -m pip install -r requirements.txt

# Run the FastAPI server:
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
- API Documentation available at: `http://localhost:8000/docs`

### 3. Frontend Setup
```bash
# In a separate terminal:
cd frontend
npm.cmd install
npm.cmd run dev
```
- Web Application available at: `http://localhost:5173`

### 4. Running Backend Tests
```bash
python -m pytest
```

---

## 🧩 Architecture

```
TruthLens
├── backend/
│   ├── app/
│   │   ├── api/             # REST endpoints (verify, article, sources, history, feedback)
│   │   ├── core/            # Configuration & settings
│   │   ├── db/              # SQLAlchemy models, SQLite session, 250+ seed records
│   │   ├── services/        # Extractor, FactCheck, News, PatternAnalyzer, Credibility, Synthesis, Cache
│   │   └── main.py          # FastAPI application
│   ├── tests/               # 18 automated unit and pipeline tests
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/      # ClaimInput, VerdictCard, ConfidenceMeter, Explainability, RedFlags, ShareableCard, ArticleMode, Trending, Sources
│   │   ├── api/             # Typed API client
│   │   ├── types/           # Full TypeScript data models
│   │   └── App.tsx
│   └── package.json
└── extension/               # Manifest V3 Chrome Extension (popup, background, content scripts)
```
