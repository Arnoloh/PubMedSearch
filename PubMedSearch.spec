# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build for the PubMed Search desktop app.

PyInstaller does not cross-compile: run this on the OS you are building for.

    pyinstaller PubMedSearch.spec

Windows gets dist/PubMedSearch.exe, macOS and Linux dist/PubMedSearch.
"""

a = Analysis(
    ["pubmed_csv/__main__.py"],
    pathex=["."],  # so "import pubmed_csv" resolves from the project root
    binaries=[],
    datas=[],
    # pypubmed reaches ElementTree through the defusedxml package, which the
    # import scan does not always follow.
    hiddenimports=["defusedxml.ElementTree"],
    hookspath=[],
    runtime_hooks=[],
    excludes=["unittest"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="PubMedSearch",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # UPX-packed exes trip antivirus scanners more often
    runtime_tmpdir=None,
    console=False,  # a GUI app: no console window behind the window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon="icon.ico",  # uncomment once you have one
)
