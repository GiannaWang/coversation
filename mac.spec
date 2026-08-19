# -*- mode: python ; coding: utf-8 -*-

import os


a = Analysis(
    [os.path.join(SPECPATH, "main.py")],
    pathex=[SPECPATH],
    binaries=[],
    datas=[
        (os.path.join(SPECPATH, "func_names.json"), "."),
        (os.path.join(SPECPATH, "functions"), "functions"),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="TextConverter",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="TextConverter",
)

app = BUNDLE(
    coll,
    name="TextConverter.app",
    icon=None,
    bundle_identifier="com.giannawang.textconverter",
    info_plist={
        "CFBundleDisplayName": "文本转换工具",
        "CFBundleName": "TextConverter",
        "CFBundleShortVersionString": "1.0.0",
        "NSHighResolutionCapable": True,
    },
)
