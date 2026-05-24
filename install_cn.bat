@echo off
chcp 65001 >nul 2>&1
title 使命召唤4：现代战争 中文补丁安装器

:: 切换到脚本所在目录
cd /d "%~dp0"

:: 优先检测 python，其次检测 py（Windows Python Launcher）
python --version >nul 2>&1
if not errorlevel 1 goto :run_python

py --version >nul 2>&1
if not errorlevel 1 goto :run_py

:: 都未找到
cls
echo.
echo    ============================================
echo    错误: 未找到 Python 3
echo    ============================================
echo.
echo    本工具需要 Python 3.6 或更高版本。
echo    请从 https://www.python.org/downloads/ 下载安装。
echo.
echo    安装时请务必勾选 "Add Python to PATH"
echo    或选择 "Use admin privileges when installing py.exe"
echo.
echo    如果已安装但仍提示此错误，请尝试在命令行运行：
echo        py cod4_cn_patch.py
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
    echo 按任意键退出...
    pause >nul
)
