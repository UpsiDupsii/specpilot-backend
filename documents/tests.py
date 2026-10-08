from unittest.mock import patch, MagicMock
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.core.files.uploadedfile import SimpleUploadedFile

from .models import Document, DocumentChunk, DocumentStatus

class DocumentAPITests(APITestCase):
    def setUp(self):
        # Create a sample document and chunk for database tests
        self.pdf_content = b"%PDF-1.4\n%Fake PDF content"
        self.file = SimpleUploadedFile("test_doc.pdf", self.pdf_content, content_type="application/pdf")
        
        self.document = Document.objects.create(
            title="Test Document",
            file=self.file,
            status=DocumentStatus.READY
        )
        
        self.chunk = DocumentChunk.objects.create(
            document=self.document,
            chunk_index=0,
            text_content="This is the text content of the test document."
        )

    def test_document_list(self):
        """Test fetching the list of documents"""
        url = reverse('document-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check the list directly instead of looking for 'results'
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], "Test Document")

    def test_document_detail(self):
        """Test fetching a single document"""
        url = reverse('document-detail', args=[self.document.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], "Test Document")

    @patch('documents.views.process_document_task.delay')
    def test_document_upload(self, mock_task_delay):
        """Test document upload and verify the Celery task is dispatched"""
        # Mock the Celery task response
        mock_task_delay.return_value = MagicMock(id='fake-task-id')
        
        url = reverse('document-upload')
        new_file = SimpleUploadedFile("new_doc.pdf", self.pdf_content, content_type="application/pdf")
        data = {'title': 'New Upload', 'file': new_file}
        
        response = self.client.post(url, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(Document.objects.count(), 2)
        mock_task_delay.assert_called_once()

    @patch('documents.views.get_milvus_client')
    def test_document_delete(self, mock_get_milvus):
        """Test document deletion and verify Milvus delete is called"""
        # Mock the Milvus client
        mock_client = MagicMock()
        mock_get_milvus.return_value = (mock_client, 'document_chunks')
        
        url = reverse('document-detail', args=[self.document.id])
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Document.objects.count(), 0)
        mock_client.delete.assert_called_once()
        mock_client.close.assert_called_once()

    @patch('documents.views.requests.post')
    @patch('documents.views.get_milvus_client')
    @patch('documents.views.embedder.encode')
    def test_document_chat(self, mock_encode, mock_get_milvus, mock_requests_post):
        """Test the RAG chat pipeline with mocked embeddings, Milvus, and Ollama"""
        # 1. Mock the embedding model so .tolist() works
        mock_encode_result = MagicMock()
        mock_encode_result.tolist.return_value = [0.1] * 384
        mock_encode.return_value = mock_encode_result
        
        # 2. Mock Milvus search returning the ID of our setUp chunk
        mock_client = MagicMock()
        mock_client.search.return_value = [[{'id': str(self.chunk.id)}]]
        mock_get_milvus.return_value = (mock_client, 'document_chunks')
        
        # 3. Mock the Ollama HTTP response
        mock_response = MagicMock()
        mock_response.json.return_value = {'response': 'This is a mocked LLM answer.'}
        mock_response.raise_for_status.return_value = None
        mock_requests_post.return_value = mock_response

        url = reverse('document-chat', args=[self.document.id])
        data = {'query': 'What is the content?'}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['answer'], 'This is a mocked LLM answer.')
        mock_requests_post.assert_called_once()