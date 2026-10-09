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
    source_doc_id = serializers.PrimaryKeyRelatedField(
        queryset=Document.objects.all(), source='source_document', write_only=True, required=False
    )
    target_doc_id = serializers.PrimaryKeyRelatedField(
        queryset=Document.objects.all(), source='target_document', write_only=True, required=False
    )
    source_document = serializers.PrimaryKeyRelatedField(
        queryset=Document.objects.all(), required=False
    )
    target_document = serializers.PrimaryKeyRelatedField(
        queryset=Document.objects.all(), required=False
    )
    findings = GapFindingSerializer(many=True, read_only=True)

    class Meta:
        model = ComparisonReport
        fields = [
            'id', 'source_document', 'target_document',
            'source_doc_id', 'target_doc_id',
            'status', 'error_message', 'created_at', 'findings'
        ]
        read_only_fields = ['id', 'status', 'error_message', 'created_at', 'findings']

    def validate(self, attrs):
        # Resolve source doc
        source = attrs.get('source_document')
        target = attrs.get('target_document')

        if not source:
            raise serializers.ValidationError({"source_doc_id": "This field is required."})
        if not target:
            raise serializers.ValidationError({"target_doc_id": "This field is required."})

        return attrs

        