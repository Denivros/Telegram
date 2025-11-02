@echo off
echo Setting up MT5 Auto-Start...
echo.

:: Check common MT5 installation paths
set "MT5_PATH="
if exist "C:\Program Files\MetaTrader 5\terminal64.exe" (
    set "MT5_PATH=C:\Program Files\MetaTrader 5\terminal64.exe"
) else if exist "C:\Program Files (x86)\MetaTrader 5\terminal64.exe" (
    set "MT5_PATH=C:\Program Files (x86)\MetaTrader 5\terminal64.exe"
) else if exist "C:\Program Files\MetaTrader 5\metatrader.exe" (
    set "MT5_PATH=C:\Program Files\MetaTrader 5\metatrader.exe"
) else (
    echo ❌ MT5 not found in standard locations
    echo Please find your MT5 installation manually
    echo Common names: terminal64.exe, metatrader.exe
    pause
    exit /b 1
)

echo ✅ Found MT5 at: %MT5_PATH%

:: Create startup folder if it doesn't exist
set "STARTUP_FOLDER=C:\Users\Administrator\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup"
if not exist "%STARTUP_FOLDER%" (
    mkdir "%STARTUP_FOLDER%"
)

:: Create shortcut to MT5 in startup folder
set "SHORTCUT_PATH=%STARTUP_FOLDER%\MT5_AutoStart.lnk"

:: Use PowerShell to create the shortcut
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%SHORTCUT_PATH%'); $Shortcut.TargetPath = '%MT5_PATH%'; $Shortcut.Save()"

if exist "%SHORTCUT_PATH%" (
    echo ✅ MT5 Auto-Start configured successfully!
    echo.
    echo 📋 Configuration:
    echo   - MT5 Path: %MT5_PATH%
    echo   - Shortcut: %SHORTCUT_PATH%
    echo.
    echo 🔄 MT5 will now start automatically when Administrator logs in
) else (
    echo ❌ Failed to create MT5 startup shortcut
)

echo.
pause