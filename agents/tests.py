from unittest.mock import patch, MagicMock
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from .models import ActionableTask, TaskPriority, AgentTaskStatus
from .tools import create_actionable_task, send_webhook_notification


class AgentAPITests(APITestCase):
    def setUp(self):
        self.task = ActionableTask.objects.create(
            title="Review encryption policy",
            description="Ensure AES-256 is enforced across databases.",
            priority=TaskPriority.HIGH,
            status=AgentTaskStatus.PENDING
        )

    def test_task_list(self):
        """Test fetching all actionable tasks."""
        url = reverse('task-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], "Review encryption policy")
        self.assertEqual(response.data[0]['priority'], "HIGH")

    @patch('agents.views.execute_agent_workflow')
    def test_agent_execute_success(self, mock_workflow):
        """Test executing the agent via POST /api/v1/agent/execute/."""
        mock_workflow.return_value = {
            "output": "Analyzed document and logged 1 critical remediation task.",
            "total_messages": 4
        }
        url = reverse('agent-execute')
        payload = {"prompt": "Check compliance on encryption standards."}

        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['prompt'], payload['prompt'])
        self.assertIn("remediation task", response.data['response'])
        self.assertEqual(response.data['steps_taken'], 4)
        mock_workflow.assert_called_once_with(payload['prompt'])

    def test_agent_execute_missing_prompt(self):
        """Test validation error when prompt is missing."""
        url = reverse('agent-execute')
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('prompt', response.data)

    def test_tool_create_actionable_task(self):
        """Test tool creation of an ActionableTask directly."""
        result = create_actionable_task.invoke({
            "title": "Patch API Gateway",
            "description": "Fix rate limiting vulnerability",
            "priority": "CRITICAL"
        })
        self.assertIn("Successfully created task", result)
        self.assertTrue(ActionableTask.objects.filter(title="Patch API Gateway").exists())
        task = ActionableTask.objects.get(title="Patch API Gateway")
        self.assertEqual(task.priority, TaskPriority.CRITICAL)

    @patch('agents.tools.requests.post')
    def test_tool_send_webhook_notification(self, mock_post):
        """Test dispatching a notification to n8n webhook."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        result = send_webhook_notification.invoke({
            "event_type": "Security Violation",
            "message": "Critical vulnerability detected in document."
        })
        self.assertIn("Notification dispatched to n8n (HTTP 200)", result)
        mock_post.assert_called_once()