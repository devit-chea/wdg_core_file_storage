from django.urls import include, path
from rest_framework import routers

from wdg_core_file_storage.views.FileStorageViewSet import (
    FileStorageByRefView,
    FileStorageViewSet,
)

router = routers.DefaultRouter(trailing_slash=False)
router.register(r"file-storage", FileStorageViewSet)

urlpatterns = [
    path(
        "file-storage/by-ref",
        FileStorageByRefView.as_view(),
        name="file_storage_by_ref",
    ),
    path("", include(router.urls)),
]
