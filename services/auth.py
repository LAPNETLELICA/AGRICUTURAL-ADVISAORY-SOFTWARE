"""Small dependency-free authentication service for V1.

The implementation deliberately avoids provider lock-in. It uses PBKDF2 password
hashing and HMAC signed bearer tokens. The same API can later be replaced by an
OIDC/OAuth2 provider without touching the advisory engine.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from typing import Any


class AuthError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class Principal:
    subject: str
    role: str

    @property
    def is_admin(self) -> bool:
        return self.role in {"admin", "knowledge_admin", "service"}


class AuthService:
    def __init__(self, secret: str, store_path: Path, token_ttl_seconds: int = 3600) -> None:
        if len(secret) < 16:
            raise ValueError("AUTH_SECRET must contain at least 16 characters")
        self._secret = secret.encode("utf-8")
        self._store_path = store_path
        self._token_ttl = token_ttl_seconds
        self._lock = RLock()
        self._users: dict[str, dict[str, str]] = {}
        self._load()

    @staticmethod
    def _b64(value: bytes) -> str:
        return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")

    @staticmethod
    def _unb64(value: str) -> bytes:
        return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))

    @staticmethod
    def _hash_password(password: str, salt: bytes | None = None) -> str:
        if len(password) < 10:
            raise AuthError("password must contain at least 10 characters")
        salt = salt or secrets.token_bytes(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 210_000)
        return f"pbkdf2_sha256$210000${AuthService._b64(salt)}${AuthService._b64(digest)}"

    @staticmethod
    def _verify_password(password: str, encoded: str) -> bool:
        try:
            algorithm, rounds, salt, digest = encoded.split("$", 3)
            if algorithm != "pbkdf2_sha256":
                return False
            computed = hashlib.pbkdf2_hmac(
                "sha256", password.encode(), AuthService._unb64(salt), int(rounds)
            )
            return hmac.compare_digest(computed, AuthService._unb64(digest))
        except (ValueError, TypeError):
            return False

    def _load(self) -> None:
        if not self._store_path.exists():
            return
        try:
            data = json.loads(self._store_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        if isinstance(data, dict):
            self._users = {
                key: value
                for key, value in data.items()
                if isinstance(value, dict) and "password_hash" in value and "role" in value
            }

    def _persist(self) -> None:
        self._store_path.parent.mkdir(parents=True, exist_ok=True)
        temp = self._store_path.with_suffix(".tmp")
        temp.write_text(json.dumps(self._users, indent=2), encoding="utf-8")
        temp.replace(self._store_path)

    def ensure_user(self, username: str, password: str, role: str) -> None:
        with self._lock:
            if username in self._users:
                return
            self._users[username] = {
                "password_hash": self._hash_password(password),
                "role": role,
            }
            self._persist()

    def register_farmer(self, username: str, password: str) -> Principal:
        with self._lock:
            if username in self._users:
                raise AuthError("account already exists")
            self._users[username] = {
                "password_hash": self._hash_password(password),
                "role": "farmer",
            }
            self._persist()
        return Principal(username, "farmer")

    def delete_user(self, username: str) -> bool:
        with self._lock:
            if username not in self._users:
                return False
            del self._users[username]
            self._persist()
            return True

    def authenticate(self, username: str, password: str) -> str:
        with self._lock:
            record = self._users.get(username)
        if record is None or not self._verify_password(password, record["password_hash"]):
            raise AuthError("invalid username or password")
        now = int(time.time())
        payload = {
            "sub": username,
            "role": record["role"],
            "iat": now,
            "exp": now + self._token_ttl,
            "nonce": secrets.token_hex(8),
        }
        body = self._b64(json.dumps(payload, separators=(",", ":")).encode())
        signature = self._b64(hmac.new(self._secret, body.encode(), hashlib.sha256).digest())
        return f"{body}.{signature}"

    def verify(self, token: str) -> Principal:
        try:
            body, signature = token.split(".", 1)
            expected = self._b64(hmac.new(self._secret, body.encode(), hashlib.sha256).digest())
            if not hmac.compare_digest(signature, expected):
                raise AuthError("invalid token signature")
            payload: dict[str, Any] = json.loads(self._unb64(body))
            if int(payload["exp"]) < int(time.time()):
                raise AuthError("token expired")
            subject = str(payload["sub"])
            role = str(payload["role"])
            with self._lock:
                current = self._users.get(subject)
            if current is None or current.get("role") != role:
                raise AuthError("account is no longer active")
        except (ValueError, KeyError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise AuthError("invalid token") from exc
        return Principal(subject, role)
