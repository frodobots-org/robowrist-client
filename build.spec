# PyInstaller spec: run from project root
# pyinstaller build.spec
# Build on each OS separately; put adb in adb/windows, adb/macos, or adb/linux before packaging

import sys
import os

block_cipher = None
root = os.path.abspath(SPECPATH)

# Single-file build extracts to temp; ship adb/<platform> next to the exe for release
datas = [("assets/icon.png", "assets")]

a = Analysis(
    [os.path.join(root, 'src', 'main.py')],
    pathex=[root],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'ntplib',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'src.core.adb',
        'src.core.time_sync',
        'src.core.sdcard_fs',
    ],
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

icon_path = os.path.join(root, "assets", "icon.ico")
exe_kw = dict(
    name='Robowrist-client',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
)
if os.path.isfile(icon_path):
    exe_kw["icon"] = icon_path

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    **exe_kw,
)
