@echo off
REM Crypto Jobs Bot - Firewall Fix Script
REM This script must be run as Administrator

echo.
echo ======================================================================
echo CRYPTO JOBS BOT - FIREWALL FIX
echo ======================================================================
echo.

REM Check if running as admin
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script must run as Administrator!
    echo.
    echo Please:
    echo 1. Right-click this file
    echo 2. Select "Run as administrator"
    echo 3. Click "Yes"
    echo.
    pause
    exit /b 1
)

echo [STEP 1] Adding Firewall Rule...
netsh advfirewall firewall add rule name="Allow Telegram API" dir=out action=allow protocol=tcp remoteport=443 enable=yes
if %errorLevel% equ 0 (
    echo [OK] Rule added successfully
) else (
    echo [WARN] Rule addition had issues, continuing...
)

echo.
echo [STEP 2] Verifying Firewall Rule...
netsh advfirewall firewall show rule name="Allow Telegram API"

echo.
echo [STEP 3] Testing Bot Connectivity...
cd /d D:\crypto-jobs-bot
python diagnostic_test.py

echo.
echo [STEP 4] If test still shows [FAIL], disabling firewall for testing...
echo.

setlocal enabledelayedexpansion
set /p continue="Disable firewall to test? (y/n): "

if /i "%continue%"=="y" (
    echo Disabling firewall...
    netsh advfirewall set allprofiles state off

    echo.
    echo Running diagnostic test with firewall disabled...
    python diagnostic_test.py

    echo.
    echo Re-enabling firewall...
    netsh advfirewall set allprofiles state on
    echo [OK] Firewall re-enabled
)

echo.
echo ======================================================================
echo DONE
echo ======================================================================
echo.
pause
