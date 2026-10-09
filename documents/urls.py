from django.urls import path
from .views import (
    DocumentUploadView, DocumentListView, DocumentDetailView, DocumentChatView,
    ComparisonReportListCreateView, ComparisonReportDetailView, ChatAPIView
)

urlpatterns = [
    # Phase 1 Documents
    path('documents/', DocumentListView.as_view(), name='document-list'),
    path('documents/upload/', DocumentUploadView.as_view(), name='document-upload'),
    path('documents/<uuid:pk>/', DocumentDetailView.as_view(), name='document-detail'),
    path('documents/<uuid:pk>/chat/', DocumentChatView.as_view(), name='document-chat'),

    # Phase 1 Blueprint Chat
    path('chat/', ChatAPIView.as_view(), name='global-chat'),

    # Phase 2 Blueprint Analysis
    path('analysis/compare/', ComparisonReportListCreateView.as_view(), name='analysis-compare'),
    path('analysis/reports/<uuid:pk>/', ComparisonReportDetailView.as_view(), name='analysis-report-detail'),

    # Backward compatibility aliases
    path('documents/comparisons/', ComparisonReportListCreateView.as_view(), name='comparison-list'),
    path('documents/comparisons/<uuid:pk>/', ComparisonReportDetailView.as_view(), name='comparison-detail'),
]