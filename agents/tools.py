import os
import requests
from langchain_core.tools import tool

from documents.milvus_utils import get_milvus_client
from documents.models import DocumentChunk
from documents.views import embedder
from .models import ActionableTask, TaskPriority


@tool
def search_documents(query: str, limit: int = 4) -> str:
    """
    Search indexed documents for relevant technical, compliance, or requirement context.
    Use this whenever you need factual information or context from uploaded files.
    """
    try:
        query_vector = embedder.encode(query).tolist()
        client, collection_name = get_milvus_client()

        results = client.search(
            collection_name=collection_name,
            data=[query_vector],
            limit=limit,
            search_params={"metric_type": "COSINE", "params": {"nprobe": 10}}
        )
        client.close()

        if not results or not results[0]:
            return "No relevant document chunks found."

        chunk_ids = [hit['id'] for hit in results[0]]
        chunks = DocumentChunk.objects.filter(id__in=chunk_ids)

        if not chunks.exists():
            return "No chunk text matches found in the database."

        formatted_context = []
        for c in chunks:
            formatted_context.append(f"[{c.document.title} - Chunk #{c.chunk_index}]:\n{c.text_content}")

        return "\n\n---\n\n".join(formatted_context)
    except Exception as e:
        return f"Document search failed: {str(e)}"


@tool
def create_actionable_task(title: str, description: str, priority: str = "MEDIUM") -> str:
    """
    Create an actionable task in the system when an audit issue, remediation step, or policy violation is identified.
    Priority must be one of: 'LOW', 'MEDIUM', 'HIGH', or 'CRITICAL'.
    """
    try:
        norm_priority = priority.upper()
        if norm_priority not in TaskPriority.values:
            norm_priority = TaskPriority.MEDIUM

        task = ActionableTask.objects.create(
            title=title,
            description=description,
            priority=norm_priority
        )
        return f"Successfully created task ID: {task.id} with title: '{task.title}' [Priority: {task.priority}]"
    except Exception as e:
        return f"Failed to create task: {str(e)}"


@tool
def send_webhook_notification(event_type: str, message: str) -> str:
    """
    Trigger an external webhook alert to n8n for Slack, email, or escalation workflows.
    Use this when high or critical issues are found, or when the user explicitly requests notifications.
    """
    webhook_url = os.getenv('N8N_WEBHOOK_URL', 'http://127.0.0.1:5678/webhook/specpilot-alerts')
    payload = {
        "event": event_type,
        "message": message,
        "source": "SpecPilot Agent"
    }

    try:
        resp = requests.post(webhook_url, json=payload, timeout=10)
        return f"Notification dispatched to n8n (HTTP {resp.status_code})"
    except requests.exceptions.RequestException as e:
        return f"Webhook notification failed (n8n might be offline): {str(e)}"
    