# wdg-file-storage

`wdg-file-storage` is a Python package that simplifies interactions with S3-compatible storage systems. It provides a reusable and extendable client for operations such as file upload, download, and presigned URL generation. Designed with scalability and testability in mind, this package is ideal for multi-account and multi-region setups.

---

## Features

- **Upload and Download Files**: Seamlessly manage file transfers to and from S3 buckets.
- **Generate Presigned URLs**: Create time-limited URLs for secure file access.
- **Lazy Initialization**: Efficient resource management by initializing the S3 client only when needed.
- **Custom Session Management**: Support for multi-account and multi-region setups with custom `boto3.Session` instances.
- **Thread-Safe Singleton Design**: Ensures a single instance for consistent client usage.

---

## Utils and Helper Function

- **save_files_meta_data** Save files meta data with dynamic model

## Requirements

- Python 3.8+
- `boto3`
- Django (to access `settings` module)

---

## Installation

Install the package using `pip`:

```bash
pip install wdg-file-storage
```

---

## Configuration

Add the following required settings in your Django project's `settings.py`:

```python
S3_ENDPOINT_URL = "your-s3-endpoint-url"
S3_ACCESS_KEY_ID = "your-access-key-id"
S3_SECRET_ACCESS_KEY = "your-secret-access-key"
```

---

## Usage

### Default Client

#### Upload a File
```python
from wdg_file_storage import S3Client

s3_client = S3Client()
s3_client.upload_file("my_bucket", "example.txt", b"File content here")
```

#### Generate a Presigned URL
```python
url = s3_client.generate_presigned_url(
    bucket_name="my_bucket",
    key="example.txt",
    method="get_object",
    expiry=3600
)
print(f"Presigned URL: {url}")
```

#### Download a File
```python
file_data = s3_client.download_file("my_bucket", "example.txt")
print(file_data.decode())
```

### Custom Session

#### Use a Custom boto3 Session
```python
from boto3.session import Session
from wdg_file_storage import S3Client

custom_session = Session(
    aws_access_key_id="custom_access_key",
    aws_secret_access_key="custom_secret_key",
    region_name="custom_region"
)

s3_client = S3Client(session=custom_session)
s3_client.upload_file("custom_bucket", "example.txt", b"File content here")
```

### List Files in a Bucket
```python
files = s3_client.list_files("my_bucket")
print(files)
```

---

## Development

### Clone the Repository

```bash
git clone https://github.com/yourusername/wdg-file-storage.git
cd wdg-file-storage
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run Tests

To ensure everything is working as expected:

```bash
pytest
```

---

## Publishing to PyPI

1. Update `setup.py` with the correct package information.
2. Build the distribution:

```bash
python setup.py sdist bdist_wheel
```

3. Upload to PyPI using `twine`:

```bash
twine upload dist/*
```

---

## License

This project is licensed under the MIT License. See the `LICENSE` file for more details.

---

## Contributing

Contributions are welcome! Please open an issue or submit a pull request to contribute to this project.

---

## Contact

For issues or inquiries, please contact [your-email@example.com].

