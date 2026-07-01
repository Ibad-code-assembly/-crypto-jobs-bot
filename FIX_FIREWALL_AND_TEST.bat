@echo off
REM ============================================================================
REM CRYPTO JOBS BOT - COMPLETE FIREWALL FIX AND TEST
REM ============================================================================
REM This script fixes firewall, tests connectivity, and deploys the bot
REM Must be run as Administrator

cls
echo.
echo ============================================================================
echo CRYPTO JOBS BOT - FIREWALL FIX AND DEPLOYMENT
echo ============================================================================
echo.

REM Check if running as admin
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo.
    echo ERROR: This script MUST run as Administrator!
    echo.
    echo HOW TO FIX:
    echo 1. Right-click this file (FIX_FIREWALL_AND_TEST.bat)
    echo 2. Select "Run as administrator"
    echo 3. Click "Yes" when prompted
    echo.
    pause
    exit /b 1
)

echo [ADMIN] Running with Administrator privileges
echo.

REM Change to project directory
cd /d D:\crypto-jobs-bot

REM ============================================================================
echo [STEP 1] REMOVING OLD FIREWALL RULES
REM ============================================================================
echo.
netsh advfirewall firewall delete rule name="Allow Telegram API" dir=out >nul 2>&1
netsh advfirewall firewall delete rule name="Allow HTTPS Outbound" dir=out >nul 2>&1
netsh advfirewall firewall delete rule name="Telegram" dir=out >nul 2>&1
echo [OK] Old rules cleaned up
echo.

REM ============================================================================
echo [STEP 2] ADDING NEW FIREWALL RULE
REM ============================================================================
echo.
echo Adding rule: Allow Telegram API on port 443...
netsh advfirewall firewall add rule ^
    name="Allow Telegram API" ^
    dir=out ^
    action=allow ^
    protocol=tcp ^
    remoteport=443 ^
    enable=yes ^
    profile=any

if %errorLevel% equ 0 (
    echo [OK] Firewall rule added successfully!
) else (
    echo [ERROR] Failed to add rule, but continuing...
)
echo.

REM ============================================================================
echo [STEP 3] VERIFYING FIREWALL RULE
REM ============================================================================
echo.
netsh advfirewall firewall show rule name="Allow Telegram API" | find "Rule Name"
if %errorLevel% equ 0 (
    echo [OK] Rule verification passed
) else (
    echo [WARN] Could not verify rule
)
echo.

REM ============================================================================
echo [STEP 4] TESTING BOT CONNECTIVITY
REM ============================================================================
echo.
echo Running diagnostic test...
python diagnostic_test.py
echo.

REM ============================================================================
echo [STEP 5] OPTION: TEST WITH FIREWALL DISABLED
REM ============================================================================
echo.
set /p test_disabled="Do you want to test with firewall disabled to confirm? (y/n): "

if /i "%test_disabled%"=="y" (
    echo.
    echo Disabling all firewall profiles...
    netsh advfirewall set allprofiles state off
    echo [OK] Firewall disabled
    echo.

    echo Running diagnostic test with firewall disabled...
    python diagnostic_test.py
    echo.

    echo Re-enabling firewall...
    netsh advfirewall set allprofiles state on
    echo [OK] Firewall re-enabled
    echo.
)

REM ============================================================================
echo [STEP 6] TESTING BOT
REM ============================================================================
echo.
set /p test_bot="Do you want to start the bot for testing? (y/n): "

if /i "%test_bot%"=="y" (
    echo.
    echo Starting bot: python test_bot.py
    echo.
    echo Send 'hi' in your Telegram group to test the bot.
    echo The bot should reply with 'hi'.
    echo.
    echo Press Ctrl+C to stop the bot.
    echo.
    python test_bot.py
)

REM ============================================================================
echo [COMPLETE] FIREWALL FIX AND TEST COMPLETE
REM ============================================================================
echo.
echo Next steps:
echo 1. If diagnostic shows [OK], firewall is fixed
echo 2. If diagnostic shows [FAIL], run:
echo    python main_integrated.py
echo 3. Deploy using:
echo    - run_bot.bat (interactive)
echo    - Task Scheduler (auto-start)
echo    - Railway Cloud (cloud deployment)
echo.
pause
