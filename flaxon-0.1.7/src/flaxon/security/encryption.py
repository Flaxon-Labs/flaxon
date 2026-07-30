from __future__ import annotations

import base64
import hashlib
import hmac
import os

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class Encryptor:
    def __init__(self, secret_key: str) -> None:
        self.secret_key = secret_key.encode()

    def _derive_key(self, salt: bytes) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return kdf.derive(self.secret_key)

    def encrypt(self, data: bytes) -> str:
        salt = os.urandom(16)
        key = self._derive_key(salt)
        iv = os.urandom(16)

        cipher = Cipher(algorithms.AES(key), modes.GCM(iv))
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(data) + encryptor.finalize()

        result = salt + iv + encryptor.tag + ciphertext
        return base64.urlsafe_b64encode(result).decode()

    def decrypt(self, encrypted: str) -> bytes:
        data = base64.urlsafe_b64decode(encrypted)

        salt = data[:16]
        iv = data[16:32]
        tag = data[32:48]
        ciphertext = data[48:]

        key = self._derive_key(salt)
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag))
        decryptor = cipher.decryptor()
        return decryptor.update(ciphertext) + decryptor.finalize()


class Hasher:
    @staticmethod
    def hash(data: str, salt: str | None = None) -> str:
        if salt is None:
            salt = os.urandom(16).hex()
        combined = salt + data
        hash_value = hashlib.sha256(combined.encode()).hexdigest()
        return f"{salt}${hash_value}"

    @staticmethod
    def verify(data: str, hashed: str) -> bool:
        try:
            salt, hash_value = hashed.split("$")
            combined = salt + data
            new_hash = hashlib.sha256(combined.encode()).hexdigest()
            return hmac.compare_digest(new_hash, hash_value)
        except ValueError:
            return False

    @staticmethod
    def hmac_sign(data: str, secret: str) -> str:
        return hmac.new(secret.encode(), data.encode(), hashlib.sha256).hexdigest()

    @staticmethod
    def hmac_verify(data: str, signature: str, secret: str) -> bool:
        expected = Hasher.hmac_sign(data, secret)
        return hmac.compare_digest(expected, signature)
