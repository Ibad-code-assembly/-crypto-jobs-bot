@echo off
cd /d "%~dp0"

echo [BOOT] Stopping any existing bot instances...
taskkill /F /IM python.exe /T >nul 2>&1
timeout /t 2 /nobreak >nul

echo [BOOT] Starting Crypto Jobs Bot in background...
start /min "CryptoJobsBot" python main_integrated.py >> bot_logs.txt 2>&1
echo [OK] Bot started. Logs: bot_logs.txt
exit /b
