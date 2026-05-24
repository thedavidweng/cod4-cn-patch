#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
《使命召唤4：现代战争》中文补丁 —— 现代化跨平台安装器
Call of Duty 4: Modern Warfare — Chinese Localization Patch
Modern Cross-Platform Installer/Uninstaller

版本: 2.0.0-modern
声明：本安装器是基于2009年游侠汉化组原汉化补丁成果的现代化版本，
      所有汉化数据均直接复用自2009年原版发行包，未做任何修改。
      本安装器仅将原版的 decompressor/replace/compressor 私有 EXE
      工具链替换为跨平台的 Python zlib 标准库实现。

特性:
- 纯 Python 3 标准库，零外部依赖
- 跨平台支持: Windows / Linux / SteamOS / macOS
- 原子安装，失败自动回滚
- 一键 install / uninstall / status
- 无附带推广软件
"""

import argparse
import os
import sys
import zlib
import shutil
from pathlib import Path
from collections import defaultdict


class COD4CNPatch:
    VERSION = "2.0.0-modern"

    # ── 原汉化组人员名单（硬编码自 2009 年原版补丁说明）─────
    CREDITS = """\
原汉化组：游侠网 × 使命召唤中文站（2009）
──────────────────────────────────────────
总监  ：lijingxing（游侠汉化组）
技术  ：070（游侠汉化组兼使命召唤中文站）
         sunwayking（游侠汉化组）、falser
翻译  ：digmouse、kb1999、Panzerwillow、softboy（游侠汉化组）
测试  ：Happymars、Loper、speedypanda、arj1984、杜达耶夫、
         wblllqbnb3、viscap、237252994、momo、unlucky
         （使命召唤中文站测试组）
         digmouse、klarc（游侠汉化组）
鸣谢  ：中国主视角站（图标汉化包）
         aintnomeinteam（遗失CSV文件）
──────────────────────────────────────────
新版安装脚本：David
──────────────────────────────────────────
声明：本安装器是基于2009年游侠汉化组原汉化补丁成果的现代化版本，
      所有汉化数据均直接复用自2009年原版发行包，未做任何修改。"""

    # ── IWD 文件规则 ─────────────────────────────────
    IWD_ENG_PATTERN = "localized_english_iw"
    IWD_CN_PATTERN  = "localized_chinese_iw"

    # ── Zone .ff 文件规则 ────────────────────────────
    ZONE_SOURCE_DIRS = ["zone/english", "zone"]
    ZONE_TARGET_DIR  = "zone/chinese"
    ZONE_EXCLUDES    = ["code_post_gfx.ff", "localized_code_post_gfx_mp.ff"]

    def __init__(self, game_dir: Path, patch_dir: Path | None = None):
        self.game_dir = game_dir.resolve()
        if patch_dir:
            self.patch_dir = patch_dir.resolve()
        else:
            self.patch_dir = Path(__file__).parent.resolve()

        self.bak_dir = self.game_dir / ".cod4cn_bak"
        self._rollback_log = []

    # ── 终端输出工具 ─────────────────────────────────
    def _clear(self):
        """清屏"""
        if os.name == "nt":
            os.system("cls")
        else:
            sys.stdout.write("\033[2J\033[H")
            sys.stdout.flush()

    def _header(self):
        """打印顶部标题"""
        print("=" * 60)
        print("  《使命召唤4：现代战争》中文补丁安装器")
        print(f"  版本 {self.VERSION}")
        print("=" * 60)
        print()

    def _info(self, msg: str):
        print(f"  [>] {msg}")

    def _warn(self, msg: str):
        print(f"  [!] {msg}")

    def _err(self, msg: str):
        print(f"  [X] {msg}")

    def _ok(self, msg: str):
        print(f"  [OK] {msg}")

    def _progress(self, current: int, total: int, msg: str = ""):
        """单行进度条，覆盖当前行"""
        width = 30
        pct = current / total if total > 0 else 1
        filled = int(width * pct)
        bar = "#" * filled + "-" * (width - filled)
        line = f"\r  [{bar}] {pct*100:5.1f}% ({current}/{total}) {msg}"
        sys.stdout.write(line.ljust(70))
        sys.stdout.flush()
        if current >= total:
            print()

    def _pause(self, prompt: str = "按 Enter 键继续..."):
        """等待用户按键"""
        try:
            input(f"\n  {prompt}")
        except (EOFError, KeyboardInterrupt):
            pass

    # ── 人员名单显示 ─────────────────────────────────
    def _show_credits(self):
        """显示原汉化组人员名单和声明"""
        for line in self.CREDITS.splitlines():
            print(f"  {line}")
        print()

    # ── 启动画面格式检测 ─────────────────────────────
    def _detect_splash_format(self) -> str | None:
        """检测游戏启动画面文件的实际扩展名"""
        for ext in [".bmp", ".png", ".jpg", ".jpeg", ".tga", ".dds"]:
            if (self.game_dir / f"cod{ext}").exists():
                return ext
        return None

    # ── 启动画面替换询问 ─────────────────────────────
    def ask_replace_splash(self) -> tuple[bool, str | None]:
        """询问用户是否替换游戏启动画面，同时返回检测到的格式"""
        splash_ext = self._detect_splash_format()
        if not splash_ext:
            print("  未检测到游戏启动画面文件，跳过替换")
            return False, None

        print("  ──────────────────────────────────────────")
        print(f"  检测到游戏启动画面: cod{splash_ext}")
        print("  是否替换为中文版？")
        print("  [Y] 是 — 使用中文启动图（推荐）")
        print("  [N] 否 — 保留原版启动图")
        try:
            choice = input("\n  请选择 [Y/N] (默认 Y): ").strip().upper()
        except (EOFError, KeyboardInterrupt):
            return True, splash_ext
        return choice != "N", splash_ext

    # ── 游戏目录检测 ─────────────────────────────────
    def verify_game_dir(self) -> bool:
        exe_candidates = [
            "iw3sp.exe", "iw3mp.exe", "cod4.exe",
            "cod4sp.exe", "cod4mp.exe"
        ]
        has_exe = any((self.game_dir / f).exists() for f in exe_candidates)
        has_zone = (self.game_dir / "zone" / "english").exists()
        has_main = (self.game_dir / "main").exists()
        return has_exe or (has_zone and has_main)

    # ── Patch payload 扫描 ────────────────────────────
    def find_patch_payloads(self) -> dict:
        search_paths = [
            self.patch_dir / "patches" / "zone" / "chinese",
            self.patch_dir / "zone" / "chinese",
        ]

        patches = defaultdict(list)

        for sp in search_paths:
            if not sp.exists():
                continue
            for bin_file in sorted(sp.glob("*.bin")):
                stem = bin_file.stem
                if ".ff.dump." not in stem:
                    continue
                ff_name, _, offset_hex = stem.rpartition(".ff.dump.")
                if not ff_name or not offset_hex:
                    continue
                try:
                    offset = int(offset_hex, 16)
                except ValueError:
                    continue

                payload = bin_file.read_bytes()
                patches[f"{ff_name}.ff"].append((offset, payload))

        for ff_name in patches:
            patches[ff_name].sort(key=lambda x: x[0])
            self._check_overlap(ff_name, patches[ff_name])

        return dict(patches)

    def _check_overlap(self, ff_name: str, patch_list: list):
        for i in range(len(patch_list) - 1):
            off1, d1 = patch_list[i]
            off2, d2 = patch_list[i + 1]
            if off1 + len(d1) > off2:
                self._warn(
                    f"{ff_name} patch 重叠: "
                    f"0x{off1:X}+{len(d1)}b 与 0x{off2:X} 重叠"
                )

    # ── .ff 压缩/解压 ─────────────────────────────────
    # COD4 FastFile 格式: 12-byte header + zlib compressed payload
    # header: [4] "IWff" magic + [4] "u100" version + [4] uint32 version_number
    def decompress_ff(self, data: bytes) -> bytes:
        if len(data) < 12:
            raise RuntimeError(f".ff 文件只有 {len(data)} 字节，缺少 12-byte header")
        try:
            return zlib.decompress(data[12:])
        except zlib.error as e:
            raise RuntimeError(f".ff 解压失败 (请确认文件格式): {e}")

    def compress_ff(self, data: bytes, header: bytes) -> bytes:
        """压缩并恢复原始 12-byte header"""
        return header + zlib.compress(data)

    # ── 回滚系统 ─────────────────────────────────────
    def _backup(self, target: Path) -> Path | None:
        if not target.exists():
            return None
        rel = target.relative_to(self.game_dir)
        bak = self.bak_dir / rel
        bak.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target, bak)
        self._rollback_log.append(("restore", bak, target))
        return bak

    def _mark_delete(self, path: Path):
        self._rollback_log.append(("delete", path))

    def _mark_rename(self, src: Path, dst: Path):
        self._rollback_log.append(("rename", dst, src))

    def _rollback(self):
        self._warn("发生错误，正在回滚已执行的操作...")
        for action, *args in reversed(self._rollback_log):
            try:
                if action == "restore":
                    bak, orig = args
                    if bak.exists():
                        shutil.copy2(bak, orig)
                elif action == "rename":
                    dst, src = args
                    if dst.exists() and not src.exists():
                        dst.rename(src)
            except Exception as e:
                self._err(f"回滚步骤失败: {e}")
        self._warn("回滚完成。如果文件仍异常，请手动检查 .cod4cn_bak/ 备份。")

    # ═══════════════════════════════════════════════════
    #  INSTALL
    # ═══════════════════════════════════════════════════
    def install(self) -> bool:
        self._clear()
        self._header()

        # 1. 目录验证
        if not self.verify_game_dir():
            self._err("当前目录看起来不是 COD4 游戏根目录。")
            print("  请将此脚本放到 COD4 安装目录后运行。")
            print("  例如: C:\\Program Files (x86)\\Call of Duty 4\\")
            self._pause()
            return False

        # 2. 检查是否已安装
        if self.bak_dir.exists():
            self._warn("检测到 .cod4cn_bak/ 备份已存在，补丁可能已安装。")
            print("  如需重装，请先选择 [卸载还原]。")
            self._pause()
            return False

        # 3. 扫描补丁数据
        ff_patches = self.find_patch_payloads()
        if not ff_patches:
            self._err("未找到任何 .bin patch 数据文件。")
            print("  请确保 patches/zone/chinese/ 目录存在且包含 .bin 文件。")
            self._pause()
            return False

        total_ff = len(ff_patches)
        total_patches = sum(len(p) for p in ff_patches.values())
        print(f"  发现 {total_ff} 个 .ff 文件需要汉化，共 {total_patches} 处 patch")
        print()

        # 4. 询问是否替换启动画面（同时检测格式）
        replace_splash, splash_ext = self.ask_replace_splash()
        print()

        # 5. 创建备份目录
        try:
            self.bak_dir.mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            self._err("备份目录 .cod4cn_bak/ 已存在。")
            return False

        try:
            # ── Step 1: 基础文件 ───────────────────────
            print("[1/4] 替换基础文件...")
            self._step_basic_files(replace_splash=replace_splash, splash_ext=splash_ext)
            self._ok("完成")

            # ── Step 2: IWD 字体资源 ───────────────────
            print("\n[2/4] 安装中文字体资源...")
            self._step_iwd_files()
            self._ok("完成")

            # ── Step 3: 准备 .ff 源文件 ────────────────
            print(f"\n[3/4] 准备 {total_ff} 个游戏数据文件...")
            self._step_zone_prep(set(ff_patches.keys()))
            self._ok("完成")

            # ── Step 4: 应用 .ff patches ───────────────
            print(f"\n[4/4] 写入汉化补丁 (共 {total_ff} 个文件)...")
            self._step_ff_patches(ff_patches)
            self._ok("完成")

            print("\n" + "=" * 60)
            print("  [OK] 安装完成！游戏已切换为中文版。")
            print("=" * 60)
            if not replace_splash:
                print("  注意：已保留原版英文启动图（未替换）。")
            print("  还原命令: python3 cod4_cn_patch.py uninstall")
            print("=" * 60)
            self._pause("按 Enter 键退出...")
            return True

        except Exception as e:
            self._err(f"\n安装失败: {e}")
            self._rollback()
            try:
                if self.bak_dir.exists():
                    shutil.rmtree(self.bak_dir)
            except Exception:
                pass
            self._pause("按 Enter 键退出...")
            return False

    def _step_basic_files(self, replace_splash: bool = True, splash_ext: str | None = None):
        """替换基础文件：localization.txt（始终） + 启动图（根据检测到的格式）"""
        # 1. 替换 localization.txt（始终执行）
        target = self.game_dir / "localization.txt"
        source = self.patch_dir / "patches" / "localization.cn"
        if not source.exists():
            source = self.patch_dir / "localization.cn"

        if target.exists():
            self._backup(target)

        if source.exists():
            shutil.copy2(source, target)
            self._info("已替换: localization.txt")
        else:
            self._warn("源文件缺失，跳过: localization.cn")

        # 2. 替换启动图（根据用户选择和检测到的格式）
        if replace_splash and splash_ext:
            target_name = f"cod{splash_ext}"
            target = self.game_dir / target_name

            # 查找对应格式的源文件（优先 patches/ 目录）
            source = self.patch_dir / "patches" / f"cod1{splash_ext}"
            if not source.exists():
                source = self.patch_dir / f"cod1{splash_ext}"
            # 如果没有对应格式，回退到 bmp
            if not source.exists():
                source = self.patch_dir / "patches" / "cod1.bmp"
                if not source.exists():
                    source = self.patch_dir / "cod1.bmp"

            if target.exists():
                self._backup(target)

            if source.exists():
                shutil.copy2(source, target)
                self._info(f"已替换启动图: {target_name}")
            else:
                self._warn(f"未找到启动图源文件 cod1{splash_ext}，跳过替换")
        elif not replace_splash:
            self._info("保留原版启动图（用户选择不替换）")

    def _step_iwd_files(self):
        main_dir = self.game_dir / "main"
        if not main_dir.exists():
            self._warn("main/ 目录不存在，跳过 IWD 处理")
            return

        for old in main_dir.glob(f"{self.IWD_CN_PATTERN}*.iwd"):
            old.unlink()
            self._info(f"已删除旧文件: {old.name}")

        cn_iwd_source = self.patch_dir / "patches" / "main" / "localized_chinese_iw15.iwd"
        if not cn_iwd_source.exists():
            cn_iwd_source = self.patch_dir / "main" / "localized_chinese_iw15.iwd"

        if cn_iwd_source.exists():
            dst = main_dir / "localized_chinese_iw15.iwd"
            if dst.exists():
                self._backup(dst)
            shutil.copy2(cn_iwd_source, dst)
            self._info(f"已安装: {dst.name}")

            for eng in sorted(main_dir.glob(f"{self.IWD_ENG_PATTERN}*.iwd")):
                disabled = eng.with_suffix(eng.suffix + ".disabled")
                self._backup(eng)
                eng.rename(disabled)
                self._mark_rename(disabled, eng)
                self._info(f"已停用: {eng.name} -> {disabled.name}")
        else:
            for eng in sorted(main_dir.glob(f"{self.IWD_ENG_PATTERN}*.iwd")):
                new_name = self.IWD_CN_PATTERN + eng.name[len(self.IWD_ENG_PATTERN):]
                new_path = main_dir / new_name
                self._backup(eng)
                eng.rename(new_path)
                self._mark_rename(new_path, eng)
                self._info(f"已重命名: {eng.name} -> {new_name}")

    def _step_zone_prep(self, target_ff_names: set):
        chinese_dir = self.game_dir / self.ZONE_TARGET_DIR
        chinese_dir.mkdir(parents=True, exist_ok=True)

        copied = set()

        for src_rel in self.ZONE_SOURCE_DIRS:
            src_dir = self.game_dir / src_rel
            if not src_dir.exists():
                continue
            for ff in src_dir.glob("*.ff"):
                if ff.name in self.ZONE_EXCLUDES:
                    continue
                dst = chinese_dir / ff.name
                if dst.exists():
                    self._backup(dst)
                shutil.copy2(ff, dst)
                copied.add(ff.name)
                self._info(f"已复制: {src_rel}/{ff.name}")

        for ex_name in self.ZONE_EXCLUDES:
            ex_path = chinese_dir / ex_name
            if ex_path.exists():
                self._backup(ex_path)
                ex_path.unlink()
                self._mark_delete(ex_path)
                self._info(f"已删除排除项: {ex_name}")

        missing = [n for n in target_ff_names if n not in copied
                   and not (chinese_dir / n).exists()]
        if missing:
            raise RuntimeError(
                f"缺少必需的 .ff 源文件: {', '.join(missing)}"
            )

    def _step_ff_patches(self, ff_patches: dict):
        chinese_dir = self.game_dir / self.ZONE_TARGET_DIR
        total = len(ff_patches)
        current = 0

        for ff_name, plist in ff_patches.items():
            ff_path = chinese_dir / ff_name
            if not ff_path.exists():
                current += 1
                self._progress(current, total, f"跳过 {ff_name}")
                continue

            self._backup(ff_path)

            # 读取 + 保存 header + 解压
            compressed = ff_path.read_bytes()
            header = compressed[:12]                    # 保存原始 IWff header
            decompressed = self.decompress_ff(compressed)  # 内部跳过 12-byte header
            data = bytearray(decompressed)

            # 应用 patches
            for offset, payload in plist:
                end = offset + len(payload)
                if end > len(data):
                    raise ValueError(
                        f"{ff_name}: patch 0x{offset:X}(+{len(payload)}) "
                        f"超出 dump 大小 ({len(data)})"
                    )
                data[offset:end] = payload

            # 压缩 + 恢复 header + 写回
            new_compressed = self.compress_ff(bytes(data), header)
            ff_path.write_bytes(new_compressed)

            current += 1
            size_str = f"{len(compressed)/1024:.0f}KB -> {len(new_compressed)/1024:.0f}KB"
            self._progress(current, total, f"{ff_name:24s} {size_str}  ({len(plist)}p)")

    # ═══════════════════════════════════════════════════
    #  UNINSTALL
    # ═══════════════════════════════════════════════════
    def uninstall(self) -> bool:
        self._clear()
        self._header()

        if not self.bak_dir.exists():
            self._err("未找到 .cod4cn_bak/ 备份目录，无法卸载。")
            print("  如果已手动恢复过文件，可直接删除 .cod4cn_bak/ 目录。")
            self._pause()
            return False

        bak_count = sum(1 for _ in self.bak_dir.rglob("*") if _.is_file())
        print(f"  发现 {bak_count} 个备份文件，开始恢复...")
        print()

        print("[*] 从备份恢复原始文件...")
        restored = 0
        for bak_file in sorted(self.bak_dir.rglob("*")):
            if not bak_file.is_file():
                continue
            try:
                rel = bak_file.relative_to(self.bak_dir)
                target = self.game_dir / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(bak_file, target)
                restored += 1
                self._progress(restored, bak_count, f"恢复 {rel}")
            except Exception as e:
                self._warn(f"恢复失败 {bak_file.name}: {e}")

        print("\n[*] 清理汉化生成的文件...")
        self._cleanup()

        print("\n[*] 删除备份...")
        try:
            shutil.rmtree(self.bak_dir)
            self._ok("备份已清理")
        except Exception as e:
            self._warn(f"删除备份目录失败: {e}")

        print("\n" + "=" * 60)
        print("  [OK] 卸载完成！游戏已恢复为英文版。")
        print("=" * 60)
        self._pause("按 Enter 键退出...")
        return True

    def _cleanup(self):
        main_dir = self.game_dir / "main"
        chinese_dir = self.game_dir / self.ZONE_TARGET_DIR

        # 删除中文 IWD
        for cn_iwd in main_dir.glob(f"{self.IWD_CN_PATTERN}*.iwd"):
            try:
                cn_iwd.unlink()
                self._info(f"已删除: main/{cn_iwd.name}")
            except Exception as e:
                self._warn(f"删除失败 {cn_iwd.name}: {e}")

        # 恢复被禁用的英文 IWD
        for disabled in main_dir.glob(f"{self.IWD_ENG_PATTERN}*.iwd.disabled"):
            orig = disabled.with_suffix("")
            try:
                disabled.rename(orig)
                self._info(f"已恢复: {orig.name}")
            except Exception as e:
                self._warn(f"恢复失败 {disabled.name}: {e}")

        # 清理 zone/chinese/ 下的 .ff 文件
        if chinese_dir.exists():
            for ff in chinese_dir.glob("*.ff"):
                try:
                    ff.unlink()
                    self._info(f"已删除: zone/chinese/{ff.name}")
                except Exception as e:
                    self._warn(f"删除失败 {ff.name}: {e}")

        # 清理安装时创建、但无备份的残留启动图文件
        for ext in [".bmp", ".png", ".jpg", ".jpeg", ".tga", ".dds"]:
            splash = self.game_dir / f"cod{ext}"
            if splash.exists():
                rel = splash.relative_to(self.game_dir)
                bak = self.bak_dir / rel
                if not bak.exists():
                    try:
                        splash.unlink()
                        self._info(f"已删除残留启动图: cod{ext}")
                    except Exception as e:
                        self._warn(f"删除残留启动图失败 cod{ext}: {e}")

    # ═══════════════════════════════════════════════════
    #  STATUS
    # ═══════════════════════════════════════════════════
    def status(self) -> bool:
        self._clear()
        self._header()

        print(f"  游戏目录: {self.game_dir}")
        print(f"  补丁目录: {self.patch_dir}")
        print()

        if self.bak_dir.exists():
            bak_count = sum(1 for _ in self.bak_dir.rglob("*") if _.is_file())
            print(f"  状态: 已安装中文补丁")
            print(f"  备份文件: {bak_count} 个")
            print(f"  备份位置: {self.bak_dir}")
        else:
            print(f"  状态: 未安装（或已卸载）")

        ff_patches = self.find_patch_payloads()
        if ff_patches:
            total_patches = sum(len(p) for p in ff_patches.values())
            print(f"\n  补丁数据就绪: {len(ff_patches)} 个 .ff 文件, {total_patches} 处 patch")
        else:
            print("\n  未找到补丁数据文件")

        loc_cn = (self.game_dir / "localization.txt").exists()
        loc_bak = (self.game_dir / "localization.bak").exists()
        if loc_cn and loc_bak:
            print("  语言文件: 已替换为中文")
        elif loc_cn and not loc_bak:
            print("  语言文件: 未修改")
        else:
            print("  语言文件: 未知")

        print()
        print("=" * 60)
        self._pause()
        return True

    # ═══════════════════════════════════════════════════
    #  INTERACTIVE MODE
    # ═══════════════════════════════════════════════════
    def interactive(self):
        """交互式菜单模式（双击启动时进入）"""
        while True:
            self._clear()
            self._header()

            # 显示人员名单和声明
            self._show_credits()

            # 检测当前状态
            installed = self.bak_dir.exists()
            status_str = "[已安装]" if installed else "[未安装]"
            print(f"  当前状态: {status_str}")
            print()
            print("  [I] 安装中文补丁")
            print("  [U] 卸载还原英文版")
            print("  [S] 查看详细状态")
            print("  [Q] 退出")
            print()

            try:
                choice = input("  请选择 [I/U/S/Q]: ").strip().upper()
            except (EOFError, KeyboardInterrupt):
                print()
                break

            if choice == "I":
                self.install()
            elif choice == "U":
                self.uninstall()
            elif choice == "S":
                self.status()
            elif choice == "Q":
                break
            else:
                print("\n  无效选择，请重新输入。")
                self._pause()

        self._clear()
        print("  感谢使用，再见。")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="COD4:MW 中文补丁 — 现代化跨平台安装器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
运行方式:
  直接运行（无参数） -> 进入交互式菜单（推荐双击启动）
  install            -> 直接安装（默认替换启动图）
  uninstall          -> 直接卸载
  status             -> 查看状态

示例:
  python3 cod4_cn_patch.py
  python3 cod4_cn_patch.py install
  python3 cod4_cn_patch.py install --game-dir ~/Games/COD4
        """.strip()
    )
    parser.add_argument(
        "command",
        nargs="?",
        choices=["install", "uninstall", "status"],
        default=None,
        help="操作命令 (默认: 进入交互菜单)"
    )
    parser.add_argument(
        "--game-dir", "-g",
        type=Path,
        default=Path.cwd(),
        help="COD4 游戏根目录 (默认: 当前目录)"
    )
    parser.add_argument(
        "--patch-dir", "-p",
        type=Path,
        default=None,
        help="补丁资源目录 (默认: 脚本所在目录)"
    )

    args = parser.parse_args()
    patcher = COD4CNPatch(game_dir=args.game_dir, patch_dir=args.patch_dir)

    # ── 防呆：检查是否在正确的游戏目录 ───────────────
    if not patcher.verify_game_dir():
        print()
        print("=" * 60)
        print("  错误：当前目录似乎不是 COD4 游戏根目录")
        print("=" * 60)
        print()
        print(f"  当前位置: {patcher.game_dir}")
        print()
        print("  COD4 游戏根目录通常包含：")
        print("    - iw3sp.exe（或 iw3mp.exe）")
        print("    - main/ 文件夹")
        print("    - zone/ 文件夹")
        print()
        print("  请将补丁文件（.bat / .command / .sh、cod4_cn_patch.py")
        print("  和 patches/）移动到 COD4 游戏根目录后再运行。")
        print()
        print("=" * 60)
        input("  按 Enter 键退出...")
        sys.exit(1)

    if args.command is None:
        patcher.interactive()
    elif args.command == "install":
        ok = patcher.install()
        sys.exit(0 if ok else 1)
    elif args.command == "uninstall":
        ok = patcher.uninstall()
        sys.exit(0 if ok else 1)
    elif args.command == "status":
        ok = patcher.status()
        sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
