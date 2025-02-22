from rest_framework import serializers

from wdg_core_file_storage.wdg_file_metadata.models import FileStorageModel


class FileStorageSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileStorageModel
        fields = "__all__"


class FileStorageValidateByRefSerializer(serializers.Serializer):
    ref_type = serializers.CharField()
    ref_id = serializers.IntegerField(required=False)
    
class FileStorageDeleteValidateSerializer(serializers.Serializer):
    id = serializers.CharField()
    file_path = serializers.CharField()
    
    
class FileStoragePreviewValidateSerializer(serializers.Serializer):
    id = serializers.CharField()
    file_id = serializers.CharField()
    file_name = serializers.CharField()
    