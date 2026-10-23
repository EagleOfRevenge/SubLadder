"""
Sub Ladder — launcher
Run this file from the project root to start the game.

  python run.py          (any platform)
  ./run.py               (Linux/macOS after chmod +x)
  Double-click run.py    (Windows with Python installed)

Project layout:
  SubLadder/
  ├── run.py              ← you are here
  ├── game/               ← Python source package
  │   ├── __init__.py
  │   ├── main.py         ← App(tk.Tk) orchestrator
  │   ├── constants.py    ← all constants, XP system, colors
  │   ├── game_state.py   ← GameState + question helpers
  │   ├── utils.py        ← data persistence, language loading
  │   ├── asset_manager.py
  │   ├── first_run.py
  │   ├── screens/        ← one file per UI screen
  │   ├── singleplayer/   ← solo game logic + anticheat
  │   └── multiplayer/    ← v6.0+ stubs
  └── data/               ← assets & config (no .py files)
"""

import os
import sys
import json
import traceback
from datetime import datetime
import importlib
import importlib.util

# ── Resolve paths ────────────────────────────────────────────────
# Nuitka / PyInstaller detection — when frozen, __file__ points inside
# the extraction directory and we must derive paths from sys.executable.
if getattr(sys, "frozen", False):
    _frozen_base = getattr(sys, "_MEIPASS", None) or os.path.dirname(sys.executable)
    ROOT_DIR = _frozen_base
    GAME_DIR = os.path.join(_frozen_base, "game")
    DATA_DIR = os.path.join(_frozen_base, "data")
else:
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
    GAME_DIR = os.path.join(ROOT_DIR, "game")
    DATA_DIR = os.path.join(ROOT_DIR, "data")

sys.path.insert(0, GAME_DIR)


def _load_game_module(module_name: str):
    """Load a game module robustly from source or packaged contexts."""
    candidates = [f"game.{module_name}", module_name]
    for candidate in candidates:
        try:
            return importlib.import_module(candidate)
        except ModuleNotFoundError as exc:
            if exc.name not in {candidate, module_name}:
                raise

    module_path = os.path.join(GAME_DIR, f"{module_name}.py")
    if os.path.exists(module_path):
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module

    raise ModuleNotFoundError(f"No module named '{module_name}'")


def _install_legacy_import_aliases():
    """Map legacy top-level imports to game.* modules for frozen builds."""
    alias_modules = [
        "secure_storage",
        "constants",
        "utils",
        "game_state",
        "asset_manager",
        "ui_helpers",
        "anticheat_shared",
    ]
    alias_packages = ["screens", "singleplayer", "multiplayer", "auth"]
    alias_submodules = {
        "screens": [
            "pre_menu",
            "menu",
            "game_screen",
            "recap",
            "profile",
            "top_scores",
            "achievements",
            "options",
            "multiplayer_normal",
            "friend_list",
            "ranked",
            "auth",
            "streamer_config",
            "streamer_game_streamer",
            "streamer_game_viewvers",
            "streamer_podium",
            "streamer_results",
        ],
        "auth": ["client", "tokens"],
    }

    for name in alias_modules:
        try:
            sys.modules[name] = importlib.import_module(f"game.{name}")
        except ModuleNotFoundError:
            pass

    for name in alias_packages:
        try:
            pkg = importlib.import_module(f"game.{name}")
            sys.modules[name] = pkg
            for sub in alias_submodules.get(name, []):
                try:
                    sys.modules[f"{name}.{sub}"] = importlib.import_module(f"game.{name}.{sub}")
                except ModuleNotFoundError:
                    pass
        except ModuleNotFoundError:
            pass


def _emit_first_run_output(first_run_result: dict):
    """Print first-run payload before App initializes and writes data.json."""
    if not isinstance(first_run_result, dict):
        return

    payload = dict(first_run_result)
    token = payload.get("online_token")
    if isinstance(token, str) and token:
        payload["online_token"] = f"{token[:8]}..." if len(token) > 8 else "***"

    print("[FIRST_RUN_OUTPUT]", json.dumps(payload, ensure_ascii=False, sort_keys=True), flush=True)


def _startup_log_path() -> str:
    """Return a writable startup log path for both source and packaged runs."""
    local_app_data = os.getenv("LOCALAPPDATA")
    if local_app_data:
        log_dir = os.path.join(local_app_data, "SubLadder", "logs")
    else:
        log_dir = os.path.join(ROOT_DIR, "logs")
    os.makedirs(log_dir, exist_ok=True)
    return os.path.join(log_dir, "startup_error.log")


def _report_startup_exception(exc: Exception):
    """Persist startup traceback and show a simple Windows error popup."""
    log_path = _startup_log_path()
    with open(log_path, "a", encoding="utf-8") as f:
        f.write("\n" + "=" * 72 + "\n")
        f.write(f"[{datetime.now().isoformat()}] Startup failure\n")
        f.write(f"Python: {sys.version}\n")
        f.write(f"Executable: {sys.executable}\n")
        f.write(f"Root: {ROOT_DIR}\n")
        f.write("\n")
        f.write("".join(traceback.format_exception(type(exc), exc, exc.__traceback__)))

    message = (
        "Sub Ladder failed to start.\n\n"
        f"Details were written to:\n{log_path}"
    )
    try:
        # Avoid tkinter dependency for crash popups in early startup failures.
        import ctypes
        ctypes.windll.user32.MessageBoxW(None, message, "Sub Ladder - Startup Error", 0x10)
    except Exception:
        pass


def _collect_first_run_result() -> dict | None:
    """Run first-run wizard if data.json is missing."""
    from utils import DATA_FILE, LEGACY_DATA_FILE

    if os.path.exists(DATA_FILE) or os.path.exists(LEGACY_DATA_FILE):
        return None

    first_run_module = _load_game_module("first_run")
    run_wizard = first_run_module.run_wizard

    lang_dir = os.path.join(DATA_DIR, "languages")
    flag_dir = os.path.join(DATA_DIR, "pictures", "flags")
    available = []
    if os.path.isdir(lang_dir):
        for fname in sorted(os.listdir(lang_dir)):
            if fname.endswith(".json"):
                try:
                    with open(os.path.join(lang_dir, fname), encoding="utf-8") as f:
                        d = json.load(f)
                    available.append(d.get("name", fname.replace(".json", "")))
                except Exception:
                    pass
    if not available:
        available = ["English"]

    first_run_result = run_wizard(available, flag_dir)
    _emit_first_run_output(first_run_result)
    return first_run_result


if __name__ == "__main__":
    try:
        _install_legacy_import_aliases()
        first_run_result = _collect_first_run_result()
        main_module = _load_game_module("main")
        App = main_module.App
        app = App(first_run_result=first_run_result)
        app.mainloop()
    except Exception as exc:
        _report_startup_exception(exc)
        raise
