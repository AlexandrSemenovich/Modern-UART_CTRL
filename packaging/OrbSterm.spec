# -*- mode: python ; coding: utf-8 -*-

"""PyInstaller spec for Modern UART Control (Windows & Linux friendly)."""

from __future__ import annotations

from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules


spec_dir = Path(SPECPATH).resolve()
project_root = spec_dir.parent
src_dir = project_root / "src"


def _add_data_dir(container: list[tuple[str, str]], rel_path: str, dest: str | None = None) -> None:
    """Add every file from ``rel_path`` into datas preserving folder hierarchy."""
    folder = project_root / rel_path
    if not folder.exists():
        return

    target_root = Path(dest or rel_path)
    for file in folder.rglob("*"):
        if file.is_file():
            relative = file.relative_to(folder)
            target = target_root / relative
            container.append((str(file), str(target).replace("\\", "/")))


datas: list[tuple[str, str]] = []


def _add_file(src: Path, dest_dir: Path) -> None:
    datas.append((str(src), str(dest_dir).replace("\\", "/")))


def _add_dir(base: Path, prefix: str) -> None:
    if not base.exists():
        return
    for file in base.rglob("*"):
        if file.is_file():
            rel = file.relative_to(base)
            target_dir = Path(prefix) / rel.parent
            print(f"Source: {file} -> target_dir: {target_dir}")  # отладка
            _add_file(file, target_dir)


_add_dir(project_root / "config", "config")
_add_dir(project_root / "assets", "assets")
_add_dir(project_root / "src" / "styles", "styles")
_add_dir(project_root / "src" / "translations", "translations")

hiddenimports = collect_submodules("src")

block_cipher = None


a = Analysis(
    [str(src_dir / "main.py")],
    pathex=[str(project_root), str(src_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

icon_path = project_root / "assets" / "icons" / "light" / "icon.ico"
exe_icon = str(icon_path) if icon_path.exists() else None

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="OrbSterm",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=exe_icon,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="OrbSterm",
)
