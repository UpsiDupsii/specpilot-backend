# SpecPilot AI Backend

SpecPilot AI is an enterprise-grade document intelligence and workflow automation platform. It allows organizations to upload standard operating procedures (SOPs), ISO documents, and contracts, enabling them to chat with their documents, perform automated cross-document gap analysis, and trigger autonomous workflows.

This repository contains the backend microservices architecture, built with an API-first approach.

## Architecture & Tech Stack

The system is designed for local, resource-constrained execution (optimized for 4GB VRAM) using quantized GGUF models, demonstrating robust system design, asynchronous processing, and separation of concerns.

* **Core Framework:** Python 3.12, Django 5, Django REST Framework
* **Task Broker & Caching:** Redis
* **Asynchronous Workers:** Celery
* **Relational Database:** PostgreSQL (App Metadata & Document Text)
* **Vector Database:** Milvus (Embeddings & Semantic Search)
* **AI/RAG Layer:** Ollama (Qwen2.5:7B / Llama 3.1 8B), LangChain/LlamaIndex
* **Agentic Orchestration:** LangGraph
* **Workflow Automation:** n8n Webhooks
* **Deployment:** Docker & Docker Compose

## Phase Roadmap

### Phase 1: Core Document Intelligence
- Multipart document ingestion (PDF, DOCX, TXT).
- Asynchronous chunking and embedding generation via Celery.
- Vector storage in Milvus with metadata isolated in PostgreSQL.
- Retrieval-Augmented Generation (RAG) chat endpoints.

### Phase 2: Multi-Document RAG
- Cross-document retrieval and semantic comparison.
- Automated compliance checking and gap analysis matrix generation (e.g., comparing an internal SOP against an ISO standard).

### Phase 3: Agentic Workflows
- LangGraph-powered AI agents capable of autonomous tool-calling.
- Automatic extraction of remediation tasks.
- Integration with external workflow engines (n8n) via webhooks.

## Local Development Setup

(Instructions to be added as infrastructure is finalized)