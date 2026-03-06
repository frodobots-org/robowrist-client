# PyInstaller spec：在项目根目录执行
# pyinstaller build.spec

# 各平台需在对应系统上分别执行；打包前请将 adb 放入 adb/windows 或 adb/macos 或 adb/linux

import sys
import os

block_cipher = None
root = os.path.abspath(SPECPATH)

# 单文件打包时 adb 解压到临时目录，无法作为 exe 旁目录使用；发布时请将 adb/<platform> 与 exe 放在同一目录
datas = []

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

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Robowrist-client',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 不显示控制台
)
