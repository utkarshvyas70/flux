# Flux — Version Control for LLM Prompts

> Git for prompts. Branch, evaluate, diff, and ship with confidence.

## The problem

Every team using LLMs manages their prompts in a folder called `prompts_final_v3_USE_THIS_ONE.txt`. Nobody knows what changed, why it changed, or which version actually performed better.

Flux gives prompts the same discipline that Git gave source code — with the addition of behavioral evaluation, because unlike code, a one-word change in a prompt can completely flip model behavior.

## Architecture
┌─────────────────────────────────────────────────────┐
│                    Browser                          │
│  Next.js 14 · TypeScript · Tailwind · Monaco Editor │
└─────────────────────┬───────────────────────────────┘
│ HTTP / SSE
┌─────────────────────▼───────────────────────────────┐
│                  FastAPI Backend                     │
│  Auth · Versioning · Eval Engine · Diff · Streaming  │
└──────┬──────────────┬──────────────────┬────────────┘
│              │                  │
┌──────▼──────┐ ┌─────▼──────┐ ┌────────▼───────┐
│  PostgreSQL  │ │   Redis    │ │   OpenAI API   │
│  (all data) │ │  (queues)  │ │  (LLM calls)   │
└─────────────┘ └────────────┘ └────────────────┘

## Features

- **Prompt repositories** — organize prompts by project
- **Git-like versioning** — commit, branch, restore any version
- **Behavioral eval engine** — exact match, TF-IDF similarity, LLM-as-judge scoring
- **Behavioral diff view** — compare two versions by their outputs, not just their text
- **Live playground** — stream LLM responses with latency, token count, cost estimate
- **Multi-user workspaces** — invite team members

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14, TypeScript, Tailwind CSS, shadcn/ui, Monaco Editor |
| Backend | Python, FastAPI, SQLAlchemy, Alembic |
| Database | PostgreSQL |
| Cache/Queue | Redis |
| ML/Eval | scikit-learn (TF-IDF similarity), OpenAI API (LLM judge) |
| Auth | JWT (access + refresh tokens, httpOnly cookies) |
| Infra | Docker, Docker Compose |

## Local setup

### Prerequisites

- Docker Desktop
- Node.js 20+
- Git

### 1. Clone

```bash
git clone https://github.com/utkarshvyas70/flux.git
cd flux
```

### 2. Start all services

```bash
docker-compose up --build
```

All 4 services start: PostgreSQL, Redis, FastAPI backend (port 8000), Next.js frontend (port 3000).

### 3. Run migrations

```bash
docker exec -it flux_backend alembic upgrade head
```

### 4. (Optional) Load demo data

```bash
docker exec -it flux_backend python seed_demo.py
```

Demo login: `demo@flux.dev` / `demo1234`

### 5. Open

- App: http://localhost:3000
- API docs: http://localhost:8000/docs

## Environment variables

### Backend (`backend/.env`)

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://flux_user:flux_password@postgres:5432/flux_db` |
| `REDIS_URL` | Redis connection string | `redis://redis:6379` |
| `SECRET_KEY` | JWT signing secret | Change in production |
| `OPENAI_API_KEY` | OpenAI API key | Optional — exact/similarity evals work without it |

### Frontend (`frontend/.env.local`)

| Variable | Description |
|---|---|
| `NEXT_PUBLIC_API_URL` | Backend API base URL |

## How it works

### Eval engine

Three eval types are supported:

1. **Exact match** — string comparison, returns 0 or 1. No API key needed.
2. **Similarity** — TF-IDF cosine similarity between expected and actual output, returns 0.0–1.0. No API key needed.
3. **LLM judge** — GPT-4o-mini scores the output against expected on a 0.0–1.0 rubric. Requires OpenAI key.

Overall score = average of all case scores × 100.

### Behavioral diff

Unlike textual diff (which compares characters), behavioral diff compares what the model actually outputs for the same inputs across two versions. A one-word prompt change can produce completely different outputs — behavioral diff surfaces this.

Both versions must have eval runs from the same suite for behavioral diff to work.

### Streaming playground

The playground uses Server-Sent Events (SSE) on the backend and ReadableStream on the frontend. Tokens stream as they arrive from the LLM. The final SSE event contains latency, token counts, and cost is calculated client-side using known per-model pricing.

## Deployment

### Frontend → Vercel

```bash
cd frontend
vercel deploy --prod
```

Set environment variable in Vercel dashboard:
- `NEXT_PUBLIC_API_URL` = your Railway backend URL

### Backend + DB + Redis → Railway

1. Create a new Railway project
2. Add PostgreSQL and Redis services
3. Deploy the backend as a service pointing to the `backend/` directory
4. Set all environment variables from `backend/.env.example`
5. Run migrations: `alembic upgrade head`

## Build status

- [x] Phase 1 — Project foundation
- [x] Phase 2 — Auth system
- [x] Phase 3 — Workspaces and repositories
- [x] Phase 4 — Prompt versioning
- [x] Phase 5 — Eval engine
- [x] Phase 6 — Diff view
- [x] Phase 7 — Streaming playground
- [x] Phase 8 — Polish and deployment