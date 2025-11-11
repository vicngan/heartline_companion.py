"""
Security helpers: password hashing + reversible encryption for sensitive text.
"""

from __future__ import annotations

import base64
import os
from typing import Tuple

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def _pbkdf2(password: str, salt: bytes, length: int = 32, iterations: int = 390_000) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=length,
        salt=salt,
        iterations=iterations,
    )
    return kdf.derive(password.encode("utf-8"))


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
