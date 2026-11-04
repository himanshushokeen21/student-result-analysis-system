"""
Automated test suite for the Student Result Analysis System (Chapter 4).

    python -m unittest test_result_analysis -v
"""

import unittest

from result_analysis_system import Database, MarksValidationError, ResultEngine


class TestMarksValidation(unittest.TestCase):
    """Unit tests: ResultEngine.validate_marks, boundary values (TC-01 to TC-04)."""

    def test_zero_marks_is_valid(self):
        ResultEngine.validate_marks(0, 100)

    def test_maximum_marks_is_valid(self):
        ResultEngine.validate_marks(100, 100)

    def test_marks_just_below_maximum_is_valid(self):
        ResultEngine.validate_marks(99.9, 100)

    def test_negative_marks_rejected(self):
        with self.assertRaises(MarksValidationError):
            ResultEngine.validate_marks(-5, 100)

    def test_marks_above_maximum_rejected(self):
        with self.assertRaises(MarksValidationError):
            ResultEngine.validate_marks(105, 100)


class TestGradeAndDivision(unittest.TestCase):
    """Unit tests: grade bands and divisions around every cutoff (TC-05 to TC-07)."""

    def test_grade_at_A_plus_cutoff(self):
        self.assertEqual(ResultEngine.grade_for_percentage(90), "A+")

    def test_grade_just_below_A_plus_cutoff(self):
        self.assertEqual(ResultEngine.grade_for_percentage(89.99), "A")

    def test_grade_at_pass_cutoff(self):
        self.assertEqual(ResultEngine.grade_for_percentage(40), "D")

    def test_grade_just_below_pass_cutoff(self):
        self.assertEqual(ResultEngine.grade_for_percentage(39.99), "F")

    def test_division_first(self):
        self.assertEqual(ResultEngine.division_for_percentage(60, True), "First Division")

    def test_division_second(self):
        self.assertEqual(ResultEngine.division_for_percentage(55, True), "Second Division")

    def test_division_third(self):
        self.assertEqual(ResultEngine.division_for_percentage(45, True), "Third Division")

    def test_division_fail_overrides_percentage(self):
        self.assertEqual(ResultEngine.division_for_percentage(95, False), "Fail")


class TestComputeResultIntegration(unittest.TestCase):
    """Integration tests: Database + ResultEngine.compute_result (TC-08 to TC-10)."""

    def setUp(self):
        self.db = Database(":memory:")
        self.sub1 = self.db.add_subject("Subject 1", 100)
        self.sub2 = self.db.add_subject("Subject 2", 100)
        self.db.add_student(1, "Test Student", "BCA-II")

    def tearDown(self):
        self.db.close()

    def test_student_who_clears_everything_passes(self):
        self.db.set_marks(1, self.sub1, 84.8)
        self.db.set_marks(1, self.sub2, 94.0)
        result = ResultEngine.compute_result(self.db, 1)
        self.assertEqual(result.percentage, 89.4)
        self.assertEqual((result.status, result.grade, result.division),
                         ("Pass", "A", "First Division"))

    def test_student_failing_one_subject_fails_overall(self):
        self.db.set_marks(1, self.sub1, 95)   # TC-08: high overall percentage...
        self.db.set_marks(1, self.sub2, 20)   # ...but one subject below 40%
        result = ResultEngine.compute_result(self.db, 1)
        self.assertEqual((result.status, result.division, result.grade), ("Fail", "Fail", "F"))

    def test_missing_student_raises(self):
        with self.assertRaises(ValueError):    # TC-09
            ResultEngine.compute_result(self.db, 999)

    def test_student_with_no_marks_raises(self):
        with self.assertRaises(ValueError):
            ResultEngine.compute_result(self.db, 1)

    def test_updating_marks_overwrites_previous_value(self):
        self.db.set_marks(1, self.sub1, 50)    # TC-10
        self.db.set_marks(1, self.sub1, 65)
        rows = self.db.marks_for_subject(self.sub1)
        self.assertEqual(rows, [(1, 65.0)])    # updated, not a duplicate row


if __name__ == "__main__":
    unittest.main()
