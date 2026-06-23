# TrustCheck Startup Script
Write-Host "Starting TrustCheck Backend..." -ForegroundColor Green
Start-Process python -ArgumentList "main.py" -WorkingDirectory "$PSScriptRoot\backend" -WindowStyle Normal

Write-Host "Waiting for backend to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

Write-Host "Starting TrustCheck Frontend..." -ForegroundColor Green
Start-Process npm -ArgumentList "run", "dev" -WorkingDirectory "$PSScriptRoot\frontend" -WindowStyle Normal

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "TrustCheck is starting!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Backend:  http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "Frontend: http://127.0.0.1:3000" -ForegroundColor Green
Write-Host "`nTwo new windows should have opened." -ForegroundColor Yellow
Write-Host "Press any key to exit this script..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")