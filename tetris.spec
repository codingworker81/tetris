# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec — Tetris 단일 실행본(onefile, windowed) 빌드.

- assets/ (sfx, bgm, icon) 를 번들에 포함한다. 런타임에는 resources.asset_path()
  가 sys._MEIPASS 를 기준으로 이 파일들을 찾는다.
- 콘솔창 숨김(console=False) = windowed.
- 아이콘 적용(assets/icon.ico).

빌드:  pyinstaller tetris.spec   (프로젝트 루트에서)
산출:  dist/Tetris.exe
"""

import os

block_cipher = None

# assets 폴더 전체를 번들의 'assets/' 아래로 복사
datas = [
    ("assets/sfx", "assets/sfx"),
    ("assets/bgm", "assets/bgm"),
    ("assets/fonts", "assets/fonts"),
    ("assets/icon.ico", "assets"),
]

a = Analysis(
    ["src/main.py"],
    pathex=["src"],
    binaries=[],
    datas=datas,
    hiddenimports=[],
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
    name="Tetris",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,            # windowed: 콘솔창 숨김
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="assets/icon.ico",
)
