# MT5 Trading Bot Monitor 
Write-Host "🤖 MT5 Trading Bot Monitor" -ForegroundColor Green 
Write-Host "================================" -ForegroundColor Green 
Write-Host "" 
# Change to bot directory 
Set-Location "C:\Users\Administrator\Documents\GitHub\Telegram\simple-direct" 
Write-Host "📂 Bot Directory: $PWD" -ForegroundColor Yellow 
Write-Host "" 
# Show bot process status 
Write-Host "🔍 Bot Process Status:" -ForegroundColor Cyan 
Get-Process python -ErrorAction SilentlyContinue | Format-Table ProcessName,Id,StartTime,CPU 
Write-Host "" 
# Show health status 
Write-Host "💚 Bot Health Check:" -ForegroundColor Cyan 
try { 
    $health = Invoke-RestMethod -Uri "http://localhost:8080/health" -Method GET -TimeoutSec 5 
    Write-Host "Status: $($health.status)" -ForegroundColor Green 
    Write-Host "MT5 Connected: $($health.mt5_connected)" -ForegroundColor Green 
    Write-Host "Balance: $($health.account.balance)" -ForegroundColor Green 
    Write-Host "Open Positions: $($health.trades.open_positions)" -ForegroundColor Green 
    Write-Host "Pending Orders: $($health.trades.pending_orders)" -ForegroundColor Green 
} catch { 
    Write-Host "❌ Health check failed - Bot may not be running" -ForegroundColor Red 
} 
Write-Host "" 
Write-Host "📊 Live Log Monitor (Ctrl+C to stop):" -ForegroundColor Cyan 
Write-Host "======================================" -ForegroundColor Cyan 
Get-Content "direct_mt5_monitor.log" -Wait -Tail 10 
