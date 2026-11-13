$ErrorActionPreference = 'Stop'
$meowBackend = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location -LiteralPath $meowBackend
$env:PYTHONPATH = $meowBackend + ';' + (Resolve-Path './private/flash-validation-tools').Path
$meowPid = [int](Get-Content -LiteralPath (Join-Path $PSScriptRoot 'loyalty-backend.pid'))
$meowProcess = Get-CimInstance Win32_Process -Filter "ProcessId=$meowPid"
if (-not $meowProcess -or $meowProcess.CommandLine -notmatch 'uvicorn.+server:app') { throw 'Backend process changed; review before restarting' }
$meowIdentity = Invoke-RestMethod -Uri 'http://127.0.0.1:8001/api/' -TimeoutSec 5
if ($meowIdentity.app -ne 'Meow Eyes') { throw 'Unexpected application on port 8001' }
Stop-Process -Id $meowPid
Wait-Process -Id $meowPid -Timeout 15 -ErrorAction SilentlyContinue
$meowStarted = Start-Process -FilePath 'C:\Python314\python.exe' -ArgumentList @('-m','uvicorn','server:app','--host','0.0.0.0','--port','8001') -WorkingDirectory $meowBackend -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $PSScriptRoot 'loyalty-backend.stdout.log') -RedirectStandardError (Join-Path $PSScriptRoot 'loyalty-backend.stderr.log')
Set-Content -LiteralPath (Join-Path $PSScriptRoot 'loyalty-backend.pid') -Value $meowStarted.Id
$meowHealthy = $false
foreach ($meowAttempt in 1..20) {
    Start-Sleep -Milliseconds 1000
    try { $meowHealth = Invoke-RestMethod -Uri 'http://127.0.0.1:8001/api/health/ready' -TimeoutSec 2; if ($meowHealth.ok) { $meowHealthy = $true; break } } catch { }
}
if (-not $meowHealthy) { throw 'Backend readiness requires review' }
& 'C:\Python314\python.exe' private/verify-loyalty-live.py
if ($LASTEXITCODE -ne 0) { throw 'Live checks require review' }
Write-Output "Backend ready on port 8001, PID $($meowStarted.Id)"
