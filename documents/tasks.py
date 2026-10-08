import os
import json
import logging
import requests
from celery import shared_task
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter
import pymupdf

from .models import Document, DocumentChunk, DocumentStatus, ComparisonReport, GapFinding
from .milvus_utils import get_milvus_client

logger = logging.getLogger(__name__)

# Load the embedding model using the environment variable configuration
MODEL_NAME = os.getenv('EMBEDDING_MODEL_NAME', 'BAAI/bge-small-en-v1.5')
embedder = SentenceTransformer(MODEL_NAME)

@shared_task
def process_document_task(document_id):
    try:
        document = Document.objects.get(id=document_id)
        document.status = DocumentStatus.PROCESSING
        document.save()

        # 1. Extract Text
        text_content = ""
        with pymupdf.open(document.file.path) as pdf:
            for page in pdf:
                text_content += page.get_text() + "\n"

        # 2. Chunk the Text
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100,
            separators=["\n\n", "\n", " ", ""]
        )
        chunks = text_splitter.split_text(text_content)

        # 3. Process and Store Chunks
        client, collection_name = get_milvus_client()
        
        data_to_insert = []
        for index, chunk_text in enumerate(chunks):
            db_chunk = DocumentChunk.objects.create(
                document=document,
                chunk_index=index,
                text_content=chunk_text
            )
            
            data_to_insert.append({
                "chunk_id": str(db_chunk.id),
                "document_id": str(document.id),
                "embedding": embedder.encode(chunk_text).tolist()
            })

        # 4. Bulk Insert into Milvus
        if data_to_insert:
            client.insert(collection_name=collection_name, data=data_to_insert)

        # CRITICAL: Close the connection to release the Windows file lock
        client.close()

        document.status = DocumentStatus.READY
        document.save()
        logger.info(f"Successfully processed document: {document_id}")

    except Exception as e:
        logger.error(f"Failed to process document {document_id}: {str(e)}")
        Document.objects.filter(id=document_id).update(
            status=DocumentStatus.FAILED,
            error_message=str(e)
        )

@shared_task
def run_comparison_task(report_id):
    try:
        report = ComparisonReport.objects.get(id=report_id)
        report.status = DocumentStatus.PROCESSING
        report.save()

        source_doc = report.source_document
        target_doc = report.target_document

        client, collection_name = get_milvus_client()
        ollama_url = f"{os.getenv('OLLAMA_BASE_URL', 'http://127.0.0.1:11434')}/api/generate"
        ollama_model = os.getenv('OLLAMA_MODEL', 'qwen2.5:3b')

        source_chunks = list(DocumentChunk.objects.filter(document=source_doc))
        total_chunks = len(source_chunks)
        logger.info(f"Starting comparison: {total_chunks} source chunks to evaluate against {target_doc.title}")

        for index, chunk in enumerate(source_chunks, start=1):
            logger.info(f"[{index}/{total_chunks}] Processing chunk {chunk.id}...")

            query_vector = embedder.encode(chunk.text_content).tolist()

            results = client.search(
                collection_name=collection_name,
                data=[query_vector],
                limit=3,
                filter=f"document_id == '{target_doc.id}'",
                search_params={"metric_type": "COSINE", "params": {"nprobe": 10}}
            )

            target_context = "No relevant context found in target document."
            if results and results[0]:
                chunk_ids = [hit['id'] for hit in results[0]]
                target_chunks = DocumentChunk.objects.filter(id__in=chunk_ids)
                target_context = "\n\n".join([tc.text_content for tc in target_chunks])

            prompt = f"""You are an expert compliance auditor. Compare the Source Requirement against the Target Context.

Source Requirement:
{chunk.text_content}

Target Context:
{target_context}

Determine if the Target Context fully satisfies the Source Requirement, or if there is a gap, missing information, or contradiction.
Respond strictly in valid JSON format with the following keys:
"has_gap": boolean (true if there is a gap/contradiction, false if fully satisfied)
"severity": string (only use "LOW", "MEDIUM", "HIGH", or "CRITICAL")
"analysis": string (explain the gap or state it is satisfied)
"""

            llm_payload = {
                "model": ollama_model,
                "prompt": prompt,
                "stream": False,
                "format": "json"
            }

            try:
                # 60-second timeout ensures Ollama doesn't hang the worker
                llm_response = requests.post(ollama_url, json=llm_payload, timeout=60)
                llm_response.raise_for_status()
                response_text = llm_response.json().get('response', '')

                result = json.loads(response_text)

                if result.get('has_gap') is True:
                    GapFinding.objects.create(
                        report=report,
                        requirement_text=chunk.text_content,
                        analysis=result.get('analysis', 'Gap identified.'),
                        severity=result.get('severity', 'MEDIUM').upper(),
                        source_chunk_id=str(chunk.id)
                    )
                    logger.info(f"[{index}/{total_chunks}] -> Gap detected ({result.get('severity')})")
                else:
                    logger.info(f"[{index}/{total_chunks}] -> Requirement satisfied")

            except Exception as llm_error:
                logger.warning(f"[{index}/{total_chunks}] LLM failed for chunk {chunk.id}: {str(llm_error)}")
                continue

        client.close()
        report.status = DocumentStatus.READY
        report.save()
        logger.info(f"Comparison report complete: {report_id}")

    except Exception as e:
        logger.error(f"Comparison task failed for {report_id}: {str(e)}")
        ComparisonReport.objects.filter(id=report_id).update(
            status=DocumentStatus.FAILED,
            error_message=str(e)
        )
