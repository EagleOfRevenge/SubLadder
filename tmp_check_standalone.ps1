$exe = 'D:\Program Files (x86)\SubLadder\dist\SubLadder-Nuitka\run.dist\SubLadder.exe'
if (-not (Test-Path $exe)) {
    Write-Output 'STANDALONE_EXE_MISSING'
    exit 0
}
$p = Start-Process -FilePath $exe -PassThru
try {
    Wait-Process -Id $p.Id -Timeout 5
    Write-Output ("STANDALONE_EXITED=1 CODE=" + $p.ExitCode)
}
catch {
    Write-Output ("STANDALONE_RUNNING=1 PID=" + $p.Id)
}
