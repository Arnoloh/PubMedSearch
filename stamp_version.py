#!/usr/bin/env python3
"""Rewrite pubmed_csv/version.py to the version given on the command line.

The release workflow runs this before building, so a git tag is the single
source of truth: tagging v1.1.0 stamps __version__ = "1.1.0" into that build,
with nothing to remember to bump by hand.

    python stamp_version.py v1.1.0

Run from a checkout; it edits the working copy, not the repository.
"""

import re
import sys
from pathlib import Path

VERSION_FILE = Path(__file__).parent / "pubmed_csv" / "version.py"

# The line stamp_version rewrites. Kept anchored and exact so a stray
# __version__ mention elsewhere in the file cannot be hit by accident.
VERSION_LINE = re.compile(r'^__version__ = "[^"]*"$', re.MULTILINE)

# Tags look like v1.1.0; the leading v is optional and the rest must be numeric.
TAG = re.compile(r"^v?(?P<version>\d+(?:\.\d+)*)$")


def stamp(tag: str) -> str:
    """Write the version from `tag` into version.py, and return it."""
    match = TAG.match(tag.strip())
    if not match:
        raise SystemExit(f"not a numeric version tag: {tag!r} (expected e.g. v1.1.0)")
    version = match.group("version")

    text = VERSION_FILE.read_text(encoding="utf-8")
    stamped, replaced = VERSION_LINE.subn(f'__version__ = "{version}"', text)
    if replaced != 1:
        raise SystemExit(
            f"expected exactly one __version__ line in {VERSION_FILE}, found {replaced}"
        )

    VERSION_FILE.write_text(stamped, encoding="utf-8")
    return version


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: stamp_version.py <tag>")
    print(f'stamped __version__ = "{stamp(sys.argv[1])}"')
