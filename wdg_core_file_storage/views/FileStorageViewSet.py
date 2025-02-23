from datetime import datetime
from django.conf import settings
from django.http import FileResponse
from rest_framework import views, viewsets, status
from rest_framework.response import Response
from django.db import transaction

from wdg_core_file_storage.backends.s3 import S3Client
from wdg_core_file_storage.backends.storages import S3MediaStorage
from wdg_core_file_storage.constants import StorageClassify, StorageModule
from wdg_core_file_storage.serializers.file_storage_serializer import (
    FileStorageCreateValidateSerializer,
    FileStorageDeleteValidateSerializer,
    FileStorageSerializer,
    FileStorageValidateByRefSerializer,
    FileStoragePreviewValidateSerializer,
)
from wdg_core_file_storage.utils.file_util import split_first_path
from wdg_core_file_storage.wdg_file_metadata.models import FileStorageModel


class FileStorageViewSet(viewsets.ModelViewSet):
    model = FileStorageModel
    queryset = FileStorageModel.objects.all()
    serializer_class = FileStorageSerializer


class FileStorageByRefView(views.APIView):
    serializer_class = FileStorageValidateByRefSerializer

    def get(self, request):
        try:
            # Validate input using query parameters
            serializer = self.serializer_class(data=request.query_params)
            serializer.is_valid(raise_exception=True)

            if not serializer.is_valid():
                return Response({"message": serializer.errors}, status=400)
        
            ref_type = serializer.validated_data.get("ref_type", None)
            ref_id = serializer.validated_data.get("ref_id", None)

            # Filter data based on query parameters
            data = FileStorageModel.objects.filter(
                ref_type=ref_type,
                ref_id=ref_id,
                deleted=False,
            ).all()

            serializer_file = FileStorageSerializer(data, many=True)
            return Response(serializer_file.data, status=status.HTTP_200_OK)

        except FileStorageModel.DoesNotExist:
            return Response([], status=status.HTTP_200_OK)


class FileStoragePreviewView(views.APIView):
    serializer_class = FileStoragePreviewValidateSerializer

    def get(self, request, *args, **kwargs):

        # Validate input using the serializer
        serializer = self.serializer_class(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        if not serializer.is_valid():
            return Response({"message": serializer.errors}, status=400)
        
        try:
            file_instance = FileStorageModel.objects.get(
                id=serializer.validated_data.get("id"),
                file_name=serializer.validated_data.get("file_name"),
                file_id=serializer.validated_data.get("file_id"),
            )

            if not file_instance:
                raise Response(
                    {"error": "File not found."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            storage = S3MediaStorage()
            # Open the file from S3 storage(Base storage config in settings)
            file_obj = storage.open(file_instance.file_path.name, "rb")

            # Return the file as a response
            return FileResponse(
                file_obj,
                as_attachment=True,
                filename=file_instance.file_name.split("/")[-1],
            )

        except Exception as e:
            return Response(
                {"error": f"Failed to retrieve the file: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class FileStorageDeleteView(views.APIView):
    serializer_class = FileStorageDeleteValidateSerializer

    def delete(self, request):
        
        # Validate input using the serializer
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not serializer.is_valid():
            return Response({"message": serializer.errors}, status=400)

        try:
            uuid = serializer.validated_data.get("id", None)
            file_path = serializer.validated_data.get("file_path", None)

            # Fetch the file object from the database
            file_object = FileStorageModel.objects.get(id=uuid, file=file_path)

            storage = S3Client()
            # Delete the file from the S3 bucket
            is_deleted = storage.delete_file_from_bucket(
                file_name=file_object.file.name
            )

            if is_deleted:
                # Delete the file record from the database
                file_object.delete()

                return Response(
                    {"message": "File deleted successfully"}, status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"message": "Failed to delete the file"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        except Exception as e:
            return Response(
                {"message": f"Failed to delete file: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class FileStorageBulkCreateView(views.APIView):
    serializer_class = FileStorageCreateValidateSerializer

    def post(self, request, *args, **kwargs):
        """Handle saving file info after successful upload."""

        # Validate input using the serializer
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Initialize an array to collect file information
        created_files = []
        object_keys = []

        file_info = request.data.get("file_info", [])
        ref_type = request.data.get("ref_type")
        ref_id = request.data.get("ref_id")
        module = request.data.get("module", StorageModule.GENERIC)
        
        # move to uploaded folder
        is_move = request.data.get("is_move", False)

        try:
            with transaction.atomic():

                for file in file_info:
                    original_file_name = file.get("original_file_name", None)
                    file_name = file.get("file_name", None)
                    file_size = file.get("file_size", 0)
                    content_type = file.get("content_type")
                    file_url = file.get("file_path")
                    description = file.get("description")

                    # Re-path object key path
                    remaining_path = split_first_path(file_url)

                    new_file_url = f"{StorageClassify.UPLOADED}/{remaining_path}" if is_move else file_url

                    object_keys.append(file_name)

                    # Create a record in FileStorageModel
                    file_record = FileStorageModel.objects.create(
                        original_file_name=original_file_name,
                        file_name=file_name,
                        file_size=file_size,
                        file_type=content_type,
                        ref_type=ref_type,
                        ref_id=ref_id,
                        file_path=new_file_url,
                        image_url=new_file_url,
                        description=description,
                        create_date=datetime.now(),
                        create_uid=self.request.user.id,
                    )

                    # Append the created file record to the list
                    created_files.append(
                        {
                            "id": file_record.id,
                            "original_file_name": file_record.original_file_name,
                            "file_name": file_record.file_name,
                            "file_size": file_record.file_size,
                            "file_type": file_record.file_type,
                            "ref_type": file_record.ref_type,
                            "ref_id": file_record.ref_id,
                            "file_path": file_record.file_path,
                            "image_url": file_record.image_url.url,
                            "description": file_record.description,
                            "create_date": file_record.create_date,
                            "create_uid": file_record.create_uid,
                        }
                    )
                    
                if is_move:
                    # copy object to new folder and delete object from temps
                    bucket_name = settings.S3_STORAGE_BUCKET_NAME
                    source_folder = f"{StorageClassify.TEMPS}/{module}/"
                    destination_folder = f"{StorageClassify.UPLOADED}/{module}/"

                    keys_to_copy = object_keys

                    storage = S3Client()
                    storage.copy_objects_and_delete_by_key(
                        bucket_name, source_folder, destination_folder, keys_to_copy
                    )

                return Response(
                    {
                        "message": "File information saved successfully.",
                        "files": created_files,
                    },
                    status=status.HTTP_200_OK,
                )

        except Exception as e:
            return Response(
                {"error": f"Failed to create the file: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )