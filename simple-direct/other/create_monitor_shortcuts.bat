@echo off
echo Creating Bot Monitor shortcuts...

:: Create PowerShell script for monitoring
set "MONITOR_SCRIPT=C:\Users\Administrator\Documents\GitHub\Telegram\simple-direct\monitor_bot.ps1"

echo # MT5 Trading Bot Monitor > "%MONITOR_SCRIPT%"
echo Write-Host "🤖 MT5 Trading Bot Monitor" -ForegroundColor Green >> "%MONITOR_SCRIPT%"
echo Write-Host "================================" -ForegroundColor Green >> "%MONITOR_SCRIPT%"
echo Write-Host "" >> "%MONITOR_SCRIPT%"
echo # Change to bot directory >> "%MONITOR_SCRIPT%"
echo Set-Location "C:\Users\Administrator\Documents\GitHub\Telegram\simple-direct" >> "%MONITOR_SCRIPT%"
echo Write-Host "📂 Bot Directory: $PWD" -ForegroundColor Yellow >> "%MONITOR_SCRIPT%"
echo Write-Host "" >> "%MONITOR_SCRIPT%"
echo # Show bot process status >> "%MONITOR_SCRIPT%"
echo Write-Host "🔍 Bot Process Status:" -ForegroundColor Cyan >> "%MONITOR_SCRIPT%"
echo Get-Process python -ErrorAction SilentlyContinue ^| Format-Table ProcessName,Id,StartTime,CPU >> "%MONITOR_SCRIPT%"
echo Write-Host "" >> "%MONITOR_SCRIPT%"
echo # Show health status >> "%MONITOR_SCRIPT%"
echo Write-Host "💚 Bot Health Check:" -ForegroundColor Cyan >> "%MONITOR_SCRIPT%"
echo try { >> "%MONITOR_SCRIPT%"
echo     $health = Invoke-RestMethod -Uri "http://localhost:8080/health" -Method GET -TimeoutSec 5 >> "%MONITOR_SCRIPT%"
echo     Write-Host "Status: $($health.status)" -ForegroundColor Green >> "%MONITOR_SCRIPT%"
echo     Write-Host "MT5 Connected: $($health.mt5_connected)" -ForegroundColor Green >> "%MONITOR_SCRIPT%"
echo     Write-Host "Balance: $($health.account.balance)" -ForegroundColor Green >> "%MONITOR_SCRIPT%"
echo     Write-Host "Open Positions: $($health.trades.open_positions)" -ForegroundColor Green >> "%MONITOR_SCRIPT%"
echo     Write-Host "Pending Orders: $($health.trades.pending_orders)" -ForegroundColor Green >> "%MONITOR_SCRIPT%"
echo } catch { >> "%MONITOR_SCRIPT%"
echo     Write-Host "❌ Health check failed - Bot may not be running" -ForegroundColor Red >> "%MONITOR_SCRIPT%"
echo } >> "%MONITOR_SCRIPT%"
echo Write-Host "" >> "%MONITOR_SCRIPT%"
echo Write-Host "📊 Live Log Monitor (Ctrl+C to stop):" -ForegroundColor Cyan >> "%MONITOR_SCRIPT%"
echo Write-Host "======================================" -ForegroundColor Cyan >> "%MONITOR_SCRIPT%"
echo Get-Content "direct_mt5_monitor.log" -Wait -Tail 10 >> "%MONITOR_SCRIPT%"

:: Create Desktop shortcuts using PowerShell
powershell -Command "& {
    # Monitor shortcut
    $WshShell = New-Object -comObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut('C:\Users\Administrator\Desktop\🤖 Bot Monitor.lnk')
    $Shortcut.TargetPath = 'powershell.exe'
    $Shortcut.Arguments = '-NoExit -ExecutionPolicy Bypass -File \"C:\Users\Administrator\Documents\GitHub\Telegram\simple-direct\monitor_bot.ps1\"'
    $Shortcut.WorkingDirectory = 'C:\Users\Administrator\Documents\GitHub\Telegram\simple-direct'
    $Shortcut.IconLocation = 'powershell.exe,0'
    $Shortcut.Description = 'Monitor MT5 Trading Bot'
    $Shortcut.Save()
    
    # Quick Health Check shortcut
    $Shortcut2 = $WshShell.CreateShortcut('C:\Users\Administrator\Desktop\💚 Bot Health.lnk')
    $Shortcut2.TargetPath = 'powershell.exe'
    $Shortcut2.Arguments = '-Command \"Invoke-RestMethod http://localhost:8080/health | Format-List; Read-Host 'Press Enter to close'\"'
    $Shortcut2.IconLocation = 'powershell.exe,0'
    $Shortcut2.Description = 'Quick Bot Health Check'
    $Shortcut2.Save()
    
    # Bot Directory shortcut
    $Shortcut3 = $WshShell.CreateShortcut('C:\Users\Administrator\Desktop\📁 Bot Folder.lnk')
    $Shortcut3.TargetPath = 'C:\Users\Administrator\Documents\GitHub\Telegram\simple-direct'
    $Shortcut3.Description = 'Open Bot Directory'
    $Shortcut3.Save()
}"

echo.
echo ✅ Bot Monitor shortcuts created on Desktop:
echo.
echo 🤖 Bot Monitor.lnk      - Live log monitoring with status
echo 💚 Bot Health.lnk      - Quick health check  
echo 📁 Bot Folder.lnk      - Open bot directory
echo.
echo 🎯 Just double-click "🤖 Bot Monitor" to watch your bot!
echo.
pause