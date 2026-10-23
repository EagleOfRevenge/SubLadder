"""
utils.py — Sub Ladder
Shared utilities: data persistence, language loading, asset validation.
"""

import json
import os
import sys
import copy
import traceback

from secure_storage import (
    SecureStorageError,
    SCOPE_DEVICE,
    SCOPE_PORTABLE,
    read_secure_json,
    write_secure_json,
)

# ── Paths ──────────────────────────────────────────────────────────
# Nuitka (and PyInstaller) set sys.frozen to True when running a
# compiled / frozen executable.  In that case __file__ points inside
# the temporary extraction directory (or the exe location) and we
# must derive all paths from sys.executable / sys._MEIPASS instead.
if getattr(sys, "frozen", False):
    # Frozen / Nuitka build:
    #   sys._MEIPASS  – PyInstaller extraction dir (may not exist with Nuitka)
    #   sys.executable – path to the .exe itself
    _frozen_base = getattr(sys, "_MEIPASS", None) or os.path.dirname(sys.executable)
    # In a Nuitka *onefile* build the exe extracts to a temp dir;
    # data/ lives alongside the exe or under the extraction root.
    ROOT_DIR = _frozen_base
    GAME_DIR = os.path.join(_frozen_base, "game")
    DATA_DIR = os.path.join(_frozen_base, "data")
else:
    # Source Python run:
    GAME_DIR   = os.path.dirname(os.path.abspath(__file__))
    ROOT_DIR   = os.path.dirname(GAME_DIR)
    DATA_DIR   = os.path.join(ROOT_DIR, "data")


def _user_data_root() -> str:
    """Return the writable per-user storage directory for SubLadder."""
    base_dir = os.getenv("APPDATA") or os.getenv("LOCALAPPDATA") or os.path.expanduser("~")
    return os.path.join(base_dir, "SubLadder")


USER_DATA_DIR = _user_data_root()
LEGACY_DATA_FILE = os.path.join(DATA_DIR, "data.json")
LEGACY_ACH_FILE = os.path.join(DATA_DIR, "achievements.json")
LEGACY_AVATAR_DIR = os.path.join(DATA_DIR, "avatars")
UI_LOG_FILE = os.path.join(USER_DATA_DIR, "logs", "ui_errors.log")

LANG_DIR   = os.path.join(DATA_DIR, "languages")
Q_DIR      = os.path.join(DATA_DIR, "questions")
AVATAR_DIR = os.path.join(USER_DATA_DIR, "avatars")
DATA_FILE  = os.path.join(USER_DATA_DIR, "data.json")
ACH_FILE   = os.path.join(USER_DATA_DIR, "achievements.json")
LEGACY_SERVER_HOST = "45.156.84.114"
PRIMARY_SERVER_HOST = "dedicated-zap1280014-1.zap-srv.com"

# ── Default data structure ─────────────────────────────────────────
DEFAULT_DATA = {
    "options": {
        "language":     "English",
        "resolution":   "900 × 720",
        "fullscreen":   False,
        "theme":        "Dark Navy",
        "music_volume": 0.7,
        "sfx_volume":   0.7,
        "friend_list_collapsed": False,
        "friend_list_hover_preview": True,
    },
    "active_profile": None,
    "profiles": {},
    "save": None,
    "social": {
        "friends": [],
        "blocked_players": [],
        "reports": [],
        "friend_requests_in": [],
        "friend_requests_out": [],
        "notifications": [],
    },
    "auth": {
        "tokens": {},       # {profile_name: jwt_token_string}
        "sessions": {},     # {profile_name: {user_id, expires_at, ...}}
    },
    "server": {
        "host": "dedicated-zap1280014-1.zap-srv.com",
        "port": 8000,
        "last_check": None,     # timestamp of last health check
        "is_online": False,     # cached server status
    },
}


def _normalize_data_payload(data: dict) -> dict:
    """Merge defaults into a loaded data payload and normalize legacy values."""
    if not isinstance(data, dict):
        return copy.deepcopy(DEFAULT_DATA)

    for k, v in DEFAULT_DATA.items():
        if k not in data:
            data[k] = copy.deepcopy(v)

    if not isinstance(data.get("social"), dict):
        data["social"] = copy.deepcopy(DEFAULT_DATA["social"])
    else:
        for k, v in DEFAULT_DATA["social"].items():
            if k not in data["social"]:
                data["social"][k] = copy.deepcopy(v)

    for k, v in DEFAULT_DATA["options"].items():
        if k not in data.get("options", {}):
            data.setdefault("options", {})[k] = v

    server_data = data.setdefault("server", {})
    if server_data.get("host") in {None, "", LEGACY_SERVER_HOST}:
        server_data["host"] = PRIMARY_SERVER_HOST

    return data


def _read_legacy_or_current_data() -> tuple[dict, str | None]:
    """Read the current save file, falling back to the legacy bundle path."""
    for path in (DATA_FILE, LEGACY_DATA_FILE):
        if os.path.exists(path):
            data = read_secure_json(
                path,
                default=DEFAULT_DATA,
                migrate_plain_to_encrypted=False,
                scope=SCOPE_DEVICE,
            )
            return _normalize_data_payload(data), path
    return copy.deepcopy(DEFAULT_DATA), None


def log_ui_exception(context: str, exc: Exception):
    """Append a UI exception traceback to a per-user log file."""
    os.makedirs(os.path.dirname(UI_LOG_FILE), exist_ok=True)
    with open(UI_LOG_FILE, "a", encoding="utf-8") as f:
        f.write("\n" + "=" * 72 + "\n")
        f.write(f"Context: {context}\n")
        f.write("".join(traceback.format_exception(type(exc), exc, exc.__traceback__)))


# ══════════════════════════════════════════════════════════════════
# DATA  (load / save)
# ══════════════════════════════════════════════════════════════════

def load_data() -> dict:
    # Ensure avatar directory exists
    os.makedirs(AVATAR_DIR, exist_ok=True)

    try:
        data, source_path = _read_legacy_or_current_data()
        if source_path == LEGACY_DATA_FILE and not os.path.exists(DATA_FILE):
            try:
                write_secure_json(DATA_FILE, data, scope=SCOPE_DEVICE)
            except Exception:
                pass
        return data
    except (json.JSONDecodeError, OSError, SecureStorageError):
        # Corrupted — back up the file we tried to read and start fresh
        backup_source = DATA_FILE if os.path.exists(DATA_FILE) else LEGACY_DATA_FILE
        backup = backup_source + ".bak"
        try:
            import shutil
            shutil.copy2(backup_source, backup)
        except Exception:
            pass
    return copy.deepcopy(DEFAULT_DATA)


def save_data(data: dict, silent: bool = False):
    try:
        write_secure_json(DATA_FILE, data, scope=SCOPE_DEVICE)
    except (OSError, SecureStorageError) as e:
        if not silent:
            raise


# ══════════════════════════════════════════════════════════════════
# LANGUAGE
# ══════════════════════════════════════════════════════════════════

def list_languages() -> list:
    """Return list of language names discovered in data/languages/."""
    names = []
    if os.path.isdir(LANG_DIR):
        for fname in sorted(os.listdir(LANG_DIR)):
            if fname.endswith(".json"):
                try:
                    with open(os.path.join(LANG_DIR, fname), encoding="utf-8") as f:
                        d = json.load(f)
                    names.append(d.get("name", fname.replace(".json", "")))
                except Exception:
                    pass
    return names or ["English"]


def load_language(name: str) -> dict:
    """Load the language file matching 'name'."""
    if os.path.isdir(LANG_DIR):
        for fname in os.listdir(LANG_DIR):
            if fname.endswith(".json"):
                try:
                    path = os.path.join(LANG_DIR, fname)
                    with open(path, encoding="utf-8") as f:
                        d = json.load(f)
                    if d.get("name") == name:
                        return d
                except Exception:
                    pass
    # Minimal English fallback
    return {
        "code": "en", "name": "English",
        "questions_file": "en_questions.json",
        "ui": {}
    }


def load_achievements() -> list:
    for path in (ACH_FILE, LEGACY_ACH_FILE):
        if os.path.exists(path):
            try:
                data = read_secure_json(
                    path,
                    default={"achievements": []},
                    migrate_plain_to_encrypted=False,
                    scope=SCOPE_PORTABLE,
                )
                if path == LEGACY_ACH_FILE and not os.path.exists(ACH_FILE):
                    try:
                        write_secure_json(ACH_FILE, data, scope=SCOPE_PORTABLE)
                    except Exception:
                        pass
                return data.get("achievements", [])
            except Exception:
                pass
    return []


def load_questions_file(questions_file: str) -> list[dict]:
    path = os.path.join(Q_DIR, questions_file)
    try:
        data = read_secure_json(
            path,
            default={"questions": []},
            migrate_plain_to_encrypted=True,
            scope=SCOPE_PORTABLE,
        )
        qs = data.get("questions", [])
        if not qs:
            raise ValueError(f"No questions found in {questions_file}")
        return qs
    except (FileNotFoundError, json.JSONDecodeError, ValueError, SecureStorageError):
        fallback = os.path.join(Q_DIR, "en_questions.json")
        if path != fallback and os.path.exists(fallback):
            data = read_secure_json(
                fallback,
                default={"questions": []},
                migrate_plain_to_encrypted=True,
                scope=SCOPE_PORTABLE,
            )
            return data.get("questions", [])
        raise RuntimeError(f"Cannot load questions: {questions_file}")


# ══════════════════════════════════════════════════════════════════
# VALIDATION
# ══════════════════════════════════════════════════════════════════

def validate_assets(lang_data: dict) -> list:
    """Return list of missing critical files/paths."""
    missing = []
    required = [
        (LANG_DIR,  "data/languages/"),
        (Q_DIR,     "data/questions/"),
        (os.path.join(LANG_DIR, "en.json"), "data/languages/en.json"),
    ]
    qfile = lang_data.get("questions_file", "en_questions.json")
    required.append((os.path.join(Q_DIR, qfile), f"data/questions/{qfile}"))
    for path, label in required:
        if not os.path.exists(path):
            missing.append(label)
    return missing


# ══════════════════════════════════════════════════════════════════
# AVATAR SYSTEM
# ══════════════════════════════════════════════════════════════════

def validate_avatar(file_path: str, max_size_mb: int = 2) -> tuple[bool, str]:
    """
    Validate avatar image file.
    Returns (is_valid, error_message).
    Accepts PNG and JPG files up to max_size_mb.
    """
    if not os.path.exists(file_path):
        return False, "File does not exist"
    
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in [".png", ".jpg", ".jpeg"]:
        return False, "Only PNG and JPG formats are supported"
    
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    if file_size_mb > max_size_mb:
        return False, f"File too large (max {max_size_mb}MB, got {file_size_mb:.1f}MB)"
    
    try:
        from PIL import Image
        img = Image.open(file_path)
        img.verify()
        return True, ""
    except Exception as e:
        return False, f"Invalid image file: {str(e)}"


def save_avatar(source_path: str, profile_name: str) -> str:
    """
    Copy and validate avatar image, save to data/avatars/ with unique name.
    Returns avatar filename (relative to AVATAR_DIR) or None if validation failed.
    """
    is_valid, error = validate_avatar(source_path)
    if not is_valid:
        return None
    
    os.makedirs(AVATAR_DIR, exist_ok=True)
    
    ext = os.path.splitext(source_path)[1].lower()
    import uuid
    avatar_filename = f"{uuid.uuid4().hex}{ext}"
    avatar_path = os.path.join(AVATAR_DIR, avatar_filename)
    
    try:
        import shutil
        shutil.copy2(source_path, avatar_path)
        return avatar_filename
    except Exception as e:
        print(f"Failed to save avatar: {e}")
        return None


def get_avatar_path(avatar_filename: str) -> str:
    """Get full path to avatar file."""
    if not avatar_filename:
        return None

    user_path = os.path.join(AVATAR_DIR, avatar_filename)
    if os.path.exists(user_path):
        return user_path

    legacy_path = os.path.join(LEGACY_AVATAR_DIR, avatar_filename)
    if os.path.exists(legacy_path):
        return legacy_path

    return user_path


def delete_avatar(avatar_filename: str) -> bool:
    """Delete avatar file from disk."""
    if not avatar_filename:
        return False
    path = get_avatar_path(avatar_filename)
    try:
        if os.path.exists(path):
            os.remove(path)
        return True
    except Exception as e:
        print(f"Failed to delete avatar: {e}")
        return False
