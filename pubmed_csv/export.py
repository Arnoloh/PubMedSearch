"""Run PubMed searches and export the results to CSV."""

import csv
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import defusedxml.ElementTree as ElementTree
from pypubmed import Article, PubMed

# The columns asked for, in the order they should appear in the file.
CSV_COLUMNS = ["title", "pmid", "doi", "url"]

DEFAULT_MAX_RESULTS = 100

# PubMed hands back at most 9,999 ids per search whatever retmax asks for, so
# an unlimited search stops there rather than at the real number of matches.
FETCH_CEILING = 9_999

# PubMed accepts 200 ids per fetch. Batching by hand, rather than letting
# pypubmed chunk internally, is what makes progress and cancelling possible.
FETCH_BATCH_SIZE = 200


def _titles_by_pmid(xml_text: str) -> dict[str, str]:
    """Map each PMID to its title, with inline markup flattened to text."""
    root = ElementTree.fromstring(xml_text)
    titles = {}
    for element in root.findall(".//PubmedArticle"):
        pmid = element.findtext(".//PMID", default="")
        title_element = element.find(".//ArticleTitle")
        if pmid and title_element is not None:
            title = "".join(title_element.itertext()).strip()
            if title:
                titles[pmid] = title
    return titles


class _FullTitlePubMed(PubMed):
    """A PubMed client that keeps titles containing inline markup intact.

    pypubmed reads titles with ``findtext``, which returns only the text
    before the first child tag. A title like ``<i>NF2</i> loss transforms
    …`` then parses as empty, and ``Role of <i>TP53</i> in cancer`` loses
    everything from the italics on. Gene and species names are italicised
    all over PubMed, so this reads the titles again from the very same XML,
    keeping the text inside the markup. No extra requests.
    """

    def _parse_articles(self, xml_text: str) -> list[Article]:
        articles = super()._parse_articles(xml_text)
        titles = _titles_by_pmid(xml_text)
        for article in articles:
            full_title = titles.get(article.pmid)
            if full_title:
                article.title = full_title
        return articles


@dataclass
class SearchOutcome:
    """Articles retrieved, plus what happened while retrieving them."""

    articles: list[Article]
    total_matches: int
    cancelled: bool = False

    @property
    def capped_by_api(self) -> bool:
        """True when PubMed's ceiling, not the user's limit, cut the results.

        Landing exactly on the ceiling with matches left over is what that
        looks like; a smaller user limit stops well short of it.
        """
        return (
            not self.cancelled
            and len(self.articles) >= FETCH_CEILING
            and self.total_matches > len(self.articles)
        )


def run_search(
    query: str,
    max_results: int | None = DEFAULT_MAX_RESULTS,
    progress: Callable[[int, int], None] | None = None,
    is_cancelled: Callable[[], bool] | None = None,
) -> SearchOutcome:
    """Search PubMed and fetch the details of the matching articles.

    Args:
        query: A PubMed query, typically from ``query.build_query``.
        max_results: How many articles to retrieve, or ``None`` for every
            match PubMed will return (up to ``FETCH_CEILING``).
        progress: Called as ``progress(fetched, total)`` after each batch.
        is_cancelled: Polled between batches; return True to stop early and
            keep whatever has been fetched so far.

    Returns:
        The articles, the total number of matches PubMed reported, and whether
        the run was cancelled part way.
    """
    client = _FullTitlePubMed()
    wanted = FETCH_CEILING if max_results is None else min(max_results, FETCH_CEILING)

    result = client.search(query, max_results=wanted)
    if not result.ids:
        return SearchOutcome(articles=[], total_matches=result.count)

    articles: list[Article] = []
    total = len(result.ids)
    for start in range(0, total, FETCH_BATCH_SIZE):
        if is_cancelled is not None and is_cancelled():
            return SearchOutcome(
                articles=articles, total_matches=result.count, cancelled=True
            )
        articles.extend(client.fetch(result.ids[start : start + FETCH_BATCH_SIZE]))
        if progress is not None:
            progress(len(articles), total)

    return SearchOutcome(articles=articles, total_matches=result.count)


def write_csv(articles: list[Article], path: str | Path) -> None:
    """Write the articles to a CSV file with title, pmid, doi and url.

    The file carries a UTF-8 BOM so Excel opens accented titles correctly.
    """
    with Path(path).open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle, dialect="excel")
        writer.writerow(CSV_COLUMNS)
        for article in articles:
            writer.writerow([article.title, article.pmid, article.doi or "", article.url])
