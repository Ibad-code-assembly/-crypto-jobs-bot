@echo off
REM This script adds a firewall rule to allow Telegram API access on port 443
REM Right-click and select "Run as administrator"

echo.
echo ================================================
echo Fixing Windows Firewall for Telegram Bot
echo ================================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script must be run as Administrator!
    echo.
    echo Please:
    echo 1. Right-click this file
    echo 2. Select "Run as administrator"
    echo 3. Click "Yes" when prompted
    pause
    exit /b 1
)

echo Adding firewall rule...
netsh advfirewall firewall add rule name="Allow Telegram API" dir=out action=allow protocol=tcp remoteport=443 enable=yes

if %errorLevel% equ 0 (
    echo.
    echo [OK] Firewall rule added successfully!
    echo.
    echo Verifying rule...
    netsh advfirewall firewall show rule name="Allow Telegram API"
    echo.
    echo ================================================
    echo SUCCESS! Your bot should now work.
    echo ================================================
    echo.
    echo Next steps:
    echo 1. Open Command Prompt or PowerShell
    echo 2. Navigate to: D:\crypto-jobs-bot
    echo 3. Run: python main_integrated.py
    echo 4. Send /start in your Telegram group
    echo.
) else (
    echo.
    echo [ERROR] Failed to add firewall rule!
    echo Please try again or contact support.
    echo.
)

pause
