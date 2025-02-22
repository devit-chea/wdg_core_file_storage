import logging
import threading

import boto3
from botocore.config import Config
from botocore.exceptions import (
    ClientError,
    EndpointConnectionError,
    NoCredentialsError,
    PartialCredentialsError,
)
from django.conf import settings

from wdg_core_file_storage.helpers.s3_helpers import get_bucket_name

logger = logging.getLogger(__name__)


class S3Client:
    """
    A reusable and extendable client for interacting with S3-compatible storage.

    Features include lazy initialization, enhanced error handling, presigned URL generation,
    and upload operations. Designed to be scalable and testable.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        """
        Singleton pattern to ensure only one instance of S3Client exists.
        """
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self, session=None):
        """
        Initialize the S3Client.

        :param session: A custom boto3.Session instance for multi-account or multi-region use.
        """
        self.client = None
        self.session = session or boto3.Session()
        self.s3_client_init = "S3 client is not initialized."

    def _validate_settings(self):
        """
        Validate that all required settings are configured.
        """
        required_settings = [
            "S3_ENDPOINT_URL",
            "S3_ACCESS_KEY_ID",
            "S3_SECRET_ACCESS_KEY",
        ]
        for setting in required_settings:
            if not hasattr(settings, setting):
                logger.error(f"Missing required S3 setting: {setting}")
                raise ValueError(f"Missing required S3 setting: {setting}")

    def _get_client(self):
        """
        Lazily initialize and return the boto3 S3 client.
        """
        if self.client is None:
            self._validate_settings()
            try:
                config = Config(retries={"max_attempts": 10, "mode": "standard"})
                self.client = self.session.client(
                    service_name="s3",
                    endpoint_url=f"https://{settings.S3_ENDPOINT_URL}",
                    aws_access_key_id=settings.S3_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
                    config=config,
                )
            except (NoCredentialsError, PartialCredentialsError) as e:
                logger.error(f"Credentials error: {e}")
                raise
            except EndpointConnectionError as e:
                logger.error(f"Endpoint connection error: {e}")
                raise
            except Exception as e:
                logger.error(f"Failed to initialize S3 client: {e}")
                raise
        return self.client

    def list_files(self, bucket_name: str, prefix: str = "") -> list:
        """
        List files in the specified S3 bucket.

        :param bucket_name: Name of the S3 bucket.
        :param prefix: Prefix to filter files.
        :return: List of file keys or an empty list on failure.
        """
        
        client = self._get_client()
        try:
            response = client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
            return [obj["Key"] for obj in response.get("Contents", [])]
        except ClientError as e:
            logger.error(f"Failed to list files in bucket {bucket_name}: {e}")
            return []

    def upload_file(self, bucket_name: str, file_name: str, file_data) -> bool:
        """
        Upload a file to the specified S3 bucket.

        :param bucket_name: Name of the S3 bucket.
        :param file_name: Name of the file (key) to upload.
        :param file_data: File data to upload.
        :return: True if successful, False otherwise.
        """
        client = self._get_client()
        try:
            client.put_object(Bucket=bucket_name, Key=file_name, Body=file_data)
            logger.info(f"File {file_name} uploaded successfully to {bucket_name}.")
            return True
        except ClientError as e:
            logger.error(f"Failed to upload file {file_name}: {e}")
            return False

    def generate_upload_presigned_url(
        self,
        file_key: str,
        file_size,
        bucket_name=None,
        content_type=None,
        expiry: int = 3600,
    ):
        """
        Generate a presigned URL for getting or uploading a file from S3.
        :param object_name: The key name for the file in the bucket.
        :return: Presigned upload URL as a string.
        """

        client = self._get_client()
        try:
            bucket_name = bucket_name or get_bucket_name()

            url = client.generate_presigned_url(
                ClientMethod="put_object",
                Params={
                    "Bucket": bucket_name,
                    "Key": file_key,
                    "ContentLength": file_size,
                    "ContentType": content_type,
                },
                ExpiresIn=expiry,
            )

            return url
        except TypeError as e:
            logger.error(f"Error generating presigned upload URL: {e}")
            raise ValueError("Type error.")
        except ClientError as e:
            logger.error(f"Error generating presigned upload URL: {e}")
            raise ValueError("AWS credentials not configured properly.")

    def generate_download_presigned_url(
        self, file_key: str, bucket_name=None, expiry: int = 3600
    ):
        """
        Generate a presigned URL to download a file from S3.
        :param file_key: Name of the file in the S3 bucket.
        :param expiry: Expiry time in seconds (default: 3600 seconds = 1 hour).
        :return: Presigned download URL as a string.
        """

        client = self._get_client()
        try:
            bucket_name = bucket_name or get_bucket_name()

            url = client.generate_presigned_url(
                ClientMethod="get_object",
                Params={
                    "Bucket": bucket_name or settings.S3_STORAGE_BUCKET_NAME,
                    "Key": file_key,
                },
                ExpiresIn=expiry,
            )
        except ClientError as e:
            logger.error(f"Error generating presigned download URL: {e}")
            raise ValueError(f"Error generating presigned URL: {e}")
        return url

    def generate_delete_presigned_url(
        self, file_key: str, bucket_name=None, expiry: int = 3600
    ):
        """
        Generate a presigned URL to delete a file from S3.
        :param file_key: Name of the file in the S3 bucket.
        :param expiry: Expiry time in seconds (default: 3600 seconds = 1 hour).
        :return: Presigned Delete Object URL as a string.
        """

        client = self._get_client()
        try:
            bucket_name = bucket_name or get_bucket_name()
            url = client.generate_presigned_url(
                ClientMethod="delete_object",
                Params={
                    "Bucket": bucket_name or settings.S3_STORAGE_BUCKET_NAME,
                    "Key": file_key,
                },
                ExpiresIn=expiry,
            )
        except ClientError as e:
            logger.error(f"Error generating presigned URL for delete: {e}")
            raise ValueError(f"Error generating presigned URL: {e}")
        return url

    def delete_file_from_bucket(self, file_name: str, bucket_name=None) -> bool:
        """
        Delete file from S3 bucket.
        :param bucket_name: Name of the bucket
        :param file_name: Name of the file
        :return: True if file was deleted, False if not
        """

        client = self._get_client()
        try:
            bucket_name = bucket_name or get_bucket_name()
            client.delete_object(Bucket=bucket_name, Key=file_name)
            return True
        except ClientError as e:
            logger.error(f"Error deleting file from bucket: {e}")
            return False
        except EndpointConnectionError as e:
            logger.error(f"Endpoint connection error: {e}")
            return False

    def check_file_exists_in_bucket(self, bucket_name, file_name) -> bool:
        """
        Check if a file exists in an S3 bucket.
        :param bucket_name: Name of the bucket
        :param file_name: Name of the file
        :return: True if the file exists, False otherwise
        """

        client = self._get_client()
        try:
            client.head_object(Bucket=bucket_name, Key=file_name)
            return True
        except ClientError as e:
            # Check for a "Not Found" error code
            if e.response["Error"]["Code"] == "404":
                logger.error(f"Error no bucket: {e}")
                return False
            raise

    def save_file_in_bucket(self, bucket_name, file_name, file_obj):
        """
        Save a file in an S3 bucket.
        :param bucket_name: The name of the bucket
        :param file_name: The name of the file
        :param file_obj: The file object to save
        :raises: Exception if the file already exists
        """

        client = self._get_client()
        try:
            client.upload_fileobj(file_obj, bucket_name, file_name)
        except ClientError as e:
            logger.error(f"Error generating presigned URL for delete: {e}")
            raise ValueError(f"Failed to upload file: {e}")

    def copy_s3_folder(self, bucket_name, source_folder, destination_folder):
        client = self._get_client()
        paginator = client.get_paginator("list_objects_v2")
        try:
            for page in paginator.paginate(Bucket=bucket_name, Prefix=source_folder):
                if "Contents" in page:
                    for obj in page["Contents"]:
                        source_key = obj["Key"]
                        # Skip copying the "folder" itself if S3 treats it as an object
                        if source_key == source_folder:
                            continue

                        destination_key = source_key.replace(
                            source_folder, destination_folder, 1
                        )
                        copy_source = {"Bucket": bucket_name, "Key": source_key}

                        # Perform the copy
                        client.copy_object(
                            Bucket=bucket_name,
                            CopySource=copy_source,
                            Key=destination_key,
                        )

                        # To delete the source file after copying
                        client.delete_object(Bucket=bucket_name, Key=source_key)

        except ClientError as e:
            logger.error(f"Error generating presigned URL for delete: {e}")
            raise ValueError(f"Failed to upload file: {e}")

    def copy_objects_and_delete_by_key(
        self,
        bucket_name: str,
        source_folder: str,
        destination_folder: str,
        keys_to_copy: list,
    ):

        client = self._get_client()
        try:
            bucket_name = bucket_name or get_bucket_name()

            for key in keys_to_copy:
                # Construct the source and destination keys
                source_key = f"{source_folder}{key}"
                destination_key = f"{destination_folder}{key}"

                copy_source = {"Bucket": bucket_name, "Key": source_key}

                # Perform the copy operation
                client.copy_object(
                    Bucket=bucket_name, CopySource=copy_source, Key=destination_key
                )

                # Perform the delete operation
                client.delete_object(Bucket=bucket_name, Key=source_key)

        except ClientError as e:
            logger.error(f"Error generating presigned URL for delete: {e}")
            raise ValueError(f"Failed to upload file: {e}")
