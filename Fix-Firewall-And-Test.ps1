# ============================================================================
# CRYPTO JOBS BOT - FIREWALL FIX AND TEST (PowerShell)
# ============================================================================
# Run this with: powershell -ExecutionPolicy Bypass -File Fix-Firewall-And-Test.ps1
# MUST be run as Administrator

# Check if running as admin
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")

if (-not $isAdmin) {
    Write-Host ""
    Write-Host "ERROR: This script must run as Administrator!" -ForegroundColor Red
    Write-Host ""
    Write-Host "HOW TO FIX:" -ForegroundColor Yellow
    Write-Host "1. Right-click PowerShell"
    Write-Host "2. Select 'Run as administrator'"
    Write-Host "3. Run: powershell -ExecutionPolicy Bypass -File Fix-Firewall-And-Test.ps1"
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "============================================================================" -ForegroundColor Green
Write-Host "CRYPTO JOBS BOT - FIREWALL FIX AND TEST" -ForegroundColor Green
Write-Host "============================================================================" -ForegroundColor Green
Write-Host ""

# Change to project directory
cd D:\crypto-jobs-bot

# ============================================================================
Write-Host "[STEP 1] REMOVING OLD FIREWALL RULES" -ForegroundColor Cyan
# ============================================================================
Write-Host ""

Remove-NetFirewallRule -DisplayName "Allow Telegram API" -ErrorAction SilentlyContinue
Remove-NetFirewallRule -DisplayName "Allow HTTPS Outbound" -ErrorAction SilentlyContinue
Remove-NetFirewallRule -DisplayName "Telegram" -ErrorAction SilentlyContinue

Write-Host "[OK] Old rules cleaned up" -ForegroundColor Green
Write-Host ""

# ============================================================================
Write-Host "[STEP 2] ADDING NEW FIREWALL RULE" -ForegroundColor Cyan
# ============================================================================
Write-Host ""

try {
    New-NetFirewallRule `
        -DisplayName "Allow Telegram API" `
        -Direction Outbound `
        -Action Allow `
        -Protocol TCP `
        -RemotePort 443 `
        -Enabled True `
        -Profile Any `
        -ErrorAction Stop

    Write-Host "[OK] Firewall rule added successfully!" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Failed to add rule: $_" -ForegroundColor Red
    Write-Host "Continuing with diagnostic test..." -ForegroundColor Yellow
}

Write-Host ""

# ============================================================================
Write-Host "[STEP 3] VERIFYING FIREWALL RULE" -ForegroundColor Cyan
# ============================================================================
Write-Host ""

$rule = Get-NetFirewallRule -DisplayName "Allow Telegram API" -ErrorAction SilentlyContinue
if ($rule) {
    Write-Host "[OK] Rule verification passed" -ForegroundColor Green
    Write-Host "Rule Details:" -ForegroundColor Cyan
    $rule | Format-List DisplayName, Enabled, Direction, Action
} else {
    Write-Host "[WARN] Rule not found" -ForegroundColor Yellow
}

Write-Host ""

# ============================================================================
Write-Host "[STEP 4] TESTING BOT CONNECTIVITY" -ForegroundColor Cyan
# ============================================================================
Write-Host ""

Write-Host "Running diagnostic test..." -ForegroundColor Yellow
python diagnostic_test.py
Write-Host ""

# ============================================================================
Write-Host "[STEP 5] OPTION: TEST WITH FIREWALL DISABLED" -ForegroundColor Cyan
# ============================================================================
Write-Host ""

$testDisabled = Read-Host "Do you want to test with firewall disabled to confirm? (y/n)"

if ($testDisabled -eq "y" -or $testDisabled -eq "Y") {
    Write-Host ""
    Write-Host "Disabling all firewall profiles..." -ForegroundColor Yellow

    Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled $false
    Write-Host "[OK] Firewall disabled" -ForegroundColor Green
    Write-Host ""

    Write-Host "Running diagnostic test with firewall disabled..." -ForegroundColor Yellow
    python diagnostic_test.py
    Write-Host ""

    Write-Host "Re-enabling firewall..." -ForegroundColor Yellow
    Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled $true
    Write-Host "[OK] Firewall re-enabled" -ForegroundColor Green
    Write-Host ""
}

# ============================================================================
Write-Host "[STEP 6] TESTING BOT" -ForegroundColor Cyan
# ============================================================================
Write-Host ""

$testBot = Read-Host "Do you want to start the bot for testing? (y/n)"

if ($testBot -eq "y" -or $testBot -eq "Y") {
    Write-Host ""
    Write-Host "Starting bot: python test_bot.py" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Send 'hi' in your Telegram group to test the bot." -ForegroundColor Cyan
    Write-Host "The bot should reply with 'hi'." -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Press Ctrl+C to stop the bot." -ForegroundColor Yellow
    Write-Host ""

    python test_bot.py
}

# ============================================================================
Write-Host ""
Write-Host "============================================================================" -ForegroundColor Green
Write-Host "FIREWALL FIX AND TEST COMPLETE" -ForegroundColor Green
Write-Host "============================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. If diagnostic shows [OK], firewall is fixed" -ForegroundColor White
Write-Host "2. Run: python main_integrated.py" -ForegroundColor White
Write-Host "3. Deploy using one of these options:" -ForegroundColor White
Write-Host "   - run_bot.bat (interactive)" -ForegroundColor White
Write-Host "   - Task Scheduler (auto-start)" -ForegroundColor White
Write-Host "   - Railway Cloud (cloud deployment)" -ForegroundColor White
Write-Host ""

Read-Host "Press Enter to exit"
