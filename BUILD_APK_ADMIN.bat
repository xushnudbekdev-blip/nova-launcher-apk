@echo off
chcp 65001 > nul
echo.
echo ╔══════════════════════════════════════════════════════╗
echo ║       Nova Launcher APK Builder - Auto Setup         ║
echo ╚══════════════════════════════════════════════════════╝
echo.

:: Check admin
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [!] Administrator huquqi kerak!
    echo [*] O'ng klik → "Administrator sifatida ishga tushirish"
    pause
    exit /b 1
)

echo [1/5] WSL o'rnatilmoqda...
wsl --install -d Ubuntu --no-launch
if %errorLevel% neq 0 (
    echo [!] WSL allaqachon o'rnatilgan yoki xato.
)

echo.
echo [2/5] Ubuntu WSL tayyor bo'lgunicha kuting...
timeout /t 5 /nobreak > nul

echo.
echo [3/5] Fayllarni WSL ga nusxalash...
set SOURCE=%~dp0nova_mobile
set DEST=/mnt/c/Users/%USERNAME%/Desktop/novalauncher/nova_mobile

echo [4/5] Buildozer o'rnatish va APK qurish...
wsl -d Ubuntu -- bash -c "
cd /mnt/c/Users/%USERNAME%/Desktop/novalauncher/nova_mobile && \
sudo apt-get update -qq && \
sudo apt-get install -y -qq python3-pip git zip unzip openjdk-17-jdk \
    libffi-dev libssl-dev zlib1g-dev build-essential autoconf libtool pkg-config && \
pip3 install -q buildozer cython==0.29.33 && \
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 && \
export PATH=$JAVA_HOME/bin:$PATH && \
buildozer -v android debug 2>&1 | tee /tmp/build.log
"

echo.
echo [5/5] APK tekshirilmoqda...
if exist "nova_mobile\bin\*.apk" (
    echo.
    echo ╔══════════════════════════════════════╗
    echo ║   ✓ APK MUVAFFAQIYATLI QURILDI!      ║
    echo ║   nova_mobile\bin\ papkasiga qarang  ║
    echo ╚══════════════════════════════════════╝
    explorer nova_mobile\bin
) else (
    echo [!] APK topilmadi. Log: nova_mobile\build.log
)

pause
