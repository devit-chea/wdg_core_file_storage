import uuid

from django.conf import settings
from base import MultiStorage
from django.db import models

from wdg_file_storage.constants import StorageProvider, UploadStatus


class FileStorageModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file_id = models.UUIDField(default=uuid.uuid4, editable=False)
    image_url = models.FileField(
        max_length=1024, db_column="image_url", storage=MultiStorage(backend_name="s3")
    )
    file_path = models.FileField(
        max_length=1024, blank=False, null=True, storage=MultiStorage(backend_name="s3")
    )
    file_type = models.CharField(max_length=255, blank=False, null=True)
    description = models.TextField(blank=False, null=True)
    ref_type = models.CharField(max_length=100, blank=True, null=True)
    ref_id = models.CharField(max_length=100, blank=True, null=True)
    file_name = models.CharField(max_length=250, blank=False, null=True)
    original_file_name = models.CharField(max_length=255, blank=False, null=True)
    file_size = models.CharField(max_length=250, blank=False, null=True)
    deleted = models.BooleanField(default=False, blank=True, null=True)
    storage_provider = models.CharField(
        blank=True,
        null=True,
        default=StorageProvider.S3,
        choices=StorageProvider.CHOICES,
    )
    upload_status = models.CharField(
        blank=True,
        null=True,
        default=UploadStatus.PENDING,
        choices=UploadStatus.CHOICES,
    )
    create_date = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    write_date = models.DateTimeField(auto_now=True, blank=True, null=True)
    create_uid = models.IntegerField(blank=True, null=True, editable=False)
    write_uid = models.IntegerField(blank=True, null=True, editable=False)

    class Meta:
    #     db_table = "file_storage"
        abstract = (
            "wdg_file_storage.file_storage" not in settings.INSTALLED_APPS
        )

    def __str__(self) -> str:
        return self.original_file_name or self.file_name
