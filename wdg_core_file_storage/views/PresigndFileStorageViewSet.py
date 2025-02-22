import logging
from django.conf import settings
from rest_framework import views, status
from django.db import transaction
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from wdg_core_file_storage.backends.s3 import S3Client
from wdg_core_file_storage.constants import StorageClassify, StorageModule, StorageProvider
from wdg_core_file_storage.serializers.file_storage_presigned_serializer import (
    DeletePreSignedSerializer,
    DownloadPreSignedSerializer,
    PreSingedUploadSerializer,
)
import uuid

from wdg_core_file_storage.services.save_file_metadata_service import SaveFileMetaService
from wdg_core_file_storage.utils.file_util import add_slash, unique_file_name_by_original

logger = logging.getLogger(__name__)


class GenerateUploadPresignedUrlView(views.APIView):
    permission_classes = []
    serializer_class = PreSingedUploadSerializer

    # To be generate presigned URL for upload to s3 direct
    def post(self, request, *args, **kwargs):
        # Validate input using the serializer
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not serializer.is_valid():
            return Response({"message": serializer.errors}, status=400)
        
        files_metadata = serializer.validated_data.get("files", [])
        hr_employee = serializer.validated_data.get("hr_employee", None)
        ref_type = serializer.validated_data.get("ref_type", None)
        ref_id = serializer.validated_data.get("ref_id", None)
        classify = serializer.validated_data.get("classify", add_slash(StorageClassify.TEMPS))
        module = serializer.validated_data.get("module", StorageModule.GENERIC)
        expiry = serializer.validated_data.get("expiry", settings.S3_PRESIGNED_EXPIRE)

        if not files_metadata:
            return Response(
                {"error": "No files metadata provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        presigned_urls = []

        try:
            with transaction.atomic():
                for file_meta in files_metadata:
                    original_file_name = file_meta["original_file_name"]
                    file_size = file_meta["file_size"]
                    content_type = file_meta["content_type"]
                    tenant = "public"

                    # Generate presigned URL for "put_object"
                    file_name = unique_file_name_by_original(original_file_name)

                    if classify and module:
                        new_obj_key = f"{add_slash(classify)}{add_slash(tenant)}{add_slash(module)}{file_name}"
                    else:
                        new_obj_key = f"{add_slash(StorageClassify.TEMPS)}{add_slash(tenant)}{file_name}"

                    storage = S3Client()
                    presigned_url = storage.generate_upload_presigned_url(
                        file_key=new_obj_key,
                        file_size=file_size,
                        content_type=content_type,
                        expiry=expiry,
                    )

                    # To append file meta
                    presigned_urls.append(
                        {
                            "file_id": uuid.uuid4(),
                            "storage_provider": StorageProvider.S3,
                            "ref_type": ref_type,
                            "ref_id": ref_id,
                            "classify": classify,
                            "module": module,
                            "hr_employee": hr_employee,
                            "original_file_name": original_file_name,
                            "file_name": file_name,
                            "file_key": f"{new_obj_key}",  # as File url
                            "file_size": file_size,
                            "content_type": content_type,
                            "presigned_url": presigned_url,
                        }
                    )

                # Save File meta
                SaveFileMetaService.create_files_meta_ref_id(
                    ref_id=ref_id,
                    ref_type=ref_type,
                    file_metadata_list=presigned_urls,
                )

                return Response({"files": presigned_urls}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"Failed to create the file: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class GenerateDownloadPresignedUrlView(views.APIView):
    serializer_class = DownloadPreSignedSerializer

    # To be generate presigned URL for download s3 direct
    def post(self, request, *args, **kwargs):
        
        # Validate input using the serializer
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        if not serializer.is_valid():
            return Response({"message": serializer.errors}, status=400)
        
        file_key = serializer.validated_data.get("file_key", None)
        bucket_name = serializer.validated_data.get("bucket_name", settings.S3_STORAGE_BUCKET_NAME)
        expiry = serializer.validated_data.get("expiry", settings.S3_PRESIGNED_EXPIRE)

        storage = S3Client()
        download_presigned_url = storage.generate_download_presigned_url(
            file_key=file_key, bucket_name=bucket_name, expiry=expiry
        )

        presigned_url = {
            "file_key": file_key,
            "bucket_name": bucket_name,
            "presigned_url": download_presigned_url,
        }

        return Response(presigned_url, status=status.HTTP_200_OK)


class GenerateDeletePresignedUrlView(views.APIView):
    serializer_class = DeletePreSignedSerializer

    # To be generate presigned URL for delete s3 direct
    def post(self, request):
        # Validate input using the serializer
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not serializer.is_valid():
            return Response({"message": serializer.errors}, status=400)
        
        file_key = serializer.validated_data.get("file_key", None)
        bucket_name = serializer.validated_data.get("bucket_name", None)

        if not file_key and bucket_name:
            return Response(
                {"error": "No file key provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        storage = S3Client()
        download_presigned_url = storage.generate_delete_presigned_url(
            file_key=file_key
        )

        presigned_url = {
            "file_key": file_key,
            "bucket_name": bucket_name,
            "presigned_url": download_presigned_url,
        }

        return Response(presigned_url, status=status.HTTP_200_OK)
