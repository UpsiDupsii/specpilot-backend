from rest_framework import serializers
from .models import Document, ComparisonReport, GapFinding

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ['id', 'title', 'file', 'status', 'error_message', 'created_at']
        read_only_fields = ['id', 'status', 'error_message', 'created_at']
    
class GapFindingSerializer(serializers.ModelSerializer):
    class Meta:
        model = GapFinding
        fields = '__all__'

class ComparisonReportSerializer(serializers.ModelSerializer):
    findings = GapFindingSerializer(many=True, read_only=True)

    class Meta:
        model = ComparisonReport
        fields = [
            'id', 'source_document', 'target_document', 
            'status', 'error_message', 'created_at', 'findings'
        ]
        read_only_fields = ['id', 'status', 'error_message', 'created_at', 'findings']
        