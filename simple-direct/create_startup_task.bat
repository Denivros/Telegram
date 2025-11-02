@echo off
echo Creating Windows Task Scheduler entry for MT5 Trading Bot...

:: First delete existing task if it exists
schtasks /delete /tn "MT5TradingBot" /f >nul 2>&1

:: Create the scheduled task with 2 minute delay for MT5 to start
:: Run as Administrator user and configure to run whether user is logged on or not
schtasks /create /tn "MT5TradingBot" /tr "\"C:\Users\Administrator\Documents\GitHub\Telegram\simple-direct\start_bot_with_mt5_check.bat\"" /sc onstart /ru "Administrator" /rp "" /rl highest /delay 0002:00 /it /f

if %errorlevel% equ 0 (
    echo ✅ Task created successfully!
    echo The bot will now start automatically when Windows boots with:
    echo   - 2 minute startup delay
    echo   - MT5 availability checking ^(up to 10 minutes^)
    echo   - Automatic retry and error handling
    echo.
    echo To manage the task:
    echo - View: schtasks /query /tn "MT5TradingBot"
    echo - Delete: schtasks /delete /tn "MT5TradingBot" /f
    echo - Run now: schtasks /run /tn "MT5TradingBot"
    echo - Test script: start_bot_with_mt5_check.bat
    goto end
) else (
    echo ❌ Failed to create task. Please run as Administrator.
    goto end
)

:end

pause