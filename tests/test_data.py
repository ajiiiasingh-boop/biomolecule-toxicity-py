"""Checks that the biology data is complete and consistent.

Run all tests with:   python -m unittest
"""

import unittest

from btd.data import (BIOMOLECULE_BY_ID, CASES, CELL_MAP, CELL_PART_BY_ID, MECHANISM_BY_ID,
                      MECHANISMS, QUIZ, TOXIN_CATEGORIES, answer_mechanisms, evidence_datasets,
                      toxin_entry_count)


class TestCases(unittest.TestCase):
    def test_six_cases_with_unique_ids(self):
        self.assertEqual(len(CASES), 6)
        self.assertEqual(len({c["id"] for c in CASES}), 6)

    def test_every_case_has_four_evidence_cards_a_to_d(self):
        for case in CASES:
            self.assertEqual([e["id"] for e in case["evidence"]], ["A", "B", "C", "D"], case["id"])

    def test_every_dataset_link_resolves(self):
        for case in CASES:
            linked = [d["id"] for e in case["evidence"] for d in evidence_datasets(case, e)]
            self.assertEqual(sorted(linked), sorted(d["id"] for d in case["datasets"]), case["id"])

    def test_the_answer_is_always_one_of_the_options(self):
        for case in CASES:
            solution, questions = case["solution"], case["questions"]
            self.assertIn(solution["biomolecule"], questions["biomolecule"]["options"])
            self.assertIn(solution["mechanism"], questions["mechanism"]["options"])

    def test_every_wrong_option_has_its_own_feedback(self):
        for case in CASES:
            solution, questions = case["solution"], case["questions"]
            for field, feedback in (("biomolecule", "wrongBiomolecule"), ("mechanism", "wrongMechanism")):
                wrong = set(questions[field]["options"]) - {solution[field]}
                self.assertEqual(wrong, set(solution[feedback]), f"{case['id']} {field}")

    def test_options_are_known_biomolecules_and_mechanisms(self):
        for case in CASES:
            for option in case["questions"]["biomolecule"]["options"]:
                self.assertIn(option, BIOMOLECULE_BY_ID)
            for option in case["questions"]["mechanism"]["options"]:
                self.assertIn(option, MECHANISM_BY_ID)

    def test_datasets_have_a_value_for_every_series(self):
        for case in CASES:
            for dataset in case["datasets"]:
                for row in dataset["rows"]:
                    for series in dataset["series"]:
                        self.assertIsInstance(row[series["key"]], (int, float))
                        self.assertLessEqual(row[series["key"]], dataset["yMax"])

    def test_six_mechanisms_are_case_answers(self):
        self.assertEqual(len(answer_mechanisms()), 6)


class TestLibrary(unittest.TestCase):
    def test_quiz_has_ten_valid_questions(self):
        self.assertEqual(len(QUIZ), 10)
        for question in QUIZ:
            self.assertTrue(0 <= question["answer"] < len(question["options"]))

    def test_toxin_targets_and_mechanism_targets_are_biomolecules(self):
        for category in TOXIN_CATEGORIES:
            for entry in category["entries"]:
                self.assertIn(entry["target"], BIOMOLECULE_BY_ID, entry["name"])
        for mechanism in MECHANISMS:
            self.assertIn(mechanism["biomolecule"], BIOMOLECULE_BY_ID)
        self.assertEqual(toxin_entry_count(), 17)

    def test_cell_routes_only_visit_known_parts(self):
        for route in CELL_MAP["routes"].values():
            for part in route["path"]:
                self.assertIn(part, CELL_PART_BY_ID)


if __name__ == "__main__":
    unittest.main()
