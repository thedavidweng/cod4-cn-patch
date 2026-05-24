#!/bin/bash
cd "$(dirname "$0")" || exit 1

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
    echo ""
    echo "  macOS 安装方式:"
    echo "    1. 安装 Xcode Command Line Tools:"
    echo "       xcode-select --install"
    echo "    2. 或使用 Homebrew:"
    echo "       brew install python3"
    echo ""
    read -rp "  按 Enter 键退出..."
    exit 1
fi

clear
exec "$PYTHON" cod4_cn_patch.py
