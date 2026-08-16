"""Remember recent searches, so they can be re-run without retyping them.

A search is stored as its keyword rows rather than as a finished query string:
picking one back out refills the form, ready to be tweaked and run again.
"""

import json
import os
import sys
from pathlib import Path

from pubmed_csv.query import DEFAULT_OPERATOR, OPERATORS, Operator, Term, build_query

MAX_ENTRIES = 20


def history_path() -> Path:
    """Where the history file lives, following each platform's convention."""
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA") or Path.home())
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    return base / "PubMedSearch" / "history.json"


def load_searches() -> list[list[Term]]:
    """Read the stored searches, newest first.

    A missing, unreadable or malformed file simply means no history: this is a
    convenience, and must never stop the app from starting.
    """
    try:
        raw = json.loads(history_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    if not isinstance(raw, list):
        return []

    searches = (_terms_from(item) for item in raw)
    return [terms for terms in searches if terms][:MAX_ENTRIES]


def save_searches(searches: list[list[Term]]) -> None:
    """Write the searches out, ignoring any failure to do so."""
    payload = [
        [{"keyword": term.keyword, "operator": term.operator} for term in terms]
        for terms in searches
    ]
    path = history_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=1), encoding="utf-8")
    except OSError:
        pass  # a lost history is not worth interrupting a search over


def remember(searches: list[list[Term]], terms: list[Term]) -> list[list[Term]]:
    """Return the history with this search at the front.

    Blank rows are dropped, and a search already in the list moves back up
    instead of being duplicated.
    """
    kept = [term for term in terms if term.keyword.strip()]
    if not kept:
        return searches

    query = build_query(kept)
    others = [terms for terms in searches if build_query(terms) != query]
    return [kept, *others][:MAX_ENTRIES]


def _terms_from(item: object) -> list[Term]:
    """Rebuild one stored search, or nothing if the entry is unusable."""
    if not isinstance(item, list):
        return []

    terms = []
    for stored in item:
        if not isinstance(stored, dict):
            return []
        keyword = stored.get("keyword")
        if not isinstance(keyword, str) or not keyword.strip():
            continue
        terms.append(Term(keyword=keyword, operator=_operator(stored.get("operator"))))
    return terms


def _operator(value: object) -> Operator:
    """Keep a stored operator only if it is still one we support."""
    return value if value in OPERATORS else DEFAULT_OPERATOR  # type: ignore[return-value]
