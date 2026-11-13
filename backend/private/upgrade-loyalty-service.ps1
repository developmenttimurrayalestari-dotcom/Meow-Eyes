$ErrorActionPreference = 'Stop'
$meowBackend = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location -LiteralPath $meowBackend
$meowPid = 3272
$meowProcess = Get-CimInstance Win32_Process -Filter "ProcessId=$meowPid"
if (-not $meowProcess -or $meowProcess.Name -ne 'python.exe' -or $meowProcess.CommandLine -notmatch 'uvicorn.+server:app') { throw 'Backend process changed; review before stopping any process' }
$meowIdentity = Invoke-RestMethod -Uri 'http://127.0.0.1:8001/api/' -TimeoutSec 5
if ($meowIdentity.app -ne 'Meow Eyes') { throw 'Port 8001 does not identify the Meow Eyes backend' }
Stop-Process -Id $meowPid
Wait-Process -Id $meowPid -Timeout 15 -ErrorAction SilentlyContinue
$env:PYTHONPATH = $meowBackend + ';' + (Resolve-Path './private/flash-validation-tools').Path
& 'C:\Python314\python.exe' private/backup-loyalty-migration.py
if ($LASTEXITCODE -ne 0) { throw 'Full backup failed; migration was not started' }
& 'C:\Python314\python.exe' private/apply-loyalty-migration.py
if ($LASTEXITCODE -ne 0) { throw 'Migration requires review; inspect private/loyalty-migration.log' }
$meowListeners = Get-NetTCPConnection -LocalPort 8001 -State Listen -ErrorAction SilentlyContinue
if ($meowListeners) { throw 'Another backend already started; no additional instance was launched' }
$meowStarted = Start-Process -FilePath 'C:\Python314\python.exe' -ArgumentList @('-m','uvicorn','server:app','--host','0.0.0.0','--port','8001') -WorkingDirectory $meowBackend -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $PSScriptRoot 'loyalty-backend.stdout.log') -RedirectStandardError (Join-Path $PSScriptRoot 'loyalty-backend.stderr.log')
Set-Content -LiteralPath (Join-Path $PSScriptRoot 'loyalty-backend.pid') -Value $meowStarted.Id
$meowHealthy = $false
foreach ($meowAttempt in 1..20) {
    Start-Sleep -Milliseconds 1000
    try {
        $meowHealth = Invoke-RestMethod -Uri 'http://127.0.0.1:8001/api/health/ready' -TimeoutSec 2
        if ($meowHealth.ok) { $meowHealthy = $true; break }
    } catch { }
}
if (-not $meowHealthy) { throw 'Database migrated but backend readiness failed; inspect private/loyalty-backend.stderr.log' }
Write-Output "Meow Eyes backend ready on port 8001, PID $($meowStarted.Id)"
