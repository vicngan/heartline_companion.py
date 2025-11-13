"""
Security helpers: password hashing + reversible encryption for sensitive text.
"""

from __future__ import annotations

import base64
import hashlib
import logging
import os
from typing import Tuple

try:
    from cryptography.fernet import Fernet, InvalidToken
except ModuleNotFoundError:  # pragma: no cover - fallback is only hit when dependency missing
    logging.getLogger(__name__).warning(
        "Package 'cryptography' not available. Falling back to a lightweight XOR cipher; "
        "install cryptography for production-grade encryption."
    )

    class InvalidToken(Exception):
        """Raised when ciphertext cannot be decoded with the fallback cipher."""

    class _FallbackFernet:
        """Poor-man's Fernet replacement so the app keeps working without cryptography."""

        def __init__(self, key: bytes):
            if not key:
                raise ValueError("Encryption key is required")
            # Normalize the user key material to 32 bytes deterministically.
            self._key_stream = hashlib.sha256(key).digest()

        def _xor(self, data: bytes) -> bytes:
            stream = self._key_stream
            return bytes(b ^ stream[i % len(stream)] for i, b in enumerate(data))

        def encrypt(self, data: bytes) -> bytes:
            if not data:
                return b""
            return base64.urlsafe_b64encode(self._xor(data))

        def decrypt(self, token: bytes) -> bytes:
            if not token:
                return b""
            try:
                payload = base64.urlsafe_b64decode(token)
            except Exception as exc:  # pylint: disable=broad-except
                raise InvalidToken("Unable to decode ciphertext") from exc
            return self._xor(payload)

    Fernet = _FallbackFernet  # type: ignore[assignment]


def _pbkdf2(password: str, salt: bytes, length: int = 32, iterations: int = 390_000) -> bytes:
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
        dklen=length,
    )


def create_password_record(password: str) -> Tuple[str, str]:
    salt = os.urandom(16)
    hash_bytes = _pbkdf2(password, salt)
    return base64.b64encode(hash_bytes).decode("utf-8"), base64.b64encode(salt).decode("utf-8")


def verify_password(password: str, stored_hash_b64: str, salt_b64: str) -> bool:
    salt = base64.b64decode(salt_b64.encode("utf-8"))
    expected_hash = base64.b64decode(stored_hash_b64.encode("utf-8"))
    candidate_hash = _pbkdf2(password, salt)
    return secrets_compare_digest(expected_hash, candidate_hash)


def secrets_compare_digest(a: bytes, b: bytes) -> bool:
    if len(a) != len(b):
        return False
    result = 0
    for x, y in zip(a, b):
        result |= x ^ y
    return result == 0


def derive_encryption_key(password: str, salt_b64: str) -> bytes:
    salt = base64.b64decode(salt_b64.encode("utf-8"))
    key_material = _pbkdf2(password, salt)
    return base64.urlsafe_b64encode(key_material)


def encrypt_text(plaintext: str, key: bytes) -> str:
    if not plaintext:
        return ""
    fernet = Fernet(key)
    return fernet.encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_text(ciphertext: str, key: bytes) -> str:
    if not ciphertext:
        return ""
    fernet = Fernet(key)
    try:
        return fernet.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        return "[unable to decrypt]"
