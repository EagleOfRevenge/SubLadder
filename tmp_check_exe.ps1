$exe = 'D:\Program Files (x86)\SubLadder\dist\SubLadder-Installer\SubLadder.exe'
$p = Start-Process -FilePath $exe -PassThru
try {
    Wait-Process -Id $p.Id -Timeout 5 -ErrorAction Stop
    Write-Output ("ONEFILE_EXITED=1 CODE=" + $p.ExitCode)
}
catch {
    Write-Output ("ONEFILE_RUNNING=1 PID=" + $p.Id)
}
if (-not $p.HasExited) {
    Stop-Process -Id $p.Id -Force
}
