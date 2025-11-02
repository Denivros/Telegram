@echo off
echo Starting MT5 Trading Bot with MT5 dependency check...
echo.

cd /d "C:\Users\Administrator\Documents\GitHub\Telegram\simple-direct"

:: Wait for MT5 to be available (check for up to 10 minutes)
echo Waiting for MetaTrader 5 to be available...
set /a counter=0
set /a max_attempts=60

:check_mt5
set /a counter+=1
echo Attempt %counter%/%max_attempts% - Checking MT5 availability...

:: Check if MT5 process is running (multiple possible names)
tasklist /FI "IMAGENAME eq terminal64.exe" 2>NUL | find /I /N "terminal64.exe" >NUL
if %ERRORLEVEL%==0 (
    echo ✅ MT5 terminal64.exe found running!
    goto start_bot
)

tasklist /FI "IMAGENAME eq metatrader.exe" 2>NUL | find /I /N "metatrader.exe" >NUL
if %ERRORLEVEL%==0 (
    echo ✅ MT5 metatrader.exe found running!
    goto start_bot
)

tasklist /FI "IMAGENAME eq MetaTrader.exe" 2>NUL | find /I /N "MetaTrader.exe" >NUL
if %ERRORLEVEL%==0 (
    echo ✅ MT5 MetaTrader.exe found running!
    goto start_bot
)

tasklist /FI "IMAGENAME eq mt5.exe" 2>NUL | find /I /N "mt5.exe" >NUL
if %ERRORLEVEL%==0 (
    echo ✅ MT5 mt5.exe found running!
    goto start_bot
)

if %counter% geq %max_attempts% (
    echo ❌ MT5 not found after %max_attempts% attempts. Starting bot anyway...
    echo    Bot will attempt to connect to remote MT5 or wait for local MT5.
    goto start_bot
)

:: Wait 10 seconds before next check
echo    MT5 not found, waiting 10 seconds...
timeout /t 10 /nobreak >nul
goto check_mt5

:start_bot
echo.
echo 🚀 Starting MT5 Trading Bot...
echo Time: %date% %time%
echo Current User: %USERNAME%
echo Current Directory: %CD%
echo.

:: Show running MT5 processes before starting bot
echo 🔍 Currently running MT5 processes:
tasklist /FI "IMAGENAME eq terminal*" /FO TABLE
tasklist /FI "IMAGENAME eq metatrader*" /FO TABLE
tasklist /FI "IMAGENAME eq mt5*" /FO TABLE
echo.

:: Start the Python bot with verbose output
echo 📊 Starting Python trading bot...
python direct_mt5_monitor.py

:: If bot exits, log the event
echo.
echo ⚠️  Bot stopped at %date% %time%
echo    Check logs for details: direct_mt5_monitor.log
echo.

:: Keep window open for 30 seconds to see any error messages
echo Window will close in 30 seconds...
timeout /t 30 /nobreak >nul