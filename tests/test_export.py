import csv
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from pypubmed import Article, PubMed, SearchResult

from pubmed_csv.export import (
    CSV_COLUMNS,
    FETCH_BATCH_SIZE,
    FETCH_CEILING,
    SearchOutcome,
    _FullTitlePubMed,
    run_search,
    write_csv,
)


def pubmed_xml(pmid: str, title_xml: str) -> str:
    """A PubmedArticle envelope trimmed to what the title parsing touches."""
    return f"""<PubmedArticleSet><PubmedArticle><MedlineCitation>
      <PMID>{pmid}</PMID>
      <Article><ArticleTitle>{title_xml}</ArticleTitle>
      <Journal><Title>J</Title></Journal></Article>
    </MedlineCitation></PubmedArticle></PubmedArticleSet>"""


def make_article(pmid="39344136", title="A title", doi="10.1000/xyz"):
    return Article(
        pmid=pmid,
        title=title,
        abstract="",
        authors=[],
        journal="",
        mesh_terms=[],
        keywords=[],
        doi=doi,
        publication_date=None,
        journal_date=None,
    )


class WriteCsvTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "results.csv"

    def read_rows(self):
        with self.path.open(encoding="utf-8-sig", newline="") as handle:
            return list(csv.reader(handle))

    def test_header_holds_the_four_requested_columns(self):
        write_csv([make_article()], self.path)
        self.assertEqual(self.read_rows()[0], CSV_COLUMNS)
        self.assertEqual(CSV_COLUMNS, ["title", "pmid", "doi", "url"])

    def test_row_holds_title_pmid_doi_and_link(self):
        write_csv([make_article()], self.path)
        self.assertEqual(
            self.read_rows()[1],
            [
                "A title",
                "39344136",
                "10.1000/xyz",
                "https://pubmed.ncbi.nlm.nih.gov/39344136/",
            ],
        )

    def test_missing_doi_becomes_an_empty_cell(self):
        write_csv([make_article(doi=None)], self.path)
        self.assertEqual(self.read_rows()[1][2], "")

    def test_file_starts_with_a_bom_for_excel(self):
        write_csv([make_article()], self.path)
        self.assertTrue(self.path.read_bytes().startswith(b"\xef\xbb\xbf"))

    def test_accents_and_commas_survive_a_round_trip(self):
        write_csv([make_article(title="Étude, phase II")], self.path)
        self.assertEqual(self.read_rows()[1][0], "Étude, phase II")

    def test_every_article_gets_a_row(self):
        articles = [make_article(pmid=str(index)) for index in range(100)]
        write_csv(articles, self.path)
        self.assertEqual(len(self.read_rows()), 101)  # header + 100 articles


class RunSearchTest(unittest.TestCase):
    """The limit, the batching and the cancel path, without touching PubMed."""

    def setUp(self):
        patcher = mock.patch("pubmed_csv.export._FullTitlePubMed")
        self.client = patcher.start().return_value
        self.addCleanup(patcher.stop)

    def given_matches(self, available, total=None):
        ids = [str(index) for index in range(available)]
        self.client.search.return_value = SearchResult(ids=ids, count=total or available)
        self.client.fetch.side_effect = lambda batch: [make_article(pmid=p) for p in batch]

    def requested_retmax(self):
        return self.client.search.call_args.kwargs["max_results"]

    def test_a_limit_is_passed_straight_through(self):
        self.given_matches(100, total=5000)
        outcome = run_search("cancer", max_results=100)
        self.assertEqual(self.requested_retmax(), 100)
        self.assertEqual(len(outcome.articles), 100)

    def test_no_limit_asks_for_everything_up_to_the_ceiling(self):
        self.given_matches(10, total=5_000_000)
        run_search("cancer", max_results=None)
        self.assertEqual(self.requested_retmax(), FETCH_CEILING)

    def test_a_limit_above_the_ceiling_is_clamped(self):
        self.given_matches(10)
        run_search("cancer", max_results=50_000)
        self.assertEqual(self.requested_retmax(), FETCH_CEILING)

    def test_ids_are_fetched_in_batches_of_two_hundred(self):
        self.given_matches(450)
        outcome = run_search("cancer", max_results=None)
        sizes = [len(call.args[0]) for call in self.client.fetch.call_args_list]
        self.assertEqual(sizes, [FETCH_BATCH_SIZE, FETCH_BATCH_SIZE, 50])
        self.assertEqual(len(outcome.articles), 450)

    def test_progress_reports_after_every_batch(self):
        self.given_matches(450)
        seen = []
        run_search("cancer", max_results=None, progress=lambda f, t: seen.append((f, t)))
        self.assertEqual(seen, [(200, 450), (400, 450), (450, 450)])

    def test_cancelling_stops_early_and_keeps_what_was_fetched(self):
        self.given_matches(1000)
        calls = {"n": 0}

        def cancel_after_two():
            calls["n"] += 1
            return calls["n"] > 2

        outcome = run_search("cancer", max_results=None, is_cancelled=cancel_after_two)
        self.assertTrue(outcome.cancelled)
        self.assertEqual(len(outcome.articles), 400)
        self.assertEqual(outcome.total_matches, 1000)

    def test_cancelling_before_the_first_batch_returns_nothing(self):
        self.given_matches(1000)
        outcome = run_search("cancer", max_results=None, is_cancelled=lambda: True)
        self.assertTrue(outcome.cancelled)
        self.assertEqual(outcome.articles, [])
        self.client.fetch.assert_not_called()

    def test_no_match_skips_the_fetch_entirely(self):
        self.client.search.return_value = SearchResult(ids=[], count=0)
        outcome = run_search("nonsense", max_results=None)
        self.assertEqual(outcome.articles, [])
        self.assertEqual(outcome.total_matches, 0)
        self.client.fetch.assert_not_called()


class FullTitleTest(unittest.TestCase):
    """Titles carrying inline markup must survive whole."""

    def parse(self, title_xml, pmid="1"):
        articles = _FullTitlePubMed()._parse_articles(pubmed_xml(pmid, title_xml))
        return articles[0].title

    def test_title_opening_with_italics_is_not_lost(self):
        # pypubmed alone returns "" here: findtext stops at the first child.
        self.assertEqual(
            self.parse("<i>NF2</i> loss transforms pancreatic cells."),
            "NF2 loss transforms pancreatic cells.",
        )

    def test_title_with_italics_in_the_middle_is_not_truncated(self):
        self.assertEqual(
            self.parse("Role of <i>TP53</i> in cancer"),
            "Role of TP53 in cancer",
        )

    def test_subscripts_are_flattened_without_inserting_spaces(self):
        self.assertEqual(self.parse("H<sub>2</sub>O uptake"), "H2O uptake")

    def test_plain_title_is_untouched(self):
        self.assertEqual(self.parse("A plain title"), "A plain title")

    def test_surrounding_whitespace_is_trimmed(self):
        self.assertEqual(self.parse("  padded title  "), "padded title")

    def test_the_private_hook_it_overrides_still_exists(self):
        # If pypubmed renames this, titles quietly go back to being truncated.
        self.assertTrue(hasattr(PubMed, "_parse_articles"))
        self.assertIn("_parse_articles", vars(_FullTitlePubMed))


class CappedByApiTest(unittest.TestCase):
    """Only PubMed's ceiling counts as capped, not the user's own limit."""

    def outcome(self, retrieved, total, cancelled=False):
        return SearchOutcome([make_article()] * retrieved, total, cancelled=cancelled)

    def test_hitting_the_ceiling_with_matches_left_is_capped(self):
        self.assertTrue(self.outcome(FETCH_CEILING, 5_000_000).capped_by_api)

    def test_a_small_user_limit_is_not_capped(self):
        self.assertFalse(self.outcome(100, 12_693).capped_by_api)

    def test_a_complete_result_set_is_not_capped(self):
        self.assertFalse(self.outcome(66, 66).capped_by_api)

    def test_a_cancelled_run_is_not_reported_as_capped(self):
        self.assertFalse(self.outcome(FETCH_CEILING, 5_000_000, cancelled=True).capped_by_api)


if __name__ == "__main__":
    unittest.main()
