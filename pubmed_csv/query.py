"""Build PubMed boolean queries out of a list of keywords."""

from dataclasses import dataclass
from typing import Iterable, Literal

Operator = Literal["AND", "OR", "NOT"]

OPERATORS: tuple[Operator, ...] = ("AND", "OR", "NOT")
DEFAULT_OPERATOR: Operator = "AND"


@dataclass(frozen=True)
class Term:
    """A keyword and the operator joining it to the query built above it.

    The operator of the first non-empty term is ignored: PubMed operators are
    binary, so nothing precedes the first keyword.
    """

    keyword: str
    operator: Operator = DEFAULT_OPERATOR


def build_query(terms: Iterable[Term]) -> str:
    """Fold terms into a PubMed query, one condition at a time.

    Each term applies to everything above it rather than to its neighbour
    alone: the query so far is parenthesised, then the new operator and
    keyword are appended. Three terms therefore give
    ``((A) AND (B)) NOT (C)`` — the ``NOT`` excludes C from the whole
    ``A AND B`` result, which is what stacking conditions in the form
    should mean. Without the nesting, PubMed's plain left-to-right reading
    makes mixed AND/OR queries change meaning with the row order.

    Empty keywords are skipped, so partially filled forms still search.

    Returns:
        A PubMed query, or an empty string if every keyword was blank.
    """
    query = ""
    for term in terms:
        keyword = term.keyword.strip()
        if not keyword:
            continue
        if not query:
            query = _group(keyword)
        else:
            query = f"{_group(query)} {term.operator} {_group(keyword)}"
    return query


def _group(expression: str) -> str:
    """Parenthesise a keyword or sub-query, unless it already is one group.

    Skipping the redundant layer keeps the query the user reads in the preview
    as short as the nesting allows.
    """
    if _is_single_group(expression):
        return expression
    return f"({expression})"


def _is_single_group(expression: str) -> bool:
    """True when the whole expression sits inside one pair of parentheses.

    ``(cancer OR tumour)`` is one group, while ``(a) AND (b)`` is not: its
    outer parentheses close early, so it still needs wrapping.
    """
    if not expression.startswith("(") or not expression.endswith(")"):
        return False

    depth = 0
    for position, char in enumerate(expression):
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0 and position < len(expression) - 1:
                return False
    return depth == 0
