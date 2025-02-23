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
    
    
class FileStorageSaveMetaDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileStorageModel
        fields = "__all__"
        

class FileInfoSerializer(serializers.Serializer):
    original_file_name = serializers.CharField(required=True, allow_blank=False)
    file_size = serializers.IntegerField(required=True)
    content_type = serializers.CharField(required=True)
    file_path = serializers.CharField(required=True)


class FileStorageCreateValidateSerializer(serializers.Serializer):
    file_info = serializers.ListField(child=FileInfoSerializer(), allow_empty=False)