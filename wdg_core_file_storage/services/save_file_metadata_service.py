from datetime import datetime

from wdg_core_file_storage.wdg_file_metadata.models import FileStorageModel


class SaveFileMetaService:
    @classmethod
    def create_files_meta_ref_id(
        cls,
        ref_type: str = None,
        ref_id: str = None,
        user_id: any = None,
        file_metadata_list: list = [],
        extra_fields: dict = None,  # New argument for extra fields
    ):
        """
        Bulk creates FileStorageModel instances from a list of file metadata.

        Args:
            ref_type (str),
            ref_id (str),
            user_id (any),
            file_metadata_list (list): List of dictionaries containing file metadata.
                Example: [{"file_name": "file1.txt", "file_path": "/path/file1.txt", "file_size": 1024}, ...],
            extra_fields={"custom_tag": "important"}

        Returns:
            list: file_metadata_list
        """
        if not file_metadata_list:
            raise ValueError("File metadata list cannot be empty.")

        extra_fields = extra_fields or {}  # Ensure it's a dictionary
        
        # Prepare model instances
        file_instances = [
            FileStorageModel(
                ref_id=ref_id,
                ref_type=ref_type,
                file_id=file.get("file_id", None),
                original_file_name=file.get("original_file_name", None),
                file_name=file.get("file_name", None),
                file_path=file.get("file_path", None),
                file_size=file.get("file_size", None),
                file_type=file.get("file_type", None),
                description=file.get("description", None),
                create_date=datetime.now(),
                create_uid=user_id,
                **extra_fields,  # Unpacking extra fields
            )
            # Mapping through file meta data list
            for file in file_metadata_list
        ]

        # Perform bulk create
        created_files = FileStorageModel.objects.bulk_create(file_instances)

        # Convert to JSON-like structure
        created_files_json = [
            {
                "id": file_record.id,
                "original_file_name": file_record.original_file_name,
                "file_name": file_record.file_name,
                "file_size": file_record.file_size,
                "file_type": file_record.file_type,
                "ref_type": file_record.ref_type,
                "ref_id": file_record.ref_id,
                "description": file_record.description,
                "create_date": file_record.create_date,
                "create_uid": file_record.create_uid,
            }
            for file_record in created_files
        ]

        return created_files_json
