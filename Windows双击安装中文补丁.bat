@echo off
chcp 65001 >nul 2>&1
title COD4 MW - Chinese Patch Installer

cd /d "%~dp0"

python --version >nul 2>&1
if not errorlevel 1 goto :run_python

py --version >nul 2>&1
if not errorlevel 1 goto :run_py

cls
echo.
echo     ============================================
echo     ERROR: Python 3 not found
echo     ============================================
echo.
echo     This tool requires Python 3.6 or later.
echo     Download: https://www.python.org/downloads/
echo.
echo     Make sure to check "Add Python to PATH"
echo     or select "Use admin privileges when installing py.exe"
echo.
echo     If already installed but still not found, try:
echo         py cod4_cn_patch.py
echo.
pause
exit /b 1

:run_python
python cod4_cn_patch.py
goto :check_error

:run_py
py cod4_cn_patch.py
goto :check_error

:check_error
if errorlevel 1 (
    echo.
    echo Press any key to exit...
    pause >nul
)
