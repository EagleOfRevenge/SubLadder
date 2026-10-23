#!/usr/bin/env bash
# build.sh — run from SubLadder/ folder
# Works on Linux and macOS

set -e
echo "[Sub Ladder] Installing build dependencies..."
pip install pyinstaller pillow pygame

echo "[Sub Ladder] Building executable..."
pyinstaller SubLadder.spec --clean

echo ""
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Done! macOS binary: dist/SubLadder/SubLadder"
    echo "Tip: to create a .app bundle, see BUILD.md"
else
    echo "Done! Linux binary: dist/SubLadder/SubLadder"
    chmod +x dist/SubLadder/SubLadder
    echo "Run with: ./dist/SubLadder/SubLadder"
fi
