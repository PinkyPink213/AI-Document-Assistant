# Enterprise AI Document Assistant

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.139+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-15-black?logo=next.js)](https://nextjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Qdrant](https://img.shields.io/badge/Qdrant-Vector_DB-DC244C?logo=qdrant&logoColor=white)](https://qdrant.tech/)
[![Tests](https://img.shields.io/badge/tests-pytest%20%7C%20Vitest-brightgreen)](#testing)

A full-stack, enterprise-style AI workspace for uploading PDFs, managing
conversations, and asking document-grounded questions. The application combines
conversation-scoped retrieval, AI tool calling, reranking, source citations,
academic discovery through MCP, and human approval for destructive actions.

> Built as a portfolio-ready reference for production-oriented RAG and agentic
> application development.

## ✨ Key Features

- **Multi-conversation workspace** — create, rename, inspect, and delete independent chats.
- **PDF document management** — drag-and-drop upload, progress feedback, duplicate detection, metadata, and deletion.
- **Conversation-scoped RAG** — retrieves only documents belonging to the active conversation.
- **Filename-aware retrieval** — searches a specific PDF when its name is mentioned; otherwise searches the full conversation collection.
- **Reranking and citations** — reranks retrieved chunks and produces page-level source references.
- **Agentic tool calling** — LangGraph agent selects document, counting, search, and deletion tools.
- **Academic Search MCP** — recommends external papers from scholarly providers with verified titles and URLs.
- **Human-in-the-loop controls** — requires approval or rejection before document deletion.
- **Persistent chat history** — stores user and assistant messages in PostgreSQL.
- **Progressive response rendering** — responsive chat states, markdown, syntax highlighting, retry controls, and response continuation.
- **Health monitoring** — API and database health indicators exposed through REST endpoints.
- **Tested frontend and backend** — Pytest integration/unit tests plus Vitest, Testing Library, and MSW.

## 🏗️ Architecture Overview

```mermaid
flowchart LR
    UI["Next.js + React UI"] -->|REST| API["FastAPI API Layer"]
    API --> SVC["Service Layer"]
    SVC --> REPO["Repository Layer"]
    REPO --> PG[("PostgreSQL")]

    SVC --> AGENT["LangGraph AI Agent"]
    AGENT --> RAG["RAG + Reranking"]
    RAG --> QD[("Qdrant")]
    AGENT --> LLM["OpenAI API"]
    AGENT --> MCP["Academic Search MCP"]
    AGENT --> HITL{"Human Approval"}
    HITL -->|Approve| PG
    HITL -->|Approve| QD
```

The backend follows a layered architecture:

| Layer      | Responsibility                                                   |
| ---------- | ---------------------------------------------------------------- |
| API        | HTTP routing, request validation, and response models            |
| Service    | Application workflows and business logic                         |
| Repository | PostgreSQL persistence and database queries                      |
| AI         | Agent orchestration, tools, retrieval, reranking, and citations  |
| Frontend   | Feature-based UI, server state, local state, and API integration |

## 🧰 Tech Stack

| Area                 | Technologies                                                |
| -------------------- | ----------------------------------------------------------- |
| Backend              | Python 3.12, FastAPI, Pydantic, SQLModel                    |
| AI                   | LangChain, LangGraph, OpenAI API, Academic Search MCP       |
| Retrieval            | Qdrant, OpenAI embeddings, metadata filtering, reranking    |
| Database             | PostgreSQL, Alembic                                         |
| Frontend             | React 19, Next.js 15, TypeScript, Tailwind CSS, shadcn/ui   |
| State and networking | TanStack Query, Zustand, Axios                              |
| UX                   | Framer Motion, React Markdown, syntax highlighting          |
| Testing              | Pytest, pytest-asyncio, HTTPX, Vitest, Testing Library, MSW |
| Tooling              | uv, npm, Husky, Docker Compose                              |

## 🚀 Installation

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- Node.js 20+ and npm
- PostgreSQL
- Qdrant or Qdrant Cloud
- OpenAI API key

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd enterprise-ai-workspace
```

### 2. Configure the backend

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your-openai-api-key
OPENAI_CHAT_MODEL=gpt-4.1-mini
OPENAI_EMBEDDINGS_MODEL=text-embedding-3-small

POSTGRES_URL=postgresql+psycopg://postgres:password@localhost:5432/enterprise_ai

QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=
QDRANT_COLLECTION_NAME=documents

LANGSMITH_API_KEY=
LANGSMITH_PROJECT=enterprise-ai-document-assistant
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_TRACING=false
```

Install dependencies, apply migrations, and start FastAPI:

```bash
uv venv
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Interactive API documentation is available at
[`http://127.0.0.1:8000/docs`](http://127.0.0.1:8000/docs).

### 3. Configure the frontend

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Open [`http://localhost:3000`](http://localhost:3000).

### Optional: PostgreSQL with Docker

The included Compose file starts PostgreSQL locally:

```bash
docker compose up -d postgres
```

Qdrant must be configured separately through a local instance or Qdrant Cloud.

## 🔌 API Overview

| Method   | Endpoint                                       | Description                            |
| -------- | ---------------------------------------------- | -------------------------------------- |
| `GET`    | `/conversation`                                | List conversations                     |
| `POST`   | `/conversation`                                | Create a conversation                  |
| `GET`    | `/conversation/{conversation_id}`              | Get conversation details               |
| `PUT`    | `/conversation/{conversation_id}`              | Rename or update a conversation        |
| `DELETE` | `/conversation/{conversation_id}`              | Delete a conversation and related data |
| `POST`   | `/{conversation_id}/documents`                 | Upload a PDF                           |
| `GET`    | `/{conversation_id}/documents`                 | List conversation documents            |
| `GET`    | `/documents/{document_id}`                     | Get document metadata                  |
| `DELETE` | `/documents/{document_id}`                     | Delete document metadata and vectors   |
| `GET`    | `/conversations/{conversation_id}/messages`    | Get persisted chat history             |
| `POST`   | `/conversations/{conversation_id}/chat`        | Send a message to the AI agent         |
| `POST`   | `/conversations/{conversation_id}/chat/resume` | Resume an interrupted agent action     |
| `GET`    | `/health`                                      | Check API health                       |
| `GET`    | `/health/db`                                   | Check database health                  |

## 📁 Project Structure

```text
enterprise-ai-workspace/
├── app/
│   ├── ai/                 # Agent, tools, RAG, MCP, embeddings, and Qdrant
│   ├── api/                # FastAPI route handlers
│   ├── core/               # Configuration, logging, and startup
│   ├── db/                 # Database engine and sessions
│   ├── models/             # SQLModel database models
│   ├── repositories/       # Persistence and query layer
│   ├── schemas/            # API request and response models
│   ├── services/           # Application workflows and business logic
│   └── main.py             # FastAPI application entry point
├── frontend/
│   ├── app/                # Next.js App Router
│   ├── components/         # Shared UI components
│   ├── features/           # Chat, conversation, document, and health modules
│   ├── services/           # Axios and TanStack Query configuration
│   ├── store/              # Zustand application state
│   └── test/               # MSW and frontend test setup
├── migrations/             # Alembic database migrations
├── tests/                  # Backend unit and integration tests
├── scripts/                # Maintenance and recovery utilities
├── docker-compose.yml      # Optional local PostgreSQL
├── pyproject.toml          # Python dependencies and tooling
└── README.md
```

## 🧪 Testing

Backend:

```bash
uv sync
uv run pytest
```

Frontend:

```bash
cd frontend
npm install
npm run test
npm run build
```

## 🗺️ Future Improvements

- Persistent PostgreSQL checkpointer for LangGraph workflows
- Authentication, role-based access control, and organization isolation
- Native server-sent event streaming from FastAPI
- Automated RAG evaluation for recall, faithfulness, and citation accuracy
- Hybrid dense/sparse retrieval and configurable reranking models
- Background document processing with task queues
- Rate limiting, audit logs, token usage, and cost monitoring
- OpenTelemetry/LangSmith dashboards and alerting
- Full Docker deployment and CI/CD with GitHub Actions

## 📄 License

This project is intended for educational and portfolio use. Add a license file
before distributing or using it commercially.
