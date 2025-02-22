from rest_framework import serializers

class FileSerializer(serializers.Serializer):
    original_file_name = serializers.CharField(max_length=255)
    file_size = serializers.IntegerField()
    content_type = serializers.CharField(max_length=50)
    
    
class PreSingedUploadSerializer(serializers.Serializer):
    module = serializers.CharField(max_length=64, required=False)
    classify = serializers.CharField(max_length=64, required=False)
    ref_type = serializers.CharField(max_length=64, required=False)
    ref_id = serializers.IntegerField(required=False)
    files = FileSerializer(many=True, required=True)


class DownloadPreSignedSerializer(serializers.Serializer):
    file_id = serializers.CharField(max_length=64)
    file_key = serializers.CharField(max_length=1024)


class DeletePreSignedSerializer(serializers.Serializer):
    file_key = serializers.CharField(max_length=1024)
