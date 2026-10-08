from django.urls import path
from .views import (
    DocumentUploadView, DocumentListView, DocumentDetailView, DocumentChatView,
    ComparisonReportListCreateView, ComparisonReportDetailView
)

urlpatterns = [
    path('', DocumentListView.as_view(), name='document-list'),
    path('upload/', DocumentUploadView.as_view(), name='document-upload'),
    path('<uuid:pk>/', DocumentDetailView.as_view(), name='document-detail'),
    path('<uuid:pk>/chat/', DocumentChatView.as_view(), name='document-chat'),
    
    path('comparisons/', ComparisonReportListCreateView.as_view(), name='comparison-list'),
    path('comparisons/<uuid:pk>/', ComparisonReportDetailView.as_view(), name='comparison-detail'),
]