from datetime import datetime
from django.apps import apps
from django.db import transaction
from typing import List, Dict, Optional


class FileManager:
    @classmethod
    def save_files_meta_data(
        cls,
        app_name: str,
        model_name: str,
        files_meta: List[Dict],
        ref_type: Optional[str] = None,
        ref_id: Optional[int] = None,
    ) -> None:
        """
        Creates or updates file metadata in the specified model.
        
        :param app_name: The name of the app where the model is located.
        :param model_name: The name of the model where the data will be saved (case-insensitive).
        :param files_meta: A list of dictionaries, each containing metadata about a file.
        :param ref_type: Optional reference type to associate with the files.
        :param ref_id: Optional reference ID to associate with the files.
        :raises ValueError: If the model name is invalid or the file metadata is not valid.
        """
        # Get the model class dynamically
        model = apps.get_model(app_name, model_name)
        if not model:
            raise ValueError(f"Model '{model_name}' in app '{app_name}' does not exist.")

        # Validate file metadata and model fields
        model_fields = {field.name for field in model._meta.get_fields()}
        
        for file_meta in files_meta:
            if not isinstance(file_meta, dict):
                raise ValueError("Each file metadata must be a dictionary.")
            if not set(file_meta.keys()).issubset(model_fields):                
                raise ValueError(
                    f"Invalid fields in file metadata: {file_meta.keys() - model_fields}"
                )

        # Add ref_type and ref_id to metadata if provided
        if ref_type:
            for file_meta in files_meta:
                file_meta["ref_type"] = ref_type
        if ref_id:
            for file_meta in files_meta:
                file_meta["ref_id"] = ref_id

        # Separate records for update and create
        update_records = []
        new_records = []
        existing_records = {
            record.id: record
            for record in model.objects.filter(
                id__in=[
                    file["id"] for file in files_meta if "id" in file
                ]
            )
        }

        for file_meta in files_meta:
            _id = file_meta.get("id")
            if _id and _id in existing_records:
                # Update existing record
                for key, value in file_meta.items():
                    setattr(existing_records[_id], key, value)
                update_records.append(existing_records[_id])
            else:
                # Prepare new record
                new_records.append(model(**file_meta))

        # Save changes to the database
        with transaction.atomic():
            if update_records:
                model.objects.bulk_update(
                    update_records, fields=list(files_meta[0].keys())
                )
            if new_records:
                model.objects.bulk_create(new_records)
