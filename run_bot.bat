@echo off
title Crypto Jobs Bot
cd /d "%~dp0"

echo [BOOT] Stopping any existing bot instances...
taskkill /F /IM python.exe /T >nul 2>&1
timeout /t 2 /nobreak >nul

echo [BOOT] Starting Crypto Jobs Bot...
echo.
python main_integrated.py
pause
