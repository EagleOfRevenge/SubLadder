@echo off
setlocal ENABLEDELAYEDEXPANSION

REM build_windows_nuitka.bat — Build SubLadder Windows release with Nuitka
REM Run from project root: build_windows_nuitka.bat [onefile|standalone]

set "BUILD_MODE=%~1"
if "%BUILD_MODE%"=="" set "BUILD_MODE=onefile"
if /I "%BUILD_MODE%"=="onefile" goto mode_ok
if /I "%BUILD_MODE%"=="standalone" goto mode_ok
echo [Sub Ladder] Invalid mode "%BUILD_MODE%".
echo Usage: build_windows_nuitka.bat [onefile^|standalone]
exit /b 1

:mode_ok

set "PY_EXE=.venv312\Scripts\python.exe"
if exist "%PY_EXE%" goto have_python

set "PY_EXE=.venv\Scripts\python.exe"
if exist "%PY_EXE%" goto have_python

set "PY_EXE=python"

:have_python
echo [Sub Ladder] Installing build dependencies for Nuitka...
%PY_EXE% -m pip install --upgrade pip
%PY_EXE% -m pip install -r requirements.txt
%PY_EXE% -m pip install nuitka ordered-set zstandard

echo [Sub Ladder] Validating runtime dependencies...
%PY_EXE% -c "import pygame, PIL" 1>nul 2>nul
if errorlevel 1 (
  echo [Sub Ladder] Missing runtime dependencies in selected Python environment.
  echo [Sub Ladder] Recommended: use Python 3.12 with .venv312.
  exit /b 1
)

echo [Sub Ladder] Cleaning previous Nuitka build output...
if exist build\nuitka rd /s /q build\nuitka
if exist dist\SubLadder-Nuitka rd /s /q dist\SubLadder-Nuitka

echo [Sub Ladder] Building Windows executable with Nuitka...
if /I "%BUILD_MODE%"=="onefile" (
  %PY_EXE% -m nuitka ^
    --standalone ^
    --onefile ^
    --mingw64 ^
    --assume-yes-for-downloads ^
    --windows-console-mode=disable ^
    --windows-company-name="Sub Ladder" ^
    --windows-product-name="Sub Ladder" ^
    --windows-file-version=2.4.0.0 ^
    --windows-product-version=2.4.0.0 ^
    --enable-plugin=tk-inter ^
    --include-data-dir=data\languages=data\languages ^
    --include-data-dir=data\questions=data\questions ^
    --include-data-file=data\achievements.json=data\achievements.json ^
    --include-data-dir=data\pictures=data\pictures ^
    --include-data-dir=data\sound=data\sound ^
    --include-data-dir=game=game ^
    --include-package=game ^
    --nofollow-import-to=unittest,*test* ^
    --output-dir=dist\SubLadder-Nuitka ^
    --remove-output ^
    --reproducible=yes ^
    run.py
) else (
  %PY_EXE% -m nuitka ^
    --standalone ^
    --mingw64 ^
    --assume-yes-for-downloads ^
    --windows-console-mode=disable ^
    --windows-company-name="Sub Ladder" ^
    --windows-product-name="Sub Ladder" ^
    --windows-file-version=2.4.0.0 ^
    --windows-product-version=2.4.0.0 ^
    --enable-plugin=tk-inter ^
    --include-data-dir=data\languages=data\languages ^
    --include-data-dir=data\questions=data\questions ^
    --include-data-file=data\achievements.json=data\achievements.json ^
    --include-data-dir=data\pictures=data\pictures ^
    --include-data-dir=data\sound=data\sound ^
    --include-data-dir=game=game ^
    --include-package=game ^
    --nofollow-import-to=unittest,*test* ^
    --output-dir=dist\SubLadder-Nuitka ^
    --remove-output ^
    --reproducible=yes ^
    run.py
)

if errorlevel 1 (
  echo [Sub Ladder] Nuitka build failed.
  exit /b 1
)

if /I "%BUILD_MODE%"=="onefile" (
  if exist "dist\SubLadder-Nuitka\run.exe" (
    if exist "dist\SubLadder-Nuitka\SubLadder.exe" del /f /q "dist\SubLadder-Nuitka\SubLadder.exe"
    ren "dist\SubLadder-Nuitka\run.exe" "SubLadder.exe"
  )
) else (
  if exist "dist\SubLadder-Nuitka\run.dist\run.exe" (
    if exist "dist\SubLadder-Nuitka\run.dist\SubLadder.exe" del /f /q "dist\SubLadder-Nuitka\run.dist\SubLadder.exe"
    ren "dist\SubLadder-Nuitka\run.dist\run.exe" "SubLadder.exe"
  )
)

echo.
echo [Sub Ladder] Done!
if /I "%BUILD_MODE%"=="onefile" (
  echo Output: dist\SubLadder-Nuitka\SubLadder.exe
) else (
  echo Output: dist\SubLadder-Nuitka\run.dist\SubLadder.exe
)
echo.
echo Build mode: %BUILD_MODE%

endlocal