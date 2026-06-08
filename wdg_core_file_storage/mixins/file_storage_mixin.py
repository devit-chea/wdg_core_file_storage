from wdg_core_file_storage.serializers.file_storage_serializer import (
    FileStorageInlineSerializer,
)
from wdg_core_file_storage.wdg_file_metadata.models import FileStorageModel


class FileStorageMixin:
    """
    Reusable mixin to attach related file metadata to any model using ref_type + ref_id.
    Supports single or multiple file output.
    """

    return_single_file = False  # Set this to True in your subclass or serializer to return only the latest file

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._file_map = {}
        meta = getattr(self, "Meta", None)

        if not meta or not hasattr(meta, "model"):
            raise AttributeError(
                "FileStorageMixin requires the parent serializer to define a Meta class with a 'model' attribute."
            )
        model_name = meta.model.__name__.lower()

        instance = getattr(self, "instance", None)
        if instance is not None:
            instances = instance if isinstance(instance, list) else [instance]
            ids = [str(obj.id) for obj in instances]

            files = FileStorageModel.objects.filter(
                ref_type=model_name, ref_id__in=ids, deleted=False
            ).order_by(
                "-create_date"
            )  # So latest is first

            for f in files:
                key = f.ref_id
                if self.return_single_file:
                    if key not in self._file_map:  # only keep latest
                        self._file_map[key] = f
                else:
                    self._file_map.setdefault(key, []).append(f)

    def get_files(self, obj):
        key = str(obj.id)
        if self.return_single_file:
            file = self._file_map.get(key)
            return FileStorageInlineSerializer(file).data if file else None
        else:
            files = self._file_map.get(key, [])
            return FileStorageInlineSerializer(files, many=True).data
