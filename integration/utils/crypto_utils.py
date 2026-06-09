import os
import base64
import hashlib
from django.db import models
from Crypto.Cipher import AES

# Ensure your local environment secret key is exactly 32 bytes
ENCRYPTION_KEY = os.environ.get(
    "INTEGRATION_CRYPTO_KEY", "secret_key_must_be_32_bytes_long"
).encode("utf-8")
IV_LENGTH = 12


def encrypt_aes_256_gcm(text: str) -> str:
    if not text:
        return ""
    iv = os.urandom(IV_LENGTH)
    cipher = AES.new(ENCRYPTION_KEY, AES.MODE_GCM, nonce=iv)
    ciphertext, auth_tag = cipher.encrypt_and_digest(text.encode("utf-8"))
    return f"{iv.hex()}:{auth_tag.hex()}:{ciphertext.hex()}"


def decrypt_aes_256_gcm(encrypted_payload: str) -> str:
    if not encrypted_payload:
        return ""
    try:
        iv_hex, auth_tag_hex, ciphertext_hex = encrypted_payload.split(":")
        cipher = AES.new(ENCRYPTION_KEY, AES.MODE_GCM, nonce=bytes.fromhex(iv_hex))
        return cipher.decrypt_and_verify(
            bytes.fromhex(ciphertext_hex), bytes.fromhex(auth_tag_hex)
        ).decode("utf-8")
    except Exception as e:
        raise ValueError("Decryption failed. Data corrupted or bad secret key.") from e


def hash_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def base64url_encode_sha256(text: str) -> str:
    hasher = hashlib.sha256(text.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(hasher).decode("utf-8").replace("=", "")


class EncryptedTextField(models.TextField):
    """Custom model field for transparent AES-256-GCM storage layer encryption."""

    def get_prep_value(self, value):
        if value is not None:
            return encrypt_aes_256_gcm(str(value))
        return value

    def from_db_value(self, value, expression, connection):
        if value is not None:
            return decrypt_aes_256_gcm(value)
        return value
