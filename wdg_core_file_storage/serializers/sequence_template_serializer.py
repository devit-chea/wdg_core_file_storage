from rest_framework import serializers


class SequenceTemplateProxySerializer(serializers.Serializer):
    code = serializers.CharField()
    name = serializers.CharField()
    is_enabled = serializers.BooleanField()
    reset_type = serializers.ChoiceField(
        choices=["MANUAL", "DAILY", "MONTHLY", "YEARLY"]
    )
    prefix = serializers.CharField()
    padding = serializers.IntegerField()
    start_number = serializers.IntegerField()
    current_number = serializers.IntegerField()
    

class ModelSequenceConfigSerializer(serializers.ModelSerializer):
    sequence_templates = SequenceTemplateProxySerializer(many=True, required=False)

    class Meta:
        model = "ModelSequenceConfig" # Replace with actual model name
        fields = ['id', 'model_name', 'is_enabled', 'description', 'sequence_templates']

