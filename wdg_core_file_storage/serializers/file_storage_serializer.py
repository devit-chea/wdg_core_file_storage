from rest_framework import serializers

from wdg_core_file_storage.utils.ref_instance_map_util import build_ref_instance_map
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


class FileStorageRelatedSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileStorageModel
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if hasattr(self, "instance"):
            self._ref_map = build_ref_instance_map(
                self.instance if hasattr(self.instance, "__iter__") else [self.instance]
            )

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        key = (instance.ref_type.lower(), instance.ref_id)
        related_obj = self._ref_map.get(key)
        if related_obj:
            rep["related_name"] = getattr(
                related_obj, "name", None
            )  # or whatever field you want
        return rep
