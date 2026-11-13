$ErrorActionPreference = 'Stop'
$meowBackend = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location -LiteralPath $meowBackend
$env:PYTHONPATH = $meowBackend + ';' + (Resolve-Path './private/flash-validation-tools').Path
& 'C:\Python314\python.exe' private/apply-loyalty-migration.py --resume-empty
if ($LASTEXITCODE -ne 0) { throw 'Migration failed; inspect private/loyalty-migration.log' }
if (Get-NetTCPConnection -LocalPort 8001 -State Listen -ErrorAction SilentlyContinue) { throw 'Another backend is already using port 8001' }
$meowStarted = Start-Process -FilePath 'C:\Python314\python.exe' -ArgumentList @('-m','uvicorn','server:app','--host','0.0.0.0','--port','8001') -WorkingDirectory $meowBackend -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $PSScriptRoot 'loyalty-backend.stdout.log') -RedirectStandardError (Join-Path $PSScriptRoot 'loyalty-backend.stderr.log')
Set-Content -LiteralPath (Join-Path $PSScriptRoot 'loyalty-backend.pid') -Value $meowStarted.Id
foreach ($meowAttempt in 1..20) {
    Start-Sleep -Milliseconds 1000
    try { $meowHealth = Invoke-RestMethod -Uri 'http://127.0.0.1:8001/api/health/ready' -TimeoutSec 2; if ($meowHealth.ok) { Write-Output "Meow Eyes backend ready on port 8001, PID $($meowStarted.Id)"; exit 0 } } catch { }
}
throw 'Migration completed but backend readiness requires review'
