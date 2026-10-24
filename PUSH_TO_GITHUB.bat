@echo off
chcp 65001 > nul
echo.
echo ╔══════════════════════════════════════════════════════════╗
echo ║     Nova Launcher → GitHub → APK AUTO BUILDER           ║
echo ╚══════════════════════════════════════════════════════════╝
echo.
echo Bu script GitHub ga push qiladi va APK avtomatik quriladi.
echo.

:: Git sozlash
set REPO_DIR=c:\Users\%USERNAME%\Desktop\novalauncher
cd /d "%REPO_DIR%"

echo [1/4] Git repo tayorlanmoqda...
git init
git add .
git config user.email "nova@launcher.com"
git config user.name "Nova Builder"
git commit -m "Nova Launcher v2.5.0 - APK Build"

echo.
echo [2/4] GitHub repo yaratish...
echo.
echo ════════════════════════════════════════════════
echo  GitHub CLI o'rnatilmoqda...
echo ════════════════════════════════════════════════
winget install --id GitHub.cli -e --silent
if %errorLevel% neq 0 (
    echo [!] winget bilan o'rnatish muvaffaqiyatsiz.
    echo     Qo'lda yuklab oling: https://cli.github.com
    pause
    exit /b 1
)

echo.
echo [3/4] GitHub ga login...
echo.
echo GitHub ga kirish oynasi ochiladi...
gh auth login --web

echo.
echo [4/4] Repo yaratib push qilmoqda...
gh repo create nova-launcher-apk --public --source=. --remote=origin --push
if %errorLevel% neq 0 (
    echo Mavjud repo ga push qilinmoqda...
    git push -u origin main --force
)

echo.
echo ╔══════════════════════════════════════════════════════════╗
echo ║   ✓ PUSH MUVAFFAQIYATLI!                                 ║
echo ║   GitHub Actions APK ni quryapti (30-60 daqiqa)...      ║
echo ╚══════════════════════════════════════════════════════════╝
echo.
echo GitHub dagi Actions ni kuring:
gh repo view --web

pause
