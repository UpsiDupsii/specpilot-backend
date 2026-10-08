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
    
    
class ComparisonReport(models.Model):
    """Tracks the asynchronous background job of comparing two documents."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source_document = models.ForeignKey(
        Document, on_delete=models.CASCADE, related_name='source_comparisons'
    )
    target_document = models.ForeignKey(
        Document, on_delete=models.CASCADE, related_name='target_comparisons'
    )
    status = models.CharField(
        max_length=20, 
        choices=DocumentStatus.choices, 
        default=DocumentStatus.PENDING
    )
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Comparison: {self.source_document.title} vs {self.target_document.title}"


class GapFinding(models.Model):
    """Stores individual discrepancies found by the LLM during comparison."""
    class Severity(models.TextChoices):
        LOW = 'LOW', 'Low'
        MEDIUM = 'MEDIUM', 'Medium'
        HIGH = 'HIGH', 'High'
        CRITICAL = 'CRITICAL', 'Critical'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report = models.ForeignKey(ComparisonReport, on_delete=models.CASCADE, related_name='findings')
    requirement_text = models.TextField(help_text="The requirement from the source document.")
    analysis = models.TextField(help_text="The LLM's explanation of the gap or contradiction.")
    severity = models.CharField(max_length=20, choices=Severity.choices, default=Severity.MEDIUM)
    
    # Optional: Store the Milvus chunk ID that triggered this finding for traceability
    source_chunk_id = models.CharField(max_length=36, blank=True, null=True)

    def __str__(self):
        return f"[{self.severity}] Gap in {self.report.id}"    
