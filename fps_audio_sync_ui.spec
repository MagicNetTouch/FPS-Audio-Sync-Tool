# -*- mode: python ; coding: utf-8 -*-
import os

APP_VERSION = "2.5"
APP_NAME = f"FPS Audio Sync Tool v{APP_VERSION}"
APP_ICON = os.path.join("assets", "app_icon.ico")


a = Analysis(
    ['fps_audio_sync_ui.py'],
    pathex=[],
    binaries=[],
    datas=[(APP_ICON, 'assets')],
    hiddenimports=['tkinterdnd2'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=APP_ICON,
)
