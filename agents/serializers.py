from rest_framework import serializers
from .models import ActionableTask


class ActionableTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActionableTask
        fields = '__all__'


class AgentExecuteInputSerializer(serializers.Serializer):
    prompt = serializers.CharField(required=True)
    