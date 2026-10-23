"""
secure_storage.py — encrypted JSON persistence helpers for Sub Ladder.

This module provides authenticated encryption for sensitive local files.
"""

from __future__ import annotations

import base64
import copy
import getpass
import hashlib
import json
import os
import platform
import tempfile
import uuid

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

ENVELOPE_MARKER = "__sl_encrypted__"
ENVELOPE_VERSION = 1
KDF_ITERATIONS = 390_000

# App pepper used in key derivation.
# This is not sufficient alone for secrecy, but is combined with a device
# fingerprint for device-bound data.
APP_PEPPER = b"SubLadder::v2::secure-local-storage::f8f6cf2a92d1"

SCOPE_DEVICE = "device"
SCOPE_PORTABLE = "portable"


class SecureStorageError(Exception):
    """Raised when encrypted file content cannot be decrypted or parsed."""


def _device_fingerprint() -> str:
    """Build a stable-ish local fingerprint for device-bound encryption keys."""
    parts = [
        platform.system(),
        platform.release(),
        platform.machine(),
        platform.node(),
        os.environ.get("PROCESSOR_IDENTIFIER", ""),
        getpass.getuser(),
        str(uuid.getnode()),
    ]
    raw = "|".join(parts).encode("utf-8", errors="ignore")
    return hashlib.sha256(raw).hexdigest()


def _derive_fernet_key(salt: bytes, scope: str) -> bytes:
    scope_material = APP_PEPPER
    if scope == SCOPE_DEVICE:
        scope_material += _device_fingerprint().encode("utf-8")
    elif scope != SCOPE_PORTABLE:
        raise SecureStorageError(f"Unknown encryption scope: {scope}")

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=KDF_ITERATIONS,
    )
    key = kdf.derive(scope_material)
    return base64.urlsafe_b64encode(key)


def _dump_json_atomic(path: str, payload: dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(prefix=".sltmp_", suffix=".json", dir=os.path.dirname(path))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, path)
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


def _encrypt_payload(data: dict, scope: str) -> dict:
    salt = os.urandom(16)
    key = _derive_fernet_key(salt=salt, scope=scope)
    token = Fernet(key).encrypt(
        json.dumps(data, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    )
    return {
        ENVELOPE_MARKER: True,
        "version": ENVELOPE_VERSION,
        "scope": scope,
        "salt": base64.urlsafe_b64encode(salt).decode("ascii"),
        "token": token.decode("ascii"),
    }


def _decrypt_payload(envelope: dict) -> dict:
    try:
        salt = base64.urlsafe_b64decode(envelope["salt"].encode("ascii"))
        token = envelope["token"].encode("ascii")
        scope = envelope.get("scope", SCOPE_DEVICE)
    except Exception as exc:
        raise SecureStorageError("Malformed encrypted payload") from exc

    key = _derive_fernet_key(salt=salt, scope=scope)
    try:
        plaintext = Fernet(key).decrypt(token)
    except InvalidToken as exc:
        raise SecureStorageError("Encrypted data could not be decrypted") from exc

    try:
        parsed = json.loads(plaintext.decode("utf-8"))
    except Exception as exc:
        raise SecureStorageError("Decrypted payload is not valid JSON") from exc

    if not isinstance(parsed, dict):
        raise SecureStorageError("Decrypted payload must be a JSON object")
    return parsed


def is_encrypted_payload(value: object) -> bool:
    return isinstance(value, dict) and value.get(ENVELOPE_MARKER) is True


def read_secure_json(
    path: str,
    *,
    default: dict | None = None,
    migrate_plain_to_encrypted: bool = False,
    scope: str = SCOPE_DEVICE,
) -> dict:
    """
    Read a JSON file and decrypt it when it uses the encrypted envelope format.

    If migrate_plain_to_encrypted is True, plain JSON payloads are immediately
    rewritten to encrypted format after a successful read.
    """
    if not os.path.exists(path):
        return copy.deepcopy(default) if default is not None else {}

    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    if is_encrypted_payload(raw):
        return _decrypt_payload(raw)

    if not isinstance(raw, dict):
        raise SecureStorageError("JSON payload must be an object")

    if migrate_plain_to_encrypted:
        write_secure_json(path, raw, scope=scope)
    return raw


def write_secure_json(path: str, data: dict, *, scope: str = SCOPE_DEVICE):
    if not isinstance(data, dict):
        raise SecureStorageError("Can only encrypt dictionary payloads")
    envelope = _encrypt_payload(data, scope=scope)
    _dump_json_atomic(path, envelope)


def write_plain_json(path: str, data: dict):
    if not isinstance(data, dict):
        raise SecureStorageError("Plain JSON payload must be an object")
    _dump_json_atomic(path, data)
