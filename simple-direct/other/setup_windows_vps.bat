@echo off
echo ==================================================
echo      🪟 Windows VPS Trading Bot Setup
echo ==================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.11+ from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo ✅ Python detected
python --version

REM Create directories
echo.
echo 📂 Creating project directories...
if not exist "C:\TradingBot" mkdir "C:\TradingBot"
if not exist "C:\TradingBot\logs" mkdir "C:\TradingBot\logs"
if not exist "C:\TradingBot\sessions" mkdir "C:\TradingBot\sessions"

REM Navigate to project directory
cd /d "C:\TradingBot"

REM Upgrade pip
echo.
echo 📦 Upgrading pip...
python -m pip install --upgrade pip

REM Install MetaTrader5 (Windows specific)
echo.
echo 🏦 Installing MetaTrader5 library...
pip install MetaTrader5

REM Install other dependencies
echo.
echo 📚 Installing Python dependencies...
pip install telethon requests python-dotenv

REM Check if .env exists
if not exist ".env" (
    echo.
    echo ⚙️ Creating .env configuration file...
    echo # Telegram API Configuration > .env
    echo TELEGRAM_API_ID=22159421 >> .env
    echo TELEGRAM_API_HASH=0a383c450ac02bbc327fd975f32387c4 >> .env
    echo TELEGRAM_PHONE=+32474071892 >> .env
    echo TELEGRAM_GROUP_ID=4867740501 >> .env
    echo SESSION_NAME=telegram_monitor >> .env
    echo. >> .env
    echo # MT5 Connection >> .env
    echo MT5_LOGIN=your_mt5_account_number >> .env
    echo MT5_PASSWORD=your_mt5_password >> .env
    echo MT5_SERVER=your_broker_server >> .env
    echo. >> .env
    echo # Trading Configuration >> .env
    echo DEFAULT_VOLUME=0.01 >> .env
    echo ENTRY_STRATEGY=adaptive >> .env
    echo MAGIC_NUMBER=123456 >> .env
    echo. >> .env
    echo # N8N Webhooks >> .env
    echo N8N_LOG_WEBHOOK=https://n8n.srv881084.hstgr.cloud/webhook/trading-logs >> .env
    echo N8N_TELEGRAM_FEEDBACK=https://n8n.srv881084.hstgr.cloud/webhook/91126b9d-bd23-4e92-8891-5bfb217455c7 >> .env
    
    echo ⚠️ Please edit .env file with your actual MT5 credentials!
)

REM Create MT5 test script
echo.
echo 🧪 Creating MT5 test script...
echo import MetaTrader5 as mt5 > test_mt5.py
echo import os >> test_mt5.py
echo from dotenv import load_dotenv >> test_mt5.py
echo. >> test_mt5.py
echo load_dotenv() >> test_mt5.py
echo. >> test_mt5.py
echo print("Testing MT5 connection...") >> test_mt5.py
echo. >> test_mt5.py
echo if not mt5.initialize(): >> test_mt5.py
echo     print("❌ MT5 initialize() failed") >> test_mt5.py
echo     print("Error:", mt5.last_error()) >> test_mt5.py
echo     print("Make sure MetaTrader 5 is installed and running") >> test_mt5.py
echo else: >> test_mt5.py
echo     print("✅ MT5 initialized successfully!") >> test_mt5.py
echo     >> test_mt5.py
echo     # Get account info >> test_mt5.py
echo     account_info = mt5.account_info() >> test_mt5.py
echo     if account_info: >> test_mt5.py
echo         print(f"Account: {account_info.login}") >> test_mt5.py
echo         print(f"Balance: ${account_info.balance}") >> test_mt5.py
echo         print(f"Server: {account_info.server}") >> test_mt5.py
echo     else: >> test_mt5.py
echo         print("⚠️ No account info - please login to MT5 terminal") >> test_mt5.py
echo     >> test_mt5.py
echo     # Test EURUSD symbol >> test_mt5.py
echo     symbol_info = mt5.symbol_info("EURUSD") >> test_mt5.py
echo     if symbol_info: >> test_mt5.py
echo         print(f"✅ EURUSD available: {symbol_info.name}") >> test_mt5.py
echo         tick = mt5.symbol_info_tick("EURUSD") >> test_mt5.py
echo         if tick: >> test_mt5.py
echo             print(f"Current EURUSD price: {tick.bid}/{tick.ask}") >> test_mt5.py
echo     else: >> test_mt5.py
echo         print("⚠️ EURUSD not available") >> test_mt5.py
echo     >> test_mt5.py
echo     mt5.shutdown() >> test_mt5.py

REM Create restart script
echo.
echo 🔄 Creating restart script...
echo @echo off > restart_bot.bat
echo echo Restarting Trading Bot... >> restart_bot.bat
echo taskkill /f /im python.exe 2^>nul >> restart_bot.bat
echo timeout /t 5 >> restart_bot.bat
echo cd /d "C:\TradingBot" >> restart_bot.bat
echo python direct_mt5_monitor.py >> restart_bot.bat

REM Create start script
echo @echo off > start_bot.bat
echo cd /d "C:\TradingBot" >> start_bot.bat
echo python direct_mt5_monitor.py >> start_bot.bat

echo.
echo ==================================================
echo      ✅ Setup Complete!
echo ==================================================
echo.
echo Next steps:
echo 1. Copy your direct_mt5_monitor.py file to C:\TradingBot\
echo 2. Copy your telegram_monitor.session file (if you have it)
echo 3. Edit .env file with your MT5 login credentials
echo 4. Make sure MetaTrader 5 is installed and logged in
echo 5. Run: python test_mt5.py (to test MT5 connection)
echo 6. Run: python direct_mt5_monitor.py (to start the bot)
echo.
echo Files created:
echo - C:\TradingBot\.env (edit with your credentials)
echo - C:\TradingBot\test_mt5.py (test MT5 connection)
echo - C:\TradingBot\restart_bot.bat (restart the bot)
echo - C:\TradingBot\start_bot.bat (start the bot)
echo.
echo Current directory: %cd%
echo.
pause