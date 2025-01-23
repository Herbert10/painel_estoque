# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

import os
import shutil
from PyInstaller.utils.hooks import collect_dynamic_libs

# Caminho para a instalação do VLC
vlc_path = r"C:\Program Files\VideoLAN\VLC"

# Copia as bibliotecas do VLC para a pasta do executável
if not os.path.exists("vlc_libs"):
    shutil.copytree(vlc_path, "vlc_libs")

a = Analysis(
    ['pedidosSP.py'],
    pathex=['.'],
    binaries=[],
    datas=[('vlc_libs/*', '.')],  # Inclui todas as bibliotecas do VLC
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='pedidosSP',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='pedidosSP'
)
