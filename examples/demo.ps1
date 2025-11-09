# Demo script for QueueCTL (PowerShell)

Write-Host "=== QueueCTL Demo ===" -ForegroundColor Cyan
Write-Host ""

# Clean up any existing database
if (Test-Path "queuectl.db") {
    Remove-Item "queuectl.db"
}

Write-Host "1. Enqueue some jobs..." -ForegroundColor Yellow
python -m queuectl.cli enqueue '{"id":"job1","command":"echo Hello from job1"}'
python -m queuectl.cli enqueue '{"id":"job2","command":"timeout /t 1 /nobreak >nul && echo Hello from job2"}'
python -m queuectl.cli enqueue '{"id":"job3","command":"echo Hello from job3"}'

Write-Host ""
Write-Host "2. Check status..." -ForegroundColor Yellow
python -m queuectl.cli status

Write-Host ""
Write-Host "3. List pending jobs..." -ForegroundColor Yellow
python -m queuectl.cli list --state pending

Write-Host ""
Write-Host "4. Start a worker..." -ForegroundColor Yellow
Write-Host "Note: In PowerShell, start worker in a separate window or use Start-Process"
Write-Host "Example: Start-Process python -ArgumentList '-m','queuectl.cli','worker','start','--count','1'"

Write-Host ""
Write-Host "5. After worker processes jobs, check status..." -ForegroundColor Yellow
Write-Host "Run: python -m queuectl.cli status"

Write-Host ""
Write-Host "6. Test failed job with retries..." -ForegroundColor Yellow
python -m queuectl.cli enqueue '{"id":"failed-job","command":"exit /b 1","max_retries":2}'

Write-Host ""
Write-Host "7. Check DLQ..." -ForegroundColor Yellow
Write-Host "Run: python -m queuectl.cli dlq list"

Write-Host ""
Write-Host "8. Check configuration..." -ForegroundColor Yellow
python -m queuectl.cli config get

Write-Host ""
Write-Host "=== Demo Complete ===" -ForegroundColor Cyan

