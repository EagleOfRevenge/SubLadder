# Sub Ladder — game package
# Re-export App lazily so importing game modules does not eagerly load the full UI stack.

import os
import sys

# Make the package-local modules importable when the package is imported directly
# (for example by tests or tooling), not only when run.py has prepended the game
# directory to sys.path.
if getattr(sys, "frozen", False):
    # Frozen / Nuitka build — sys._MEIPASS may not exist; derive game dir from exe.
    _frozen_base = getattr(sys, "_MEIPASS", None) or os.path.dirname(sys.executable)
    _package_dir = os.path.join(_frozen_base, "game")
else:
    _package_dir = os.path.dirname(os.path.abspath(__file__))

PACKAGE_DIR = _package_dir
if PACKAGE_DIR not in sys.path:
    sys.path.insert(0, PACKAGE_DIR)


def __getattr__(name):
    if name == "App":
        from .main import App
        return App
    raise AttributeError(name)


__all__ = ["App"]
