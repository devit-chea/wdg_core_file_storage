from rest_framework import serializers


class PreSingedUploadSerializer(serializers.Serializer):
    file_id = serializers.CharField(max_length=64)
    ref_type = serializers.CharField(max_length=64)
    ref_id = serializers.IntegerField()


class DownloadPreSignedSerializer(serializers.Serializer):
    file_id = serializers.CharField(max_length=64)
    file_key = serializers.CharField(max_length=1024)


class DeletePreSignedSerializer(serializers.Serializer):
    file_key = serializers.CharField(max_length=1024)
