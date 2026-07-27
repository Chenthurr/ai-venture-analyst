# AI Venture Analyst

An AI-powered startup investment analysis platform. Upload a company's pitch deck,
financials, and market research; get back a grounded, cited investment memo,
SWOT analysis, ten-category investment scoring, a twelve-factor risk profile,
and a valuation estimate computed with five standard VC methodologies —
all backed by real, unit-tested financial math and retrieval-grounded AI
generation, not a black box.

This is not a chatbot wrapper. It's a real full-stack application: a FastAPI
backend with its own financial and valuation engines, a document parsing +
hybrid-search RAG pipeline, and a Next.js frontend styled like an investment
committee's working memo rather than a generic SaaS dashboard.

> **Honest scope note.** This is a deliberately-scoped first increment of a much
> larger original spec (12-agent LangGraph orchestration, Qdrant vector DB,
> Celery workers, Power BI export, PDF/PPTX/DOCX report generation, and more).
> See [Roadmap](#roadmap--future-enhancements) for what's next and why this
> slice was chosen first. Every module described above as "done" has been
> run end-to-end and its financial formulas unit-tested — nothing here is a
> placeholder.

---

## Table of Contents
- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [API Documentation](#api-documentation)
- [Financial & Valuation Methodology](#financial--valuation-methodology)
- [Testing](#testing)
- [Screenshots](#screenshots)
- [Roadmap / Future Enhancements](#roadmap--future-enhancements)

---

## Features

### Startup Workspace
- Multi-tenant accounts (JWT auth), each user manages multiple startup projects
- Structured company profile: name, industry, country, stage, founders, one-liner

### Document Intelligence
- Upload PDF, PPTX, XLSX, CSV, TXT, Markdown
- **Real extraction** per format: `pypdf` for PDF text, `python-pptx` for slide
  text + tables, `openpyxl` for spreadsheet data, `csv`/text for the rest
- Automatic chunking + OpenAI embeddings for every uploaded document
- **Hybrid search** at query time: dense (cosine similarity over embeddings)
  blended with a BM25-style sparse keyword score — implemented from scratch,
  no external vector DB required for this scale

### AI Investment Analysis
- One retrieval-grounded LLM call per analysis run, returning structured JSON:
  - Executive summary
  - SWOT analysis
  - 10-category investment scoring (founder strength, market size, product
    quality, traction, competition, financial health, business model,
    technology, scalability, investment readiness) — each with a 0–100 score
    and cited reasoning
  - 12-category risk scoring (management, stage, legal/political,
    manufacturing, sales & marketing, funding, competition, technology,
    litigation, international, reputation, exit value)
  - A full multi-section investment memo (Overview, Market Analysis, Team,
    Product, Competitive Landscape, Financials, Risks, Funding Recommendation)
- Every claim is required (by the prompt contract) to reference a numbered
  source excerpt; citations are resolved back to the originating document
  and chunk before being returned to the client
- **AI chat**: ask free-form questions ("Should I invest?", "How can CAC
  improve?", "Generate a due diligence checklist") and get answers grounded
  in that project's own documents, with citations

### Financial Engine (real, unit-tested formulas)
Gross margin, net margin, net burn rate, cash runway, CAC, LTV, LTV:CAC ratio,
CAC payback period, EBITDA, break-even units/revenue, contribution margin,
monthly churn rate, annualized revenue run rate.

### Valuation Engine (five real methodologies)
1. **Scorecard Method** — stage-comparable base valuation adjusted by
   weighted, AI-derived factor ratios (Bill Payne weightings)
2. **Berkus Method** — up to $500k per qualitative risk-reduction factor,
   capped at $2.5M, for pre-/early-revenue companies
3. **VC Method** — terminal value from projected exit-year ARR × exit
   multiple, divided by anticipated ROI, minus investment requested
4. **Discounted Cash Flow** — multi-year free cash flow projection with
   operating-leverage opex assumptions, discounted at a configurable rate,
   plus a Gordon Growth terminal value
5. **Risk Factor Summation** — stage base valuation adjusted ±$250k per
   risk category, rated -2 to +2 from the AI's risk scores

All five are computed and shown side by side with full calculation
breakdowns, plus a blended estimate.

### Dashboard
- Conviction Gauge (this app's signature visual): a semi-circle dial showing
  overall investment conviction from the ten score categories
- SWOT matrix, investment score bars with cited reasoning on hover, a risk
  radar chart, a valuation bar chart with expandable per-method detail, and
  a full financial metrics panel
- **Portfolio-wide summary** (`GET /api/dashboard/summary`): aggregates every
  project a user owns into a single view — total companies, stage breakdown,
  average conviction score, total blended valuation, total monthly burn
  across the portfolio, and a cross-company risk heatmap

### Reports (real, downloadable PDFs)
Generated with reportlab (actual styled tables and page layout, not an
HTML-to-image hack):
- **Investment Memo** — full memo with scores, SWOT, financials, valuation,
  risk profile, narrative, and cited sources
- **Board Report** — leads with financial performance and risk
- **Investor Report** — leads with valuation and investment scores
- **Due Diligence Checklist** — a standard early-stage VC checklist
  (Corporate & Legal, Financial, Team & HR, Product & Technology, Market &
  Commercial, Cap Table) generated without requiring an AI analysis run first

---

## Architecture

```
┌─────────────────┐        ┌──────────────────┐        ┌─────────────────┐
│   Next.js 15     │◄──────►│    FastAPI       │◄──────►│   PostgreSQL     │
│   (React, TS,    │  REST  │  (Python 3.12)   │  SQL   │                  │
│   Tailwind,      │        │                  │        │  Users           │
│   Recharts,      │        │  routers/        │        │  Projects        │
│   React Query,   │        │   auth           │        │  Documents       │
│   Zustand)       │        │   projects       │        │  DocumentChunks  │
└─────────────────┘        │   documents      │        │  FinancialSnaps  │
                            │   financials     │        │  AnalysisReports │
                            │   analysis       │        └─────────────────┘
                            │                  │
                            │  services/       │        ┌─────────────────┐
                            │   document_parser│───────►│  Local disk      │
                            │   embeddings     │        │  (uploads/)      │
                            │   ai_analysis    │        └─────────────────┘
                            │   financial_eng  │
                            │   valuation      │        ┌─────────────────┐
                            └────────┬─────────┘───────►│  OpenAI API      │
                                     │                   │  (chat +        │
                                     │                   │   embeddings)    │
                                     ▼                   └─────────────────┘
                            nginx reverse proxy
                            (routes /api → backend,
                             / → frontend)
```

### RAG / Retrieval Pipeline
```
Upload → detect type → parse (pypdf / python-pptx / openpyxl / csv)
       → chunk (sliding window, char-based, with overlap)
       → embed each chunk (OpenAI text-embedding-3-small)
       → store chunk + embedding in Postgres

Query  → embed query
       → for every chunk: dense score (cosine similarity)
                          + sparse score (BM25-style term overlap)
       → blend (weighted sum) → top-K chunks
       → inject as numbered excerpts into the LLM prompt
       → LLM cites excerpt numbers → resolved back to filename + chunk index
```

### AI Analysis Flow
```
Project + latest financial metrics + top-K retrieved excerpts
        │
        ▼
  Single structured-JSON chat completion
  (system prompt enforces: ground every claim, cite excerpts,
   say "evidence missing" rather than inventing detail)
        │
        ▼
  Parsed into: executive_summary, swot, scores, risk_scores,
               investment_memo, citations
        │
        ▼
  scores + risk_scores + latest financial snapshot
        │
        ▼
  Valuation engine (5 methods) → stored alongside the report
```

---

## Tech Stack

**Frontend:** Next.js 15 (App Router), React 18, TypeScript, Tailwind CSS,
React Query, Zustand, Recharts, Framer Motion (available for future use),
Lucide icons.

**Backend:** FastAPI, Python 3.12, SQLAlchemy 2.0, Pydantic v2, JWT auth
(`python-jose`), `bcrypt` for password hashing.

**AI:** OpenAI (`gpt-4.1` for generation, `text-embedding-3-small` for
embeddings) — model names are configurable via environment variables.

**Database:** PostgreSQL 16.

**Parsing:** `pypdf`, `python-pptx`, `openpyxl`, standard-library `csv`.

**Deployment:** Docker, Docker Compose, NGINX reverse proxy, GitHub Actions CI.

---

## Installation

### Prerequisites
- Docker & Docker Compose
- An OpenAI API key (only required for the AI Analysis and AI Chat features
  — everything else, including the full financial and valuation engines,
  works without one)

### Quick start (Docker Compose)

```bash
git clone <this-repo>
cd ai-venture-analyst

# Backend config
cp backend/.env.example backend/.env
# Edit backend/.env and set OPENAI_API_KEY (and a real JWT_SECRET for anything
# beyond local testing)

# Frontend config
cp frontend/.env.example frontend/.env

docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API docs (Swagger UI): http://localhost:8000/docs
- Through the NGINX proxy: http://localhost

### Running the backend locally without Docker

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then edit DATABASE_URL to point at a local Postgres
uvicorn app.main:app --reload
```

### Running the frontend locally without Docker

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

---

## Environment Variables

### `backend/.env`
| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:postgres@db:5432/venture_analyst` |
| `JWT_SECRET` | Secret used to sign auth tokens — **change this** | `CHANGE_ME_IN_PRODUCTION` |
| `JWT_ALGORITHM` | JWT signing algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime | `1440` |
| `OPENAI_API_KEY` | Required for AI Analysis / Chat | *(empty)* |
| `OPENAI_CHAT_MODEL` | Chat completion model | `gpt-4.1` |
| `OPENAI_EMBEDDING_MODEL` | Embedding model | `text-embedding-3-small` |
| `UPLOAD_DIR` | Local disk path for uploaded files | `uploads` |
| `MAX_UPLOAD_MB` | Max upload size | `25` |
| `FRONTEND_ORIGIN` | CORS allow-origin | `http://localhost:3000` |

### `frontend/.env`
| Variable | Description | Default |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | Backend URL used by the Next.js rewrite proxy | `http://localhost:8000` |

---

## API Documentation

Full interactive OpenAPI docs are auto-generated at `/docs` (Swagger) and
`/redoc` once the backend is running. Summary of the core routes:

```
POST   /api/auth/register
POST   /api/auth/login
GET    /api/auth/me

GET    /api/projects
POST   /api/projects
GET    /api/projects/{id}
PATCH  /api/projects/{id}
DELETE /api/projects/{id}

GET    /api/projects/{id}/documents
POST   /api/projects/{id}/documents         (multipart: file, doc_category)
DELETE /api/projects/{id}/documents/{doc_id}

POST   /api/projects/{id}/financials
GET    /api/projects/{id}/financials/latest
GET    /api/projects/{id}/financials/metrics
GET    /api/projects/{id}/financials/valuation

POST   /api/projects/{id}/analysis           (runs the full AI pipeline)
GET    /api/projects/{id}/analysis/latest
POST   /api/projects/{id}/analysis/chat      ({"question": "..."})

GET    /api/dashboard/summary                (portfolio-wide aggregation across all projects)

GET    /api/projects/{id}/reports/investment-memo         (PDF download)
GET    /api/projects/{id}/reports/board-report            (PDF download)
GET    /api/projects/{id}/reports/investor-report         (PDF download)
GET    /api/projects/{id}/reports/due-diligence-checklist (PDF download, no analysis required)
```

All routes except `/auth/register` and `/auth/login` require
`Authorization: Bearer <token>`.

---

## Financial & Valuation Methodology

All formulas live in `backend/app/services/financial_engine.py` and
`backend/app/services/valuation.py`, and are directly unit-tested in
`backend/tests/`. Key formulas:

- **Gross Margin %** = (Revenue − COGS) / Revenue × 100
- **Net Burn (monthly)** = OpEx + COGS − Revenue
- **Runway (months)** = Cash Balance / Net Burn (undefined/∞ if profitable)
- **CAC** = Sales & Marketing Spend / New Customers Acquired
- **LTV** = ARPA × Gross Margin % × (1 / Monthly Churn Rate)
- **CAC Payback (months)** = CAC / (ARPA × Gross Margin %)
- **Break-even (units)** = Fixed Costs / (Price − Variable Cost per Unit)
- **VC Method** = (Terminal ARR × Exit Multiple / Anticipated ROI) − Investment Requested
- **DCF** = Σ discounted yearly free cash flow + discounted Gordon Growth terminal value

See the source files for full detail and inline documentation of every
assumption (e.g. the stage-based comparable valuations used as a Scorecard/
Risk-Factor-Summation baseline are editable constants, not hidden magic
numbers).

---

## Testing

```bash
cd backend
pip install -r requirements.txt
PYTHONPATH=. pytest -v
```

25 tests cover every financial metric, all five valuation methods, and PDF
report generation, including edge cases (zero customers, profitable vs.
burning, pre-revenue vs. revenue-generating, clamped scorecard ratios,
Berkus cap enforcement, and reports generated with missing/partial data).

---

## Screenshots

_Add screenshots of the dashboard, project detail page, and valuation panel
here once you've run the app against real data — e.g.:_

```
docs/screenshots/dashboard.png
docs/screenshots/project-detail.png
docs/screenshots/valuation-panel.png
```

---

## Roadmap / Future Enhancements

This repository intentionally ships a **working vertical slice** first. In
priority order, the next increments are:

1. **Background processing (Celery + Redis)** — move document parsing,
   embedding, and analysis off the request/response cycle so large decks
   don't block the API.
2. **Dedicated vector database (Qdrant)** — swap the in-Postgres
   embedding + cosine-similarity approach for Qdrant once corpus size
   outgrows in-process search; the `embeddings.py` interface is already
   isolated so this is a drop-in swap.
3. **Multi-agent orchestration (LangGraph)** — decompose the single
   structured-analysis call into a graph of specialist agents (Financial
   Analyst, Market Analyst, Risk Analyst, Valuation Agent, Investment
   Committee Agent) with explicit hand-offs, once there's a concrete need
   the single-call approach can't meet (e.g. multi-step tool use, longer
   deliberation chains).
4. **Power BI dataset export** — structured CSV/JSON exports of revenue,
   expenses, growth, KPIs, and scores for BI tooling.
5. **Cap table & ownership modeling.**
6. **Auth hardening** — httpOnly cookie sessions instead of localStorage
   JWT storage, refresh tokens, and role-based access control for
   multi-user firms (analyst / partner / admin roles).
7. **shadcn/ui component migration** — the current UI primitives
   (`src/components/ui.tsx`) are hand-rolled Tailwind components in the
   shadcn style; wiring up the actual shadcn CLI/registry is a mechanical
   next step once the visual direction is locked.
8. **TAM/SAM/SOM structured extraction** — currently the AI is asked to
   derive these narratively from context; a dedicated structured-output
   pass with explicit market-sizing math would make this more rigorous.
9. **PPTX/DOCX report formats** — reports currently generate as PDF only;
   the same section-assembly logic in `report_generator.py` could target
   `python-pptx`/`python-docx` for editable board-deck or Word deliverables.

![CI](https://github.com/Chenthurr/ai-venture-analyst/actions/workflows/ci.yml/badge.svg)
---

## License

MIT — see `LICENSE`.
