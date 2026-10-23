param(
  [int]$StartupRuns = 3
)

$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$buildScript = Join-Path $root 'build_windows_nuitka.bat'
$nuitkaRoot = Join-Path $root 'dist\SubLadder-Nuitka'
$compareRoot = Join-Path $root 'dist\SubLadder-Nuitka-compare'

function Get-FileSizeMB {
  param([string]$Path)
  if (!(Test-Path $Path)) { return $null }
  $size = (Get-Item $Path).Length
  return [math]::Round($size / 1MB, 2)
}

function Get-FolderSizeMB {
  param([string]$Path)
  if (!(Test-Path $Path)) { return $null }
  $sum = (Get-ChildItem -Path $Path -File -Recurse | Measure-Object -Property Length -Sum).Sum
  return [math]::Round(($sum / 1MB), 2)
}

function Measure-StartupMs {
  param([string]$ExePath, [int]$Runs)
  if (!(Test-Path $ExePath)) { return $null }

  $values = @()
  for ($i = 1; $i -le $Runs; $i++) {
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $proc = Start-Process -FilePath $ExePath -PassThru
    try {
      $null = $proc.WaitForInputIdle(20000)
    }
    catch {
      # Ignore, we still keep elapsed start time sample.
    }
    $sw.Stop()
    $values += $sw.Elapsed.TotalMilliseconds
    Start-Sleep -Milliseconds 400
    if (!$proc.HasExited) {
      Stop-Process -Id $proc.Id -Force
    }
    Start-Sleep -Milliseconds 300
  }

  return [math]::Round((($values | Measure-Object -Average).Average), 0)
}

if (!(Test-Path $buildScript)) {
  throw "Missing build script: $buildScript"
}

if (Test-Path $compareRoot) {
  Remove-Item -Path $compareRoot -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $compareRoot | Out-Null

Write-Host '[Sub Ladder] Building Nuitka onefile...'
& $buildScript onefile
if ($LASTEXITCODE -ne 0) {
  throw 'Onefile build failed.'
}

$onefileExe = Join-Path $nuitkaRoot 'SubLadder.exe'
if (!(Test-Path $onefileExe)) {
  throw "Expected onefile exe not found: $onefileExe"
}

$onefileOut = Join-Path $compareRoot 'onefile'
New-Item -ItemType Directory -Force -Path $onefileOut | Out-Null
Copy-Item -Path $onefileExe -Destination (Join-Path $onefileOut 'SubLadder.exe') -Force

Write-Host '[Sub Ladder] Building Nuitka standalone...'
& $buildScript standalone
if ($LASTEXITCODE -ne 0) {
  throw 'Standalone build failed.'
}

$standaloneDir = Join-Path $nuitkaRoot 'run.dist'
if (!(Test-Path $standaloneDir)) {
  throw "Expected standalone folder not found: $standaloneDir"
}

$standaloneOut = Join-Path $compareRoot 'standalone'
Copy-Item -Path $standaloneDir -Destination $standaloneOut -Recurse -Force

$onefileSize = Get-FileSizeMB -Path (Join-Path $onefileOut 'SubLadder.exe')
$standaloneSize = Get-FolderSizeMB -Path $standaloneOut

$onefileStart = Measure-StartupMs -ExePath (Join-Path $onefileOut 'SubLadder.exe') -Runs $StartupRuns
$standaloneStart = Measure-StartupMs -ExePath (Join-Path $standaloneOut 'SubLadder.exe') -Runs $StartupRuns

$report = @"
Sub Ladder - Nuitka Compare
===========================

Runs per startup benchmark: $StartupRuns

ONEFILE
- Path: $onefileOut\SubLadder.exe
- Size: $onefileSize MB
- Avg startup to input-idle: $onefileStart ms

STANDALONE
- Path: $standaloneOut\SubLadder.exe
- Folder size: $standaloneSize MB
- Avg startup to input-idle: $standaloneStart ms

Recommendation:
- Prefer ONEFILE for simple distribution.
- Prefer STANDALONE for usually faster cold startup and easier patching.
"@

$reportPath = Join-Path $compareRoot 'report.txt'
Set-Content -Path $reportPath -Value $report -Encoding UTF8

Write-Host '[Sub Ladder] Comparison done.'
Write-Host "Report: $reportPath"