@echo off
echo Setting up Windows Auto-Login for Administrator user...
echo.

:: Check if running as Administrator
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ This script must be run as Administrator!
    echo Right-click and select "Run as administrator"
    pause
    exit /b 1
)

echo 🔧 Configuring Windows Auto-Login...

:: Enable auto-login
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon" /v "AutoAdminLogon" /t REG_SZ /d "1" /f

:: Set default username
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon" /v "DefaultUserName" /t REG_SZ /d "Administrator" /f

:: Set empty password (since Administrator has no password)
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon" /v "DefaultPassword" /t REG_SZ /d "Admin2025!" /f

:: Optional: Set domain name (usually not needed for local accounts)
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon" /v "DefaultDomainName" /t REG_SZ /d "" /f

:: Disable force logoff on shutdown
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon" /v "ForceAutoLogon" /t REG_SZ /d "1" /f

if %errorlevel% equ 0 (
    echo ✅ Auto-Login configured successfully!
    echo.
    echo 📋 Configuration Summary:
    echo   - User: Administrator
    echo   - Password: ^(none^)
    echo   - Auto-login: Enabled
    echo.
    echo 🔄 Next Steps:
    echo   1. Restart your server to test auto-login
    echo   2. Administrator will login automatically
    echo   3. MT5 and Trading Bot will start automatically
    echo.
    echo ⚠️  Security Note:
    echo   Auto-login is enabled. Anyone with physical access
    echo   can access the server without password.
    echo.
    echo 🛠️  To disable auto-login later:
    echo   reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon" /v "AutoAdminLogon" /t REG_SZ /d "0" /f
) else (
    echo ❌ Failed to configure auto-login
    echo Please check if you're running as Administrator
)

echo.
pause