# Enterprise AI Document Assistant

A full-stack workspace for chatting with enterprise documents through a modern Next.js frontend and FastAPI backend.

## Architecture

- Frontend: Next.js 15, React 19, TypeScript, Tailwind CSS, TanStack Query, Zustand, shadcn/ui
- Backend: FastAPI, SQLModel, Alembic, LangGraph-style agent orchestration
- Data flow: conversations, documents, chat, and health checks are exposed via REST endpoints and consumed by the frontend feature modules

## Folder structure

- app/: FastAPI application and router modules
- frontend/: feature-based Next.js frontend application
- tests/: backend integration tests
- migrations/: Alembic migrations

## Setup

### Backend

```bash
uv venv
uv sync
uv run uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Development

- Frontend tests: `npm run test`
- Backend integration tests: `uv run pytest`

## Environment variables

- NEXT_PUBLIC_API_BASE_URL: override the frontend API base URL (defaults to http://127.0.0.1:8000)

## Deployment

The current workspace is ready for local development and can be extended to containerized deployment with Docker Compose.
