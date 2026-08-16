"""The app's version, kept alone so packaging can read it without imports.

You do not need to bump this by hand. Tagging a release stamps the tag in
here at build time: `git tag v1.1.0` produces a build reporting "1.1.0",
because the release workflow runs stamp_version.py before building.

The value committed here is only what a local, untagged build reports.

Keep the line below in the form `__version__ = "<digits and dots>"` — that is
the exact shape stamp_version.py's regex rewrites.
"""

__version__ = "1.2.0"
