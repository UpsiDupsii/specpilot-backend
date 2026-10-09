# SpecPilot AI (Backend)

SpecPilot AI is an enterprise-grade document intelligence, Retrieval-Augmented Generation (RAG), and compliance audit platform. It ingests complex multi-format documents asynchronously, performs vector similarity search via Milvus, conducts multi-document semantic gap analysis, and executes autonomous agent workflows using LangGraph and n8n.

---

## Architecture & Tech Stack

* **Core API:** Python 3.12, Django 5, Django REST Framework (DRF)
* **Asynchronous Queue:** Celery + Redis
* **Relational Database:** PostgreSQL 15
* **Vector Store:** Milvus 2.4 (Dockerized, Cosine similarity metric)
* **Local AI & Embeddings:** Ollama (`qwen2.5:3b`), SentenceTransformers (`BAAI/bge-small-en-v1.5`, 384 dimensions)
* **Agent Orchestration:** LangGraph (native `StateGraph` pattern), LangChain Core / Ollama
* **External Automation:** n8n Webhook Integration
* **CI/CD:** GitHub Actions (Automated Flake8 Linting + PostgreSQL test container)

---

## Development Roadmap

* [x] **Phase 1: Core Document Intelligence** — Asynchronous PDF parsing (PyMuPDF), semantic chunking, dual-storage split (Postgres text + Milvus vectors), and single-document RAG chat.
* [x] **Phase 2: Multi-Document Gap Analysis** — Semantic cross-referencing across vector spaces, Celery batch auditing, and schema-enforced JSON gap extraction.
* [x] **Phase 3: Autonomous Agent Workflows** — Cyclic LangGraph ReAct state machine equipped with Milvus vector search, PostgreSQL task persistence, and n8n webhook dispatchers.
* [ ] **Phase 4: React Frontend Integration** — Interactive dashboard, audit comparison workspace, and real-time agent Kanban hub.

---

## API Reference (`/api/v1/`)

### Document Ingestion & RAG (Phase 1)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/documents/upload/` | Upload PDF/TXT, queue async chunking and vector indexing |
| `GET` | `/api/v1/documents/` | List all documents and processing states (`PENDING`, `READY`, etc.) |
| `GET` | `/api/v1/documents/{id}/` | Retrieve document metadata |
| `DELETE` | `/api/v1/documents/{id}/` | Delete document file, Postgres chunks, and Milvus vector collection |
| `POST` | `/api/v1/chat/` | Single-document RAG chat (`document_id`, `message`) |

### Multi-Document Gap Analysis (Phase 2)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/analysis/compare/` | Trigger async comparison (`source_doc_id`, `target_doc_id`) |
| `GET` | `/api/v1/analysis/reports/{id}/` | Fetch comparison report and itemized severity findings |

### Autonomous Agent & Tasks (Phase 3)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/agent/execute/` | Run autonomous LangGraph agent loop with tools (`prompt`) |
| `GET` | `/api/v1/tasks/` | List actionable remediation tasks created by the agent |

---

## Local Development Setup

### 1. Prerequisites
* [Docker Desktop](https://www.docker.com/)
* Python 3.12+
* [Ollama](https://ollama.com/) running locally

### 2. Infrastructure Services
Boot PostgreSQL, Redis, and Milvus via Docker Compose:

```

bash
docker compose up -d

```

### 3. Pull Local LLM Model
Ensure the Ollama daemon is running, then pull the target model:

```

bash
ollama pull qwen2.5:3b

```

### 4. Environment Configuration
Create a `.env` file in the project root:

```

env
DEBUG=True
SECRET_KEY=your-development-secret-key

# Database

DB_NAME=specpilot_db
DB_USER=postgres
DB_PASSWORD=1234
DB_HOST=127.0.0.1
DB_PORT=5432

# Redis & Celery

CELERY_BROKER_URL=redis://127.0.0.1:6379/0

# Milvus

MILVUS_HOST=127.0.0.1
MILVUS_PORT=19530

# Ollama & Embeddings

OLLAMA_BASE_URL=[http://127.0.0.1:11434](http://127.0.0.1:11434)
OLLAMA_MODEL=qwen2.5:3b
EMBEDDING_MODEL_NAME=BAAI/bge-small-en-v1.5

# n8n Automation

N8N_WEBHOOK_URL=[http://127.0.0.1:5678/webhook/specpilot-alerts](http://127.0.0.1:5678/webhook/specpilot-alerts)

```

### 5. Python Environment & Migrations

```

bash
python -m venv wenv
wenv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate

```

### 6. Run the Application
Start the Django development server and Celery background worker in separate terminal windows:

**Terminal 1 (Django Server):**

```

bash
python manage.py runserver

```

**Terminal 2 (Celery Worker):**

```

bash
celery -A specpilot_core worker --loglevel=info -P solo

```

---

## Running Tests

Execute the complete unit test suite across all apps:

```

bash
python manage.py test

```

All external dependencies (Milvus, Ollama, Celery tasks, and n8n HTTP requests) are mocked to ensure fast, deterministic offline testing in CI/CD pipelines.

---

## API Documentation

Once the server is running, explore the interactive OpenAPI schema:
* **Swagger UI:** `http://127.0.0.1:8000/api/docs/`
* **OpenAPI Schema:** `http://127.0.0.1:8000/api/schema/`
