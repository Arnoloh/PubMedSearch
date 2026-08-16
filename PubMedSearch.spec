# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build for the PubMed Search desktop app.

PyInstaller does not cross-compile: run this on the OS, and on the CPU
architecture, you are building for.

    pyinstaller PubMedSearch.spec

Windows gets dist/PubMedSearch.exe, Linux dist/PubMedSearch, and macOS both
dist/PubMedSearch and the dist/PubMedSearch.app bundle that Finder can launch.
"""

import sys

a = Analysis(
    ["pubmed_csv/__main__.py"],
    pathex=["."],  # so "import pubmed_csv" resolves from the project root
    binaries=[],
    datas=[],
    # pypubmed reaches ElementTree through the defusedxml package, which the
    # import scan does not always follow.
    hiddenimports=["defusedxml.ElementTree", "openpyxl"],
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

# Double-clicking a bare Unix executable on macOS opens a Terminal window, so
# the GUI needs a real .app bundle. Built for whichever architecture is running
# the build: an arm64 runner produces an Apple Silicon app.
if sys.platform == "darwin":
    app = BUNDLE(
        exe,
        name="PubMedSearch.app",
        icon=None,
        bundle_identifier="com.arnoloh.pubmedsearch",
        info_plist={
            "NSHighResolutionCapable": True,
            "LSApplicationCategoryType": "public.app-category.productivity",
        },
    )
