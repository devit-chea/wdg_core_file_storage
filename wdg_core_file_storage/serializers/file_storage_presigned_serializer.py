from rest_framework import serializers

class FileSerializer(serializers.Serializer):
    original_file_name = serializers.CharField(max_length=255)
    file_size = serializers.IntegerField()
    file_type = serializers.CharField(max_length=50)
    
    
class PreSingedUploadSerializer(serializers.Serializer):
    module = serializers.CharField(max_length=64, required=False)
    classify = serializers.CharField(max_length=64, required=False)
    ref_type = serializers.CharField(max_length=64, required=False)
    ref_id = serializers.IntegerField(required=False)
    is_save_metadata = serializers.BooleanField(default=False, required=False)
    files = FileSerializer(many=True, required=True)


class DownloadPreSignedSerializer(serializers.Serializer):
    bucket_name = serializers.CharField(max_length=100, required=False)
    file_path = serializers.CharField(max_length=1024)


class DeletePreSignedSerializer(serializers.Serializer):
    bucket_name = serializers.CharField(max_length=100, required=False)
    file_path = serializers.CharField(max_length=1024)
