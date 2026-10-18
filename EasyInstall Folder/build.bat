
@echo off
setlocal
cd /d "%~dp0"

echo ====================================
echo       Building EasyInstall
echo ====================================

where python >nul 2>nul
if errorlevel 1 (
    echo Python was not found. Install Python 3 first.
    pause
    exit /b 1
)

python -m pip install -r requirements.txt
if errorlevel 1 (
    echo Failed to install build requirements.
    pause
    exit /b 1
)

python -m PyInstaller --noconfirm --clean --onefile --windowed --name EasyInstall main.py
if errorlevel 1 (
    echo Build failed.
    pause
    exit /b 1
)

echo.
echo Build complete!
echo Your executable is in the dist folder:
echo dist\EasyInstall.exe
pause
