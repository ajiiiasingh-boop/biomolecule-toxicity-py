"""Checks the NumPy / Pandas analysis and that every picture can be drawn."""

import unittest

import numpy as np

from btd import analysis, drawing
from btd.data import CASE_BY_ID, CASES, CELL_MAP


class TestPatterns(unittest.TestCase):
    def test_percent_change(self):
        np.testing.assert_allclose(analysis.percent_change([100, 82, 55, 28]), [0, -18, -45, -72])

    def test_trend_words(self):
        self.assertEqual(analysis.describe_trend([100, 82, 55, 28])[0], "falls steadily")
        self.assertEqual(analysis.describe_trend([100, 118, 165, 240])[0], "rises steadily")
        self.assertEqual(analysis.describe_trend([100, 98, 101, 97])[0], "stays flat")
        self.assertEqual(analysis.describe_trend([100, 150, 90, 200])[0], "changes direction")

    def test_correlation_sign(self):
        self.assertLess(analysis.dose_correlation([100, 82, 55, 28]), -0.95)
        self.assertGreater(analysis.dose_correlation([100, 118, 165, 240]), 0.9)
        self.assertEqual(analysis.dose_correlation([5, 5, 5, 5]), 0.0)

    def test_case_one_pattern_report(self):
        report = analysis.pattern_report(CASE_BY_ID["case-01"]["datasets"][0])
        self.assertEqual(list(report["Change vs control (%)"]), [-72.0, 140.0])


class TestReplicates(unittest.TestCase):
    def test_replicate_means_equal_the_case_data_exactly(self):
        for case in CASES:
            for dataset in case["datasets"]:
                reps = analysis.simulate_replicates(dataset)
                means = analysis.dataset_frame(dataset).to_numpy(dtype=float)
                self.assertEqual(reps.shape, (*means.shape, 3))
                np.testing.assert_allclose(reps.mean(axis=2), means)

    def test_replicates_are_repeatable(self):
        dataset = CASES[1]["datasets"][0]
        np.testing.assert_array_equal(analysis.simulate_replicates(dataset),
                                      analysis.simulate_replicates(dataset))


class TestTables(unittest.TestCase):
    def test_toxin_filters(self):
        table = analysis.toxin_frame()
        self.assertEqual(len(table), 17)
        metals = analysis.filter_toxins(table, category_ids=["heavy-metals"])
        self.assertEqual(len(metals), 4)
        self.assertTrue((analysis.filter_toxins(table, target_ids=["lipid"])["target_id"] == "lipid").all())
        self.assertEqual(int(analysis.target_counts(table).sum()), 17)

    def test_empty_filter_result_still_counts_all_four_classes(self):
        table = analysis.toxin_frame()
        empty = analysis.filter_toxins(table, text="no such toxin")
        self.assertEqual(list(analysis.target_counts(empty)), [0, 0, 0, 0])


class TestDrawing(unittest.TestCase):
    def test_every_chart_and_route_draws(self):
        for case in CASES:
            for dataset in case["datasets"]:
                self.assertEqual(len(drawing.dose_chart(dataset).axes), 1)
        for route in CELL_MAP["routes"].values():
            drawing.cell_diagram(route=route["path"])
        dot = drawing.pathway_dot(["a", 'say "hi"'], "#000000")
        self.assertIn('\\"hi\\"', dot)


if __name__ == "__main__":
    unittest.main()
