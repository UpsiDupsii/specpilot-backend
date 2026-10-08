import os
import logging
from celery import shared_task
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter
import pymupdf

from .models import Document, DocumentChunk, DocumentStatus
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