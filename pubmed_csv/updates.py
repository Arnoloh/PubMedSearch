"""Check GitHub for a newer release of the app.

This is a courtesy check, not a critical path: no network, a private repo, a
rate limit or a surprise from the API all mean "no update to offer", never an
error in the user's face.
"""

import re
from dataclasses import dataclass

import requests

GITHUB_OWNER = "Arnoloh"
GITHUB_REPO = "PubMedSearch"

LATEST_RELEASE_URL = (
    f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
)
RELEASES_PAGE_URL = f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"

TIMEOUT = (3, 5)  # (connect, read) seconds: a slow check must not delay startup


@dataclass(frozen=True)
class Release:
    """A published release that is newer than what is running."""

    version: str
    url: str


def check_for_update(current_version: str) -> Release | None:
    """Return the latest release if it is newer than the running version.

    Returns None whenever the answer is not a clear yes — offline, private
    repo, no releases yet, unparseable tag, or anything else unexpected.
    """
    try:
        response = requests.get(
            LATEST_RELEASE_URL,
            headers={"Accept": "application/vnd.github+json"},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
    except Exception:  # network, HTTP and decoding failures alike
        return None

    if not isinstance(data, dict) or data.get("draft") or data.get("prerelease"):
        return None

    tag = data.get("tag_name")
    if not isinstance(tag, str) or not is_newer(tag, current_version):
        return None

    url = data.get("html_url")
    return Release(
        version=tag.lstrip("vV"),
        url=url if isinstance(url, str) and url else RELEASES_PAGE_URL,
    )


def is_newer(candidate: str, current: str) -> bool:
    """True when `candidate` is a later version than `current`.

    Both are compared as dotted numbers, ignoring a leading "v" and anything
    from the first non-numeric part onwards, so "v1.2.0" beats "1.10" only
    where the numbers say so — 1.10 is later than 1.2.
    """
    candidate_parts = _numbers(candidate)
    current_parts = _numbers(current)
    if not candidate_parts or not current_parts:
        return False

    length = max(len(candidate_parts), len(current_parts))
    return _padded(candidate_parts, length) > _padded(current_parts, length)


def _numbers(version: str) -> tuple[int, ...]:
    """The leading dotted numbers of a version string, as integers."""
    numbers = []
    for part in re.split(r"[.\-+_]", version.strip().lstrip("vV")):
        if not part.isdigit():
            break  # stop at "rc1", "beta" and friends
        numbers.append(int(part))
    return tuple(numbers)


def _padded(numbers: tuple[int, ...], length: int) -> tuple[int, ...]:
    """Pad with zeros so 1.2 and 1.2.0 compare as equal."""
    return numbers + (0,) * (length - len(numbers))
