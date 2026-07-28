# Enterprise AI Document Assistant

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.139+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-15-black?logo=next.js)](https://nextjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Qdrant](https://img.shields.io/badge/Qdrant-Vector_DB-DC244C?logo=qdrant&logoColor=white)](https://qdrant.tech/)
[![Tests](https://img.shields.io/badge/tests-pytest%20%7C%20Vitest-brightgreen)](#testing)
[![CI](https://github.com/PinkyPink213/AI-Document-Assistant/actions/workflows/ci.yml/badge.svg)](https://github.com/PinkyPink213/AI-Document-Assistant/actions/workflows/ci.yml)
[![Live Demo](https://img.shields.io/badge/Live_Demo-Open_App-EC4899?logo=vercel&logoColor=white)](https://ai-document-assistant-mauve-one.vercel.app/)

A full-stack, enterprise-style AI workspace for uploading PDFs, managing
conversations, and asking document-grounded questions. The application combines
conversation-scoped retrieval, AI tool calling, reranking, source citations,
academic discovery through MCP, and human approval for destructive actions.

**[🚀 Open the live demo](https://ai-document-assistant-mauve-one.vercel.app/)**

> Built as a portfolio-ready reference for production-oriented RAG and agentic
> application development.

## 🗺️ Project Overview

The diagram below summarizes the architecture, feature workflows, core data
model, AI orchestration, and reliability stack of the complete application.
Click the image to open the full-size version.

[![AI Document Assistant — Project Architecture and Feature Map](img/project-architecture-feature-map.png)](img/project-architecture-feature-map.png)

## 🖥️ Application Preview

### Dark theme

[![Enterprise AI Document Assistant — dark theme](img/app-dark-them.png)](https://ai-document-assistant-mauve-one.vercel.app/)

### Light theme

[![Enterprise AI Document Assistant — light theme](img/app-light-theme.png)](https://ai-document-assistant-mauve-one.vercel.app/)

## ✨ Key Features

- **Multi-conversation workspace** — create, rename, inspect, and delete independent chats.
- **PDF document management** — drag-and-drop upload, progress feedback, duplicate detection, metadata, and deletion.
- **Conversation-scoped RAG** — retrieves only documents belonging to the active conversation.
- **Filename-aware retrieval** — searches a specific PDF when its name is mentioned; otherwise searches the full conversation collection.
- **Reranking and citations** — reranks retrieved chunks and produces page-level source references.
- **Agentic tool calling** — the LangGraph agent selects document listing, counting, retrieval, and academic discovery tools.
- **Academic Search MCP** — searches Semantic Scholar, Crossref, OpenAlex, or PubMed and returns clickable verified paper links.
- **Deterministic deletion workflow** — explicit `delete/remove/ลบ + filename.pdf` requests bypass LLM decision-making and open approval controls immediately.
- **Persistent human-in-the-loop controls** — stores LangGraph checkpoints in PostgreSQL so approval workflows survive backend restarts.
- **Consistent deletion** — approved document deletion removes PostgreSQL metadata and conversation-scoped Qdrant vectors, then refreshes the sidebar.
- **Synchronized deletion UI** — successful approval immediately updates the document list and document statistics, then revalidates both against the API.
- **Persistent chat history** — stores user and assistant messages in PostgreSQL.
- **Progressive response rendering** — responsive chat states, markdown, syntax highlighting, retry controls, and response continuation.
- **Health monitoring** — API and database health indicators exposed through REST endpoints.
- **LangSmith observability** — correlated traces and structured JSON logs for requests, conversations, retrieval, tools, LLM usage, errors, cost, and citation coverage.
- **API protection** — endpoint-specific rate limits and server-side PDF signature validation.
- **Tested frontend and backend** — Pytest integration/unit tests plus Vitest, Testing Library, and MSW.

## 🏗️ Architecture Overview

```mermaid
flowchart LR
    UI["Next.js + React UI"] -->|REST| API["FastAPI API Layer"]
    API --> SVC["Service Layer"]
    SVC --> REPO["Repository Layer"]
    REPO --> PG[("PostgreSQL")]

    SVC --> ROUTER{"Request Routing"}
    ROUTER -->|Document question| AGENT["LangGraph AI Agent"]
    AGENT --> RAG["RAG + Reranking"]
    RAG --> QD[("Qdrant")]
    AGENT --> LLM["OpenAI API"]
    AGENT --> MCP["Academic Search MCP"]

    ROUTER -->|Explicit delete request| DELETE["LangGraph Delete Workflow"]
    DELETE --> CHECKPOINT[("PostgreSQL Checkpoints")]
    DELETE --> HITL{"Approve / Reject"}
    HITL -->|Approve| PG
    HITL -->|Approve| QD
```

### Backend workflow — explain the system in this order

> **Short project explanation:** The backend is a layered FastAPI application
> for conversation-scoped document intelligence. PostgreSQL is the source of
> truth for conversations, documents, chat history, and durable LangGraph
> checkpoints. Uploaded PDFs are validated, converted into text chunks,
> embedded, and indexed in Qdrant. Chat requests are routed to document RAG,
> external academic search through MCP, or a human-approved deletion workflow.
> The service layer coordinates these stores and keeps the HTTP, business,
> persistence, and AI concerns separated.

```mermaid
flowchart TD
    START["FastAPI startup"] --> LIFE["Lifespan"]
    LIFE --> INIT["Configure JSON logging, LangSmith, and Qdrant indexes"]
    LIFE --> CP[("Open PostgreSQL checkpoint pool")]
    CP --> BUILD["Build LangGraph agent and delete workflow"]
    BUILD --> READY["API ready"]

    USER["Frontend request"] --> MW["CORS → request ID/logging → rate limit"]
    MW --> ROUTER["FastAPI router + Pydantic validation"]
    ROUTER --> DI["Dependency injection"]
    DI --> SERVICE["Service layer"]

    SERVICE --> DECISION{"Requested feature"}

    DECISION -->|Conversation CRUD| CRUD["ConversationService"]
    CRUD --> CREPO["Conversation / document / message repositories"]
    CREPO --> PG[("PostgreSQL source of truth")]

    DECISION -->|Upload PDF| UPLOAD["Validate MIME, size, and PDF signature"]
    UPLOAD --> EXTRACT["PyPDF extract → chunk 600/100"]
    EXTRACT --> EMBED["OpenAI embeddings"]
    EMBED --> QD[("Qdrant vectors + metadata")]
    QD --> DOCROW["Save document metadata"]
    DOCROW --> PG

    DECISION -->|Ask uploaded documents| AGENT["AgentService / LangGraph agent"]
    AGENT --> ACTIVE["Load active document IDs from PostgreSQL"]
    ACTIVE --> SEARCH["Qdrant filtered search: top 20"]
    SEARCH --> RERANK["LLM rerank: select 6"]
    RERANK --> ANSWER["Grounded answer + inline page citations"]

    DECISION -->|Find external papers| MCPWRAP["LangChain tool wrapper"]
    MCPWRAP --> MCP["MCP stdio: academic-search"]
    MCP --> PROVIDER["Crossref / Semantic Scholar / OpenAlex / PubMed"]
    PROVIDER --> LINKS["Validate URLs + clickable paper titles"]

    DECISION -->|Delete PDF| DELETE["Deterministic LangGraph delete workflow"]
    DELETE --> INTERRUPT["interrupt: Approve / Reject"]
    INTERRUPT --> CP
    INTERRUPT -->|Approve| CLEAN["Delete Qdrant vectors + PostgreSQL row"]
    INTERRUPT -->|Reject| CANCEL["Cancel without side effects"]

    ANSWER --> HISTORY["Persist assistant message"]
    LINKS --> HISTORY
    CLEAN --> HISTORY
    CANCEL --> HISTORY
    HISTORY --> PG
    HISTORY --> RESPONSE["Typed API response → Frontend"]
    CRUD --> RESPONSE
    DOCROW --> RESPONSE
```

Follow one request through the same reusable layers:

```text
HTTP request
  → Middleware: cross-cutting protection and observability
  → Router: endpoint and HTTP contract
  → Pydantic schema: input/output validation
  → Dependency injection: assemble session, repositories, and services
  → Service: business rules and workflow orchestration
  → Repository / AI adapter: PostgreSQL, Qdrant, OpenAI, or MCP
  → Response schema
  → Frontend
```

| Feature | Start here | Main workflow | State changed |
| --- | --- | --- | --- |
| Conversation CRUD | `app/api/conversation.py` | Router → `ConversationService` → repositories | PostgreSQL; deletion also cleans Qdrant and checkpoints |
| PDF upload | `POST /{conversation_id}/documents` | Validate → extract → chunk → embed → index → save metadata | Qdrant + PostgreSQL |
| Document question | `POST /conversations/{id}/chat` | active SQL IDs → filtered retrieval → rerank → grounded answer | Chat history + agent checkpoint |
| Paper discovery | `AgentService` academic route | LangChain wrapper → MCP client → academic provider → URL validation | Chat history |
| PDF deletion | delete intent or delete tool | StateGraph → interrupt → durable checkpoint → Approve/Reject | Qdrant + PostgreSQL + checkpoint |
| Conversation deletion | `DELETE /conversation/{id}` | clean vectors → agent threads → messages → documents → parent | All conversation-scoped state |

The core design rule is:

```text
Use deterministic code for actions that must be predictable.
Use the LLM for ambiguous language and tool selection.
Use human approval for destructive side effects.
```

### Request routing

| Request type                   | Execution path                                                             |
| ------------------------------ | -------------------------------------------------------------------------- |
| Question about an uploaded PDF | Conversation/filename filter → Qdrant retrieval → reranking → cited answer |
| External paper recommendation  | Academic Search MCP → normalized paper metadata → clickable source links   |
| Explicit PDF deletion          | Deterministic delete workflow → PostgreSQL checkpoint → Approve/Reject     |
| Conversation deletion          | PostgreSQL rows + Qdrant vectors + LangGraph checkpoint cleanup            |

The backend follows a layered architecture:

| Layer      | Responsibility                                                                |
| ---------- | ----------------------------------------------------------------------------- |
| API        | HTTP routing, request validation, and response models                         |
| Service    | Application workflows and business logic                                      |
| Repository | PostgreSQL persistence and database queries                                   |
| AI         | Agent orchestration, MCP, persistent workflows, RAG, reranking, and citations |
| Frontend   | Feature-based UI, server state, local state, and API integration              |

## 🧰 Tech Stack

| Area                 | Technologies                                                |
| -------------------- | ----------------------------------------------------------- |
| Backend              | Python 3.12, FastAPI, Pydantic, SQLModel                    |
| AI                   | LangChain, LangGraph, OpenAI API, Academic Search MCP       |
| Retrieval            | Qdrant, OpenAI embeddings, metadata filtering, reranking    |
| Persistence          | PostgreSQL, Alembic, LangGraph PostgreSQL Checkpointer      |
| Frontend             | React 19, Next.js 15, TypeScript, Tailwind CSS, shadcn/ui   |
| State and networking | TanStack Query, Zustand, Axios                              |
| UX                   | Framer Motion, React Markdown, syntax highlighting          |
| Testing              | Pytest, pytest-asyncio, HTTPX, Vitest, Testing Library, MSW |
| Tooling              | uv, npm, Husky, Docker Compose                              |

## 🚀 Installation

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- Node.js 24.x and npm
- Docker with Docker Compose (recommended), or separate PostgreSQL and Qdrant instances
- OpenAI API key

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd enterprise-ai-workspace
```

### 2. Start PostgreSQL and Qdrant

The included Compose file runs the complete local data layer with persistent
volumes:

```bash
docker compose up -d
docker compose ps
```

| Service    | Local address                     | Purpose                                    |
| ---------- | --------------------------------- | ------------------------------------------ |
| PostgreSQL | `localhost:5432`                  | Application data and LangGraph checkpoints |
| Qdrant     | `http://localhost:6333`           | Document embeddings and metadata           |
| Qdrant UI  | `http://localhost:6333/dashboard` | Local collection inspection                |

The default database credentials are `postgres` / `password`, with database
name `enterprise_ai`. Override `POSTGRES_USER`, `POSTGRES_PASSWORD`,
`POSTGRES_DB`, `POSTGRES_PORT`, `QDRANT_HTTP_PORT`, or `QDRANT_GRPC_PORT` in
your shell or root `.env` when required.

Stop the services without deleting their data:

```bash
docker compose stop
```

### 3. Configure and run the backend

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

RATE_LIMIT_ENABLED=true
RATE_LIMIT_WINDOW_SECONDS=60
RATE_LIMIT_DEFAULT_REQUESTS=120
RATE_LIMIT_CHAT_REQUESTS=30
RATE_LIMIT_UPLOAD_REQUESTS=10

CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

Set `LANGSMITH_TRACING=true` in staging or production to send traces. Every chat
turn is grouped by `conversation_id` and enriched with the HTTP `request_id`.
Do not commit LangSmith or OpenAI API keys.

Install dependencies, apply migrations, and start FastAPI:

```bash
uv venv
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

At startup, LangGraph creates or upgrades its PostgreSQL checkpoint tables
automatically. These tables persist agent state and pending human approvals.
Alembic manages the application tables, while Qdrant collections and payload
indexes are initialized by the backend startup lifecycle.
The application uses the conversation ID for the main agent thread and a
dedicated `conversation:{id}:document-deletion` thread for deletion approval.

Interactive API documentation is available at
[`http://127.0.0.1:8000/docs`](http://127.0.0.1:8000/docs).

### 4. Configure and run the frontend

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Open [`http://localhost:3000`](http://localhost:3000).

The frontend API URL is configured in `frontend/.env.local`:

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

### Run only one infrastructure service

```bash
docker compose up -d postgres
docker compose up -d qdrant
```

For Qdrant Cloud or Neon, keep the unused local service stopped and replace
`QDRANT_URL`, `QDRANT_API_KEY`, or `POSTGRES_URL` in the backend `.env`.

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
├── .github/workflows/
│   ├── ci.yml                  # Backend/frontend validation
│   └── deploy.yml              # CI-gated production deploy hooks
├── app/
│   ├── ai/
│   │   ├── academic_search.py  # Lazy Academic Search MCP bridge
│   │   ├── agent.py            # LangGraph document assistant
│   │   ├── checkpointer.py     # Async PostgreSQL checkpointer lifecycle
│   │   ├── delete_workflow.py  # Deterministic persistent approval workflow
│   │   ├── retriever.py        # Filename routing, retrieval, reranking, citations
│   │   ├── tools.py            # Typed LangChain tools
│   │   └── vectorstore.py      # Qdrant collection and payload indexes
│   ├── api/                    # Conversation, chat, document, and health routes
│   ├── core/
│   │   ├── config/             # Settings, logging, LangSmith, and startup
│   │   ├── observability.py    # JSON logs and LangSmith metrics callbacks
│   │   ├── rate_limit.py       # Endpoint-specific sliding-window limiter
│   │   └── security.py         # PDF content-signature validation
│   ├── db/                     # SQLModel engine and sessions
│   ├── models/                 # Conversation, document, and chat tables
│   ├── repositories/           # PostgreSQL query layer
│   ├── schemas/                # Typed API contracts
│   ├── services/               # Agent, conversation, document, index, and RAG logic
│   ├── dependencies.py         # FastAPI dependency composition
│   └── main.py                 # Application lifespan and router registration
├── frontend/
│   ├── app/                    # Next.js App Router and global styles
│   ├── components/ui/          # Reusable UI and error components
│   ├── features/
│   │   ├── chat/               # Markdown chat, approval UI, and history state
│   │   ├── conversation/       # Optimistic conversation CRUD
│   │   ├── documents/          # Upload, progress, listing, and deletion
│   │   └── health/             # API and PostgreSQL health indicators
│   ├── services/               # Axios and TanStack Query configuration
│   ├── store/                  # Persisted Zustand application state
│   └── test/                   # Vitest and MSW setup
├── migrations/                 # Alembic application-table migrations
├── tests/
│   ├── integration/            # REST API behavior
│   └── unit/                   # RAG, MCP, checkpoint, and delete workflow tests
├── scripts/                    # Metadata recovery utilities
├── docker-compose.yml          # Local PostgreSQL and Qdrant infrastructure
├── pyproject.toml              # Python dependencies and test configuration
├── uv.lock                     # Reproducible Python dependency lock
└── README.md
```

## 🧪 Testing

Backend:

```bash
uv sync
uv run pytest
```

Current backend coverage includes REST integration, retrieval routing, academic
MCP formatting, citation enforcement, PostgreSQL URL handling, persistent
delete approval behavior, rate limiting, observability context, and PDF
signature validation.

Frontend:

```bash
cd frontend
npm install
npm run test
npm run build
```

The frontend suite covers components, hooks, API clients, stores, forms,
markdown/code rendering, approval controls, CRUD behavior, uploads, health
status, and error handling through MSW.

## 📈 Observability

The backend emits one-line JSON logs and returns `X-Request-ID` on every HTTP
response. Supplying an `X-Request-ID` request header preserves the caller's ID;
otherwise the server creates one. Chat traces include:

| Signal            | JSON log / LangSmith representation                         |
| ----------------- | ----------------------------------------------------------- |
| Request ID        | `request_id` on every log and root trace                    |
| Conversation ID   | `conversation_id` metadata for thread grouping              |
| Tool execution    | Tool name, success/failure, and latency child runs          |
| Retrieval latency | `retrieval_latency_ms`, candidate count, and selected count |
| LLM latency       | `llm_latency_ms` per call and chat turn                     |
| Token usage       | Input, output, and total tokens                             |
| Cost per request  | LangSmith automatic model-price cost tracking               |
| Error rate        | Process counters in logs and LangSmith project dashboards   |
| Citation coverage | Cited sources divided by retrieved source markers           |

In LangSmith, open the configured project and use **Monitoring → Dashboard**.
The default dashboard provides trace latency, error rate, tool performance,
tokens, and cost. Create a custom chart for the `citation_coverage` trace
metadata and group operational charts by `conversation_id` when debugging a
thread.

## 🔐 Security Controls

The API applies endpoint-specific sliding-window limits per client:

| Scope           | Default limit |
| --------------- | ------------: |
| Chat and resume |     30/minute |
| PDF upload      |     10/minute |
| Other API calls |    120/minute |

Health checks, OpenAPI, and CORS preflight requests are exempt. Successful
responses include `X-RateLimit-*` headers; rejected requests return HTTP `429`
with `Retry-After`. Limits are configurable through the `RATE_LIMIT_*`
environment variables.

Uploads are checked using both the declared `application/pdf` MIME type and a
PDF `%PDF-x.y` content signature within the first 1,024 bytes. This rejects
common extension/MIME spoofing before parsing or indexing. Signature validation
is not malware scanning; production environments should add antivirus or
content-disarm processing for untrusted public uploads.

The included limiter stores counters in each backend process. Use a shared
Redis-backed limiter before scaling to multiple backend replicas.

## 🔄 CI/CD

GitHub Actions runs CI on every pull request and every push to `main`.

```text
Pull request / push to main
├── Backend
│   ├── uv sync --locked
│   ├── Ruff
│   └── Pytest
└── Frontend
    ├── npm ci
    ├── ESLint
    ├── Vitest + coverage
    └── Next.js production build

Successful CI on main
└── Production environment
    ├── Render backend deploy hook
    └── Vercel frontend deploy hook
```

Create a protected GitHub environment named `production`, then add these
environment secrets under **Settings → Environments → production**:

| Secret                   | Value                                                   |
| ------------------------ | ------------------------------------------------------- |
| `RENDER_DEPLOY_HOOK_URL` | Render backend deploy hook URL                          |
| `VERCEL_DEPLOY_HOOK_URL` | Vercel deploy hook URL configured for the `main` branch |

Treat deploy-hook URLs as passwords. Disable direct automatic production
deployments in the hosting dashboards when using this gated workflow; otherwise
a push can deploy once through the provider's Git integration and again after
CI. Preview deployments may remain enabled for pull requests.

For a human approval gate, enable **Required reviewers** on the GitHub
`production` environment. Production can also be triggered manually from
**Actions → Deploy production → Run workflow**.

## 🗺️ Future Improvements

- Authentication, role-based access control, and organization isolation
- Native server-sent event streaming from FastAPI
- Automated RAG evaluation for recall, faithfulness, and citation accuracy
- Hybrid dense/sparse retrieval and configurable reranking models
- Background document processing with task queues
- Audit logs and Redis-backed distributed rate limiting
- OpenTelemetry export and LangSmith alert policies
- Production backend/frontend container images

## 📄 License

This project is intended for educational and portfolio use. Add a license file
before distributing or using it commercially.
