# SpecPilot AI (Backend)

SpecPilot AI is an enterprise-grade document intelligence and Retrieval-Augmented Generation (RAG) platform. It allows users to asynchronously ingest complex documents, perform semantic searches, and conduct multi-document gap analysis using local LLMs.

## Architecture & Tech Stack
*   **Core API:** Python 3.12, Django 5, Django REST Framework (DRF)
*   **Asynchronous Tasks:** Celery + Redis
*   **Database:** PostgreSQL 15
*   **Vector Store:** Milvus 2.4 (Dockerized)
*   **Local AI / RAG:** Ollama (qwen2.5:3b), LangChain, SentenceTransformers (BAAI/bge-small-en-v1.5)
*   **CI/CD:** GitHub Actions (Automated Flake8 Linting & Django Unit Testing)

## Current Status
*   [x] **Phase 1: RAG Orchestration** - Async PDF parsing, semantic chunking, vector storage, and Ollama chat integration. *(Completed)*
*   [ ] **Phase 2: Gap Analysis Engine** - Multi-document semantic comparison and discrepancy reporting. *(In Progress)*

## Local Development Setup

### 1. Prerequisites
*   Docker & Docker Compose
*   Python 3.12+
*   [Ollama](https://ollama.com/) installed locally.

### 2. Start Infrastructure
Boot up PostgreSQL, Redis, and Milvus using Docker Compose:

```

bash
docker compose up -d

```

### 3. Pull the Local LLM
Ensure Ollama is running, then pull the required model:

```

bash
ollama pull qwen2.5:3b

```

### 4. Setup Python Environment

```

bash
python -m venv wenv
wenv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate

```

### 5. Run the Application
You need two terminal windows running simultaneously.

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

## API Documentation
The API is fully documented using OpenAPI 3 (Swagger). Once the Django server is running, navigate to:
*   **Swagger UI:** `http://127.0.0.1:8000/api/docs/`
*   **OpenAPI Schema:** `http://127.0.0.1:8000/api/schema/`
