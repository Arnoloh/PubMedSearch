import unittest

from pubmed_csv.query import Term, build_query


class BuildQueryTest(unittest.TestCase):
    def test_single_keyword_is_parenthesised(self):
        self.assertEqual(build_query([Term("CRISPR")]), "(CRISPR)")

    def test_two_keywords_need_no_nesting(self):
        terms = [Term("CRISPR"), Term("cancer", "AND")]
        self.assertEqual(build_query(terms), "(CRISPR) AND (cancer)")

    def test_each_condition_applies_to_the_whole_query_above_it(self):
        terms = [
            Term("CRISPR"),
            Term("cancer", "AND"),
            Term("mice", "NOT"),
            Term("gene editing", "OR"),
        ]
        self.assertEqual(
            build_query(terms),
            "(((CRISPR) AND (cancer)) NOT (mice)) OR (gene editing)",
        )

    def test_nesting_keeps_or_from_swallowing_the_earlier_terms(self):
        # Flat, PubMed would read this left to right as ((a AND b) OR c),
        # returning c on its own too. The nesting makes that grouping explicit.
        terms = [Term("a"), Term("b", "AND"), Term("c", "OR")]
        self.assertEqual(build_query(terms), "((a) AND (b)) OR (c)")

    def test_a_later_and_narrows_an_earlier_or(self):
        terms = [Term("cancer"), Term("tumour", "OR"), Term("2024", "AND")]
        self.assertEqual(build_query(terms), "((cancer) OR (tumour)) AND (2024)")

    def test_nesting_deepens_one_layer_per_condition(self):
        terms = [Term("a"), Term("b", "AND"), Term("c", "AND"), Term("d", "AND")]
        self.assertEqual(build_query(terms), "(((a) AND (b)) AND (c)) AND (d)")

    def test_first_operator_is_ignored(self):
        self.assertEqual(build_query([Term("CRISPR", "NOT")]), "(CRISPR)")

    def test_blank_keywords_are_skipped_without_leaving_empty_groups(self):
        terms = [Term("CRISPR"), Term("   ", "OR"), Term("cancer", "AND")]
        self.assertEqual(build_query(terms), "(CRISPR) AND (cancer)")

    def test_blank_row_in_the_middle_does_not_add_a_nesting_layer(self):
        terms = [Term("a"), Term("b", "AND"), Term("", "OR"), Term("c", "NOT")]
        self.assertEqual(build_query(terms), "((a) AND (b)) NOT (c)")

    def test_leading_blank_promotes_the_next_keyword(self):
        terms = [Term(""), Term("cancer", "NOT")]
        self.assertEqual(build_query(terms), "(cancer)")

    def test_all_blank_gives_empty_query(self):
        self.assertEqual(build_query([Term(""), Term("  ")]), "")

    def test_keywords_are_stripped(self):
        self.assertEqual(build_query([Term("  CRISPR  ")]), "(CRISPR)")

    def test_already_grouped_keyword_is_left_alone(self):
        self.assertEqual(build_query([Term("(cancer OR tumour)")]), "(cancer OR tumour)")

    def test_keyword_whose_parentheses_close_early_is_wrapped(self):
        self.assertEqual(build_query([Term("(a) AND (b)")]), "((a) AND (b))")

    def test_field_tags_are_preserved(self):
        self.assertEqual(build_query([Term("smith j[Author]")]), "(smith j[Author])")


if __name__ == "__main__":
    unittest.main()
