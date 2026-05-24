#!/usr/bin/env bash
# 使命召唤4：现代战争 中文补丁安装器 — Linux / SteamOS / macOS 启动器
# 声明：本安装器是基于2009年游侠汉化组原汉化补丁成果的现代化版本，
#       所有汉化数据均直接复用自2009年原版发行包，未做任何修改。

cd "$(dirname "$0")" || exit 1

# 检测 Python
PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &> /dev/null; then
        PYTHON="$cmd"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    clear
    echo "============================================"
    echo "  错误: 未找到 Python 3"
    echo "============================================"
    echo ""
    echo "  本工具需要 Python 3.6 或更高版本。"
    echo "  大多数 Linux 发行版已预装，如未安装请用包管理器安装:"
    echo ""
    echo "    SteamOS / Arch:  sudo pacman -S python"
    echo "    Ubuntu / Debian: sudo apt install python3"
    echo "    Fedora:          sudo dnf install python3"
    echo ""
    read -rp "  按 Enter 键退出..."
    exit 1
fi

# 启动交互式安装器
clear
exec "$PYTHON" cod4_cn_patch.py
