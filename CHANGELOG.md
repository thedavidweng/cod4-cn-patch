# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]


### ✨ New Features

- Platform-specific launcher filenames for idiot-proof UX
- Idiot-proof guard — refuse to run outside COD4 game directory

### 🐛 Bug Fixes

- UTF-8 BOM + dual Python detection (python/py) for Windows
- Make install_cn.bat pure ASCII + CRLF to eliminate Windows encoding issues
- Copy all .ff to zone/chinese/; verify_game_dir checks data files not exe names
- Handle stale .disabled files left by partial uninstall on Windows
- Uninstall now properly removes stale .disabled files when .iwd already exists
- Repack localized_chinese_iw15.iwd with STORE compression for COD4 engine compatibility

### 📝 Documentation

- Add GitHub Download ZIP instructions to README
- Simplify comparison table, remove inaccurate claims
- Link David GitHub profile, remove dead codchina.net link

### 🔧 Chores

- Add gitignore, preview image, and fix Couldn't load image error on Win11

