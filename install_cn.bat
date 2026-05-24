@echo off
chcp 65001 >nul 2>&1
title 使命召唤4：现代战争 中文补丁安装器

:: 切换到脚本所在目录
cd /d "%~dp0"

:: 检查 Python
where python >nul 2>&1
if errorlevel 1 (
    echo.
    echo    ============================================
    echo    错误: 未找到 Python 3
    echo    ============================================
    echo.
    echo    本工具需要 Python 3.6 或更高版本。
    echo    请从 https://www.python.org/downloads/ 下载安装。
    echo.
    echo    安装时请务必勾选 "Add Python to PATH"。
    echo.
    pause
    exit /b 1
)

echo.
echo    本安装器是基于2009年游侠汉化组原汉化补丁成果的现代化版本，
echo    所有汉化数据均直接复用自2009年原版发行包，未做任何修改。
echo.

:: 启动交互式安装器
python cod4_cn_patch.py

:: 如果出错则暂停显示
if errorlevel 1 (
    echo.
    echo 按任意键退出...
    pause >nul
)
