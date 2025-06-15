# views.py
from rest_framework import viewsets
from rest_framework.response import Response
from django.conf import settings
from .models import ModelSequenceConfig
from .serializers import ModelSequenceConfigSerializer
from .services.sequence_client import SequenceNumberingClient

class ModelSequenceConfigViewSet(viewsets.ModelViewSet):
    queryset = ModelSequenceConfig.objects.all()
    serializer_class = ModelSequenceConfigSerializer

    def get_client(self):
        return SequenceNumberingClient(settings.SEQUENCE_NUMBERING_SERVICE_URL)

    def perform_create(self, serializer):
        sequence_templates = self.request.data.get("sequence_templates", [])
        instance = serializer.save()

        client = self.get_client()
        for template in sequence_templates:
            client.create_template(template)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        response = super().retrieve(request, *args, **kwargs)
        try:
            client = self.get_client()
            templates = client.get_templates(instance.model_name)
        except Exception as e:
            templates = {"error": str(e)}
        response.data["sequence_templates"] = templates
        return response

    def perform_update(self, serializer):
        sequence_templates = self.request.data.get("sequence_templates", [])
        instance = serializer.save()

        client = self.get_client()
        # optional: delete old templates first
        client.delete_templates(instance.model_name)
        for template in sequence_templates:
            client.create_template(template)

    def perform_destroy(self, instance):
        client = self.get_client()
        client.delete_templates(instance.model_name)
        instance.delete()
