param(
  [string]$OutputPath = "D:\Program Files (x86)\SubLadder\dist\SubLadder-Installer"
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$nuitkaRoot = Join-Path $root 'dist\SubLadder-Nuitka'
$onefileExe = Join-Path $nuitkaRoot 'SubLadder.exe'
$standaloneDir = Join-Path $nuitkaRoot 'run.dist'

New-Item -ItemType Directory -Force -Path $OutputPath | Out-Null

if (Test-Path $onefileExe) {
  Copy-Item -Path $onefileExe -Destination (Join-Path $OutputPath 'SubLadder.exe') -Force
  $sourceType = 'nuitka-onefile'
}
elseif (Test-Path $standaloneDir) {
  Copy-Item -Path (Join-Path $standaloneDir '*') -Destination $OutputPath -Recurse -Force
  $sourceType = 'nuitka-standalone'
}
else {
  throw "No Nuitka build output found. Run .\\build_windows_nuitka.bat first."
}

$readme = @"
Sub Ladder
==========

Ce dossier contient l'exécutable Windows du jeu.

- Exécutez SubLadder.exe pour lancer le jeu.
- Le jeu inclut ses assets nécessaires (langues, questions, images et sons).
- Le serveur et la documentation ne sont pas inclus.
- Source du package: $sourceType
"@

Set-Content -Path (Join-Path $OutputPath 'README.txt') -Value $readme -Encoding UTF8

Write-Host "Installation package created at: $OutputPath"
