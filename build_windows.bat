@echo off
:: build_windows.bat — run from SubLadder\ folder
echo [Sub Ladder] Installing build dependencies...
pip install pyinstaller pillow pygame
echo [Sub Ladder] Building Windows executable...
pyinstaller SubLadder.spec --clean
echo.
echo Done! Your game is in: dist\SubLadder\SubLadder.exe
pause
