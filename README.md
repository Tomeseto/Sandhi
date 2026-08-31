# SANDHI

**Travel Disruption Cascade Intelligence**

*A delay is not an event. It is a set of countdowns nobody told you had started.*

---

## Overview

SANDHI treats a traveller's itinerary as a temporal dependency graph. When one booking is disrupted, SANDHI propagates the impact through downstream dependencies, identifies which bookings become infeasible, computes policy-governed deadlines, calculates applicable entitlements, and generates feasibility-verified recovery options — all with full provenance.

## Problem

When a flight is delayed by 3 hours, the real loss is not the flight delay. It's the missed train connection, the forfeited hotel booking, the expired refund window, and the timed museum entry that becomes useless. These cascading consequences are invisible to existing travel tools.

See [problem statement.md](problem%20statement.md) for the full problem statement.

## Solution

SANDHI models itineraries as dependency graphs and provides:

1. **Cascade Analysis** — Propagates disruptions through downstream bookings
2. **Deadline Ledger** — Live countdowns for refund/cancellation/claim windows
3. **Entitlement Computation** — Deterministic calculation from Indian travel regulations
4. **Recovery Options** — Feasibility-verified alternatives ranked transparently
5. **Provenance** — Source, timestamp, and type for every important value

See [solution.md](solution.md) for the full solution description.

## Features

- ✅ Dependency graph modelling of multi-modal itineraries
- ✅ Deterministic disruption propagation
- ✅ Per-booking impact explanations
- ✅ Live deadline countdowns with value at stake
- ✅ Indian railway/aviation entitlement rules (verified subset)
- ✅ Feasibility-checked recovery options
- ✅ Transparent ranking with scoring breakdown
- ✅ Provenance system for all critical values
- ✅ Evidence drawer for source inspection
- ✅ Offline/demo mode — no API keys required
- ✅ No AI/LLM dependency for any core computation

## Architecture Summary

```
Frontend (React 18 + TypeScript + Vite + Tailwind CSS)
    ↕ HTTP REST
Backend (FastAPI + Python + NetworkX)
    ↕
Data (In-Memory Seeded Repository for MVP · PostgreSQL/PostGIS for Production)
```

See [architecture.md](architecture.md) for the full architecture document.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS |
| Backend | Python 3.11+, FastAPI, Pydantic, NetworkX |
| Persistence (MVP) | In-Memory Seeded Repository Store (`DataStore`) |
| Persistence (Prod) | PostgreSQL + PostGIS (Production Architecture) |
| Testing | Pytest (16/16 tests passing) |


## Local Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- npm

### Backend Setup

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend runs on `http://localhost:5173` and the backend on `http://localhost:8000`.

### Docker Setup

```bash
docker-compose up --build
```

This starts both frontend and backend.

## Vercel Single-Project Deployment

SANDHI is configured to deploy as a **single project on Vercel** combining the React/Vite SPA and FastAPI Python serverless backend.

### Option 1: Deploy via Vercel CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy directly from repository root
vercel

# Deploy to production
vercel --prod
```

### Option 2: Deploy via GitHub / Vercel Dashboard

1. Push this repository to GitHub: `https://github.com/Tomeseto/Sandhi.git`
2. Import the repository in [Vercel Dashboard](https://vercel.com/new).
3. Vercel automatically detects the configuration from `vercel.json`, `package.json`, and `requirements.txt`:
   - **Build Command**: `cd frontend && npm install && npm run build` (or root `npm run build`)
   - **Output Directory**: `frontend/dist`
   - **Serverless API**: `api/index.py` handles all `/api/*` requests
4. Click **Deploy**.

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SANDHI_MODE` | `demo` | `demo` (seeded offline fixtures) or `live` |
| `CORS_ORIGINS` | `*` | Allowed CORS origins (comma-separated) |

> **Note**: Zero external API keys or database connection strings are required. SANDHI operates 100% deterministically in DEMO/OFFLINE mode on Vercel.

## Local Development Commands


### Backend

```bash
cd backend
pytest                          # Run tests
pytest -v                       # Verbose test output
python -m uvicorn app.main:app --reload  # Dev server
```

### Frontend

```bash
cd frontend
npm run dev                     # Dev server
npm run build                   # Production build
npm run preview                 # Preview production build
```

## Test Commands

```bash
# Backend tests
cd backend && pytest -v

# Frontend tests
cd frontend && npm test
```

## Demo Instructions

1. Start the backend: `cd backend && python -m uvicorn app.main:app --reload --port 8000`
2. Start the frontend: `cd frontend && npm run dev`
3. Open `http://localhost:5173`
4. View the demo itinerary: Mumbai → Delhi → Agra
5. Click "Trigger Disruption" to delay Flight 6E 5312 by 2h50m
6. Observe the cascade: which bookings break and why
7. View the Deadline Ledger with live countdowns
8. Click any entitlement to see source/provenance
9. View ranked recovery options with feasibility status

## Example Scenario

**Itinerary**: Mumbai → (Flight 6E 5312) → Delhi → (Transfer) → Delhi → (Train 12002) → Agra → (Hotel) → Agra → (Taj timed entry)

**Disruption**: Flight 6E 5312 delayed by 2h50m

**Result**:
- Flight: DELAYED
- Transfer: AT_RISK
- Train 12002: INFEASIBLE (missed)
- Hotel: AT_RISK
- Taj timed entry: FORFEITED

**Deadline Ledger** shows countdowns for TDR filing, hotel cancellation, etc.

## API Overview

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/trips/{trip_id}` | GET | Get trip with bookings |
| `/trips/{trip_id}/graph` | GET | Get dependency graph structure |
| `/trips/{trip_id}/disruptions` | POST | Trigger a disruption |
| `/trips/{trip_id}/cascade` | GET | Get cascade analysis results |
| `/trips/{trip_id}/deadlines` | GET | Get Deadline Ledger |
| `/trips/{trip_id}/entitlements` | GET | Get computed entitlements |
| `/trips/{trip_id}/recovery-options` | GET | Get feasibility-checked recovery options |
| `/evidence/{evidence_id}` | GET | Get evidence/provenance record |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Backend won't start | Ensure Python 3.11+ and `pip install -r requirements.txt` |
| Frontend won't start | Ensure Node 18+ and `npm install` |
| CORS errors | Check `CORS_ORIGINS` in `.env` |
| Empty trip data | Backend seeds demo data on startup automatically |

## Limitations

- MVP supports one demo scenario only
- No live API integration (all data is fixture-based)
- No user authentication
- No persistent state across restarts (SQLite in-memory for demo)
- Policy rules are a verified subset, not comprehensive
- No mobile-optimized layout (desktop-first)

## Known Assumptions

- Demo scenario uses realistic but fixture times/prices
- Policy rules represent verified structural patterns, not legal advice
- Transfer times are estimates based on typical conditions
- All monetary values in the demo are labelled with provenance type
- The system does not provide legal advice

## Related Documents

- [Architecture](architecture.md)
- [Solution](solution.md)
- [Problem Statement](problem%20statement.md)
- [AI Rules](ai%20rules.md)
- [Implementation Status](IMPLEMENTATION_STATUS.md)
