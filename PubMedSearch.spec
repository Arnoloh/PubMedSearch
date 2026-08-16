# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller recipe for PubMedSearch.exe.

Built by .github/workflows/build-windows.yml with `pyinstaller PubMedSearch.spec`.
PyInstaller cannot cross-compile, so this only ever produces a Windows .exe on
a Windows runner — running it on macOS or Linux builds the same app for that
platform instead, which is handy for checking the recipe still holds together.

Everything lands in a single file: the release is one download the user runs,
with no folder to keep next to it and nothing to install.
"""

# Analysis, PYZ, EXE and SPECPATH are not imported: PyInstaller injects them
# when it executes this file. That is why a spec reads like a script with
# undefined names, and why it only ever runs under `pyinstaller`.

# Where `import pubmed_csv` is resolved from. The repo checkout comes first so
# the build packages the working tree — the one stamp_version.py has just
# written the tag into — rather than a copy installed earlier in the job.
PROJECT_ROOT = SPECPATH

a = Analysis(
    # The package's own entry point, so the frozen app starts exactly the way
    # `python -m pubmed_csv` does and there is no second copy of that wiring.
    ["pubmed_csv/__main__.py"],
    pathex=[PROJECT_ROOT],
    binaries=[],
    datas=[],
    # openpyxl is imported inside write_xlsx rather than at the top of
    # export.py, to keep it off the startup path. Naming it here means the
    # export still works if PyInstaller ever stops following imports that sit
    # inside a function body.
    hiddenimports=["openpyxl"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # Nothing here is imported by the app; they are large, and PyInstaller
    # pulls them in through optional imports in the standard library if left
    # to its own devices.
    excludes=["numpy", "pandas", "matplotlib", "PIL", "pytest", "setuptools"],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    # Binaries and data inside the EXE itself is what makes this a one-file
    # build; handing them to a COLLECT instead would produce a folder.
    a.binaries,
    a.datas,
    [],
    name="PubMedSearch",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    # Left off deliberately. UPX shaves a few MB, but packed executables are a
    # standard heuristic for antivirus engines, and an app people download from
    # a GitHub release can do without the extra warning.
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    # A desktop app: no console window should flash up behind the Tk window.
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
