"""Checks the real-data analysis: Tox21 counts and the LD50 comparison."""

import unittest

import numpy as np

from btd import realdata as rd


class TestTox21Counts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tox = rd.add_labels(rd.load_tox21())

    def test_size_and_assays(self):
        self.assertEqual(len(self.tox), 7831)
        for assay in rd.ASSAY_IDS:
            self.assertIn(assay, self.tox.columns)

    def test_toxic_plus_non_toxic_is_everything(self):
        counts = rd.label_counts(self.tox)
        self.assertEqual(counts["toxic"] + counts["non_toxic"], counts["total"])
        self.assertEqual(counts["toxic"], 2872)
        self.assertLess(counts["non_toxic_fully_tested"], counts["non_toxic"])

    def test_assay_table_adds_up(self):
        table = rd.assay_table(self.tox)
        totals = table["Active (toxic)"] + table["Inactive"] + table["Not tested"]
        self.assertTrue((totals == 7831).all())


class TestLD50Comparison(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = rd.load_merged()

    def test_matched_table(self):
        self.assertGreater(len(self.data), 3000)
        self.assertTrue(set(self.data["toxic"].unique()) <= {0, 1})
        self.assertFalse(self.data["neglog_ld50"].isna().any())

    def test_toxic_group_is_more_toxic(self):
        result = rd.compare(self.data, n_permutations=2000)
        self.assertGreater(result["difference"], 0)          # higher -log(LD50) = more toxic
        self.assertLess(result["p_value"], 0.01)
        self.assertGreater(result["fold"], 1)
        self.assertTrue(rd.conclusion(result).startswith("Yes."))

    def test_permutation_test_on_identical_groups(self):
        values = np.arange(100, dtype=float)
        diff, p = rd.permutation_test(values[::2], values[1::2], n=2000)
        self.assertLess(abs(diff), 1.5)
        self.assertGreater(p, 0.2)

    def test_cohens_d(self):
        self.assertAlmostEqual(rd.cohens_d(np.array([2.0, 4.0]), np.array([0.0, 2.0])), 2 / np.sqrt(2))

    def test_ghs_table_counts_every_compound(self):
        self.assertEqual(int(rd.ghs_table(self.data).to_numpy().sum()), len(self.data))


if __name__ == "__main__":
    unittest.main()
