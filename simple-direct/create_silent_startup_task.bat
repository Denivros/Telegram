@echo off
echo Creating SILENT Windows Task Scheduler entry for MT5 Trading Bot...

:: First delete existing task if it exists
schtasks /delete /tn "MT5TradingBot" /f >nul 2>&1

:: Create the scheduled task with silent execution (no visible window)
:: Run whether user is logged on or not with /it flag
schtasks /create /tn "MT5TradingBot" /tr "wscript.exe \"C:\Users\Administrator\Documents\GitHub\Telegram\simple-direct\start_bot_silent.vbs\"" /sc onstart /ru "Administrator" /rp "" /rl highest /delay 0002:00 /it /f

if %errorlevel% equ 0 (
    echo ✅ SILENT Task created successfully!
    echo The bot will now start automatically when Windows boots with:
    echo   - 2 minute startup delay
    echo   - MT5 availability checking ^(up to 10 minutes^)
    echo   - NO VISIBLE TERMINAL WINDOW ^(runs silently in background^)
    echo   - Runs whether user is logged on or not
    echo   - Automatic retry and error handling
    echo.
    echo To manage the task:
    echo - View: schtasks /query /tn "MT5TradingBot"
    echo - Delete: schtasks /delete /tn "MT5TradingBot" /f
    echo - Run now: schtasks /run /tn "MT5TradingBot"
    echo - Test silent: wscript start_bot_silent.vbs
    echo - Test visible: start_bot_with_mt5_check.bat
    echo.
    echo 🔍 To monitor the bot:
    echo - Health URL: http://51.75.64.102:8080/health
    echo - Log file: direct_mt5_monitor.log
    echo - Task Manager: Look for "python.exe" process
    goto end
) else (
    echo ❌ Failed to create task. Please run as Administrator.
    goto end
)

:end

pause