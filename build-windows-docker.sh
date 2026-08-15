#!/usr/bin/env bash
#
# Build PubMedSearch.exe without a Windows machine, by running Windows Python
# and PyInstaller under Wine inside a Linux container.
#
# Why this is needed: PyInstaller cannot cross-compile, and a Linux container
# builds Linux binaries. Wine is the only way to get a real Windows .exe out of
# a non-Windows host. Windows containers are not an option — they need a
# Windows kernel, so they cannot run on macOS or Linux at all.
#
# DOES NOT WORK ON APPLE SILICON. Tried on an M5 and Wine aborts during its own
# memory init, before reaching any of this project's code:
#
#   wine: dlls/ntdll/unix/virtual.c:267: anon_mmap_fixed:
#         Assertion `!((UINT_PTR)start & host_page_mask)' failed.
#   qemu: uncaught target signal 6 (Aborted)
#
# Rosetta does not save it: it cannot run 32-bit x86, which Wine's startup
# helpers need, so those fall back to QEMU — and Wine's ntdll reserves memory
# at fixed low addresses that QEMU's address space cannot satisfy. Nothing in
# this script or the image can be adjusted around that.
#
# Use it on an x86_64 Linux host, where there is no emulation in the way.
# Everywhere else use .github/workflows/build-windows.yml, which builds on a
# genuine Windows runner.
#
# Whatever this produces, test it on a real Windows machine before shipping it.
#
# Result: ./dist/PubMedSearch.exe

set -euo pipefail

IMAGE="tobix/pywine:3.14" # Wine + Windows Python + PyInstaller, preinstalled

cd "$(dirname "$0")"

docker run --rm \
	--platform linux/amd64 \
	--volume "$PWD":/src \
	--workdir /src \
	"$IMAGE" \
	sh -c '
        set -eu
        # Fails early if this image ships a Python built without tcl/tk,
        # rather than producing an exe that dies on launch.
        wine python -c "import tkinter; print(\"tkinter\", tkinter.TkVersion)"
        wine pip install --no-warn-script-location .
        wine pyinstaller --noconfirm PubMedSearch.spec
    '

ls -lh dist/PubMedSearch.exe
