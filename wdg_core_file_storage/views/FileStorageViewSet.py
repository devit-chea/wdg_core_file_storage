from django.http import FileResponse
from rest_framework import views, viewsets, status
from rest_framework.response import Response

from wdg_core_file_storage.backends.s3 import S3Client
from wdg_core_file_storage.backends.storages import S3MediaStorage
from wdg_core_file_storage.serializers.file_storage_serializer import (
    FileStorageDeleteValidateSerializer,
    FileStorageSerializer,
    FileStorageValidateByRefSerializer,
)
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
    serializer_class = FileStorageDeleteValidateSerializer

    def get(self, request, *args, **kwargs):

        # Validate input using the serializer
        serializer = self.serializer_class(data=request.data)
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
