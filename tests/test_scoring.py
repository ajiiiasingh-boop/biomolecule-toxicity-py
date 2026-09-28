"""Checks the grading algorithm, the score and the quiz marking."""

import unittest

from btd import progress as prog
from btd.data import CASE_BY_ID, QUIZ
from btd.scoring import get_hint, grade_case, grade_quiz

CASE = CASE_BY_ID["case-01"]            # answer: protein + enzyme-inhibition


class TestGradeCase(unittest.TestCase):
    def test_perfect_first_attempt_scores_120(self):
        result = grade_case(CASE, "protein", "enzyme-inhibition")
        self.assertTrue(result["solved"])
        self.assertEqual(result["points"], 120)          # 50 + 50 + 20 bonus
        self.assertIsNotNone(result["explanation"])
        self.assertEqual(len(result["pathway"]), 6)

    def test_each_hint_costs_ten_and_removes_the_bonus(self):
        self.assertEqual(grade_case(CASE, "protein", "enzyme-inhibition", hints_used=1)["points"], 90)
        self.assertEqual(grade_case(CASE, "protein", "enzyme-inhibition", hints_used=2)["points"], 80)

    def test_second_attempt_has_no_bonus(self):
        self.assertEqual(grade_case(CASE, "protein", "enzyme-inhibition", attempt=2)["points"], 100)

    def test_half_right_is_not_solved_and_gets_feedback(self):
        result = grade_case(CASE, "protein", "protein-denaturation")
        self.assertFalse(result["solved"])
        self.assertEqual(result["points"], 50)
        self.assertIsNone(result["explanation"])
        self.assertIn("Correct", result["feedback"]["biomolecule"])
        self.assertIn("melting temperature", result["feedback"]["mechanism"])

    def test_points_never_go_below_zero(self):
        self.assertEqual(grade_case(CASE, "lipid", "oxidative-damage", hints_used=2)["points"], 0)

    def test_hints_exist_for_both_questions(self):
        self.assertTrue(get_hint(CASE, "biomolecule"))
        self.assertTrue(get_hint(CASE, "mechanism"))


class TestQuiz(unittest.TestCase):
    def test_all_correct(self):
        result = grade_quiz(QUIZ, {q["id"]: q["answer"] for q in QUIZ})
        self.assertEqual((result["score"], result["points"], result["percentage"]), (10, 100, 100))

    def test_all_wrong(self):
        wrong = {q["id"]: (q["answer"] + 1) % len(q["options"]) for q in QUIZ}
        self.assertEqual(grade_quiz(QUIZ, wrong)["score"], 0)


class TestProgress(unittest.TestCase):
    def test_points_are_banked_only_once(self):
        notebook = prog.new_progress()
        result = grade_case(CASE, "protein", "enzyme-inhibition")
        self.assertTrue(prog.record_attempt(notebook, "case-01", result))
        self.assertFalse(prog.record_attempt(notebook, "case-01", result))
        self.assertEqual(notebook["score"], 120)
        self.assertEqual(prog.summary(notebook)["attempts"], 2)

    def test_quiz_retake_replaces_the_old_points(self):
        notebook = prog.new_progress()
        prog.record_quiz(notebook, {"score": 4, "total": 10, "points": 40})
        prog.record_quiz(notebook, {"score": 7, "total": 10, "points": 70})
        self.assertEqual(notebook["score"], 70)

    def test_next_unsolved_and_report(self):
        notebook = prog.new_progress()
        self.assertEqual(prog.next_unsolved(notebook), "case-01")
        prog.record_attempt(notebook, "case-01", grade_case(CASE, "protein", "enzyme-inhibition"))
        self.assertEqual(prog.next_unsolved(notebook), "case-02")
        report = prog.make_report(notebook, "Test")
        self.assertIn("SOLVED", report)
        self.assertIn("Detective: Test", report)


if __name__ == "__main__":
    unittest.main()
