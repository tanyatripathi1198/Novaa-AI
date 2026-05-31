# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

block_cipher = None
src = str(Path("src").resolve())

a = Analysis(
    [str(Path("src/main.py").resolve())],
    pathex=[src],
    binaries=[],
    datas=[],
    hiddenimports=[
        "customtkinter",
        "pystray._win32",
        "PIL",
        "PIL.Image",
        "PIL.ImageDraw",
        "sounddevice",
        "numpy",
        "ctranslate2",
        "faster_whisper",
        "keyboard",
        "winreg",
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="MurmurAI",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,         # no terminal window
    uac_admin=False,
)
