import os
import requests
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from sentence_transformers import SentenceTransformer

from .models import Document, DocumentChunk
from .serializers import DocumentSerializer
from .tasks import process_document_task
from .milvus_utils import get_milvus_client

MODEL_NAME = os.getenv('EMBEDDING_MODEL_NAME', 'BAAI/bge-small-en-v1.5')
embedder = SentenceTransformer(MODEL_NAME)

class DocumentUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        serializer = DocumentSerializer(data=request.data)
        if serializer.is_valid():
            document = serializer.save()
            task = process_document_task.delay(str(document.id))
            return Response({
                "message": "File received. Ingestion queued.",
                "document_id": document.id,
                "task_id": task.id,
                "status": document.status
            }, status=status.HTTP_202_ACCEPTED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DocumentListView(generics.ListAPIView):
    queryset = Document.objects.all().order_by('-created_at')
    serializer_class = DocumentSerializer

class DocumentDetailView(generics.RetrieveDestroyAPIView):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer

    def perform_destroy(self, instance):
        try:
            client, collection_name = get_milvus_client()
            client.delete(collection_name=collection_name, filter=f"document_id == '{instance.id}'")
            client.close()
        except Exception as e:
            print(f"Error deleting from Milvus: {e}")
        
        instance.file.delete(save=False)
        instance.delete()

class DocumentChatView(APIView):
    def post(self, request, pk):
        query = request.data.get('query')
        if not query:
            return Response({"error": "Query is required"}, status=status.HTTP_400_BAD_REQUEST)

        query_vector = embedder.encode(query).tolist()

        try:
            client, collection_name = get_milvus_client()
            results = client.search(
                collection_name=collection_name,
                data=[query_vector],
                limit=5,
                filter=f"document_id == '{pk}'",
                search_params={"metric_type": "COSINE", "params": {"nprobe": 10}}
            )
            client.close()
        except Exception as e:
            return Response({"error": f"Milvus search failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if not results or not results[0]:
            return Response({"answer": "No relevant information found in this document."})

        chunk_ids = [hit['id'] for hit in results[0]]
        chunks = DocumentChunk.objects.filter(id__in=chunk_ids)
        context = "\n\n".join([chunk.text_content for chunk in chunks])

        ollama_url = f"{os.getenv('OLLAMA_BASE_URL', 'http://127.0.0.1:11434')}/api/generate"
        prompt = f"Use the following document context to answer the user's question.\n\nContext:\n{context}\n\nQuestion: {query}\nAnswer:"
        
        llm_payload = {
            "model": os.getenv('OLLAMA_MODEL', 'qwen2.5:3b'),
            "prompt": prompt,
            "stream": False
        }

        try:
            llm_response = requests.post(ollama_url, json=llm_payload)
            llm_response.raise_for_status()
            answer = llm_response.json().get('response', '')
            return Response({"answer": answer.strip()})
        except requests.exceptions.RequestException as e:
            return Response({"error": f"LLM backend error: {str(e)}"}, status=status.HTTP_502_BAD_GATEWAY)
        