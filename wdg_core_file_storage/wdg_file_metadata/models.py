import uuid

from django.conf import settings
from django.db import models

from wdg_core_file_storage.base import MultiStorage
from wdg_core_file_storage.constants import StorageProvider, UploadStatus

abstract = "wdg_core_file_storage.wdg_file_metadata" not in settings.INSTALLED_APPS


class FileStorageModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file_id = models.UUIDField(default=uuid.uuid4, editable=False)
    image_url = models.FileField(
        max_length=1024, db_column="image_url", storage=MultiStorage(backend_name="s3")
    )
    file_path = models.TextField(max_length=1024, blank=False, null=True)
    file_type = models.CharField(max_length=255, blank=False, null=True)
    description = models.TextField(blank=False, null=True)
    ref_type = models.CharField(max_length=100, blank=True, null=True)
    ref_id = models.CharField(max_length=100, blank=True, null=True)
    file_name = models.CharField(max_length=250, blank=False, null=True)
    original_file_name = models.CharField(max_length=255, blank=False, null=True)
    file_size = models.CharField(max_length=250, blank=False, null=True)
    deleted = models.BooleanField(default=False, blank=True, null=True)
    storage_provider = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        default=StorageProvider.S3,
        choices=StorageProvider.CHOICES,
    )
    upload_status = models.CharField(
        max_length=64,
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
        abstract = abstract

    def __str__(self) -> str:
        return self.original_file_name or self.file_name
