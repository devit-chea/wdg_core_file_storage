from django.urls import include, path
from rest_framework import routers

from wdg_core_file_storage.views.PresigndFileStorageViewSet import (
    GenerateDeletePresignedUrlView,
    GenerateDownloadPresignedUrlView,
    GenerateUploadPresignedUrlView,
)


router = routers.DefaultRouter(trailing_slash=False)

urlpatterns = [
    path(
        "file-storage/generate-upload-presigned-url",
        GenerateUploadPresignedUrlView.as_view(),
        name="file_storage_generate_presigned_url",
    ),
    path(
        "file-storage/generate-download-presigned-url",
        GenerateDownloadPresignedUrlView.as_view(),
        name="file_storage_generate_download_presigned_url",
    ),
    path(
        "file-storage/generate-delete-presigned-url",
        GenerateDeletePresignedUrlView.as_view(),
        name="file-storage_generate_delete_presigned_url",
    ),
    
    path("", include(router.urls)),
]
