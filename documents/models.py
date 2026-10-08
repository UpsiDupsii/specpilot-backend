import uuid
from django.db import models

class DocumentStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    PROCESSING = 'PROCESSING', 'Processing'
    READY = 'READY', 'Ready'
    FAILED = 'FAILED', 'Failed'

class Document(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='uploads/documents/')
    status = models.CharField(
        max_length=20, 
        choices=DocumentStatus.choices, 
        default=DocumentStatus.PENDING
    )
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class DocumentChunk(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='chunks')
    chunk_index = models.IntegerField()
    text_content = models.TextField()
    page_number = models.IntegerField(null=True, blank=True)
    
    class Meta:
        ordering = ['chunk_index']

    def __str__(self):
        return f"{self.document.title} - Chunk {self.chunk_index}"
    
    