from django.urls import path
from .views import AgentExecuteView, TaskListView

urlpatterns = [
    path('agent/execute/', AgentExecuteView.as_view(), name='agent-execute'),
    path('tasks/', TaskListView.as_view(), name='task-list'),
]