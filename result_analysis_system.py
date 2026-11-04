"""
Student Result Analysis System
--------------------------------
BCA 311 - Summer Training Project
Submitted by: Himanshu Shokeen

A menu-driven, database-backed Python application that stores students'
subject-wise marks, computes their results (total, percentage, grade,
division, pass/fail), generates individual report cards, and produces
class-level result analysis.

Modules (kept in this single file for clarity in the report; in the
actual submission these correspond to the module boundaries described
in Chapter 3 - System Design):
    - Data-access layer   : Database class
    - Business-logic layer: ResultEngine class
    - Presentation layer  : ReportGenerator class, run_cli()
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

DB_PATH = Path(__file__).parent / "result_analysis.db"

# Grading scheme used by this project (documented in Chapter 3.1 / 5.2).
GRADE_BANDS = [
    (90, "A+"),
    (80, "A"),
    (70, "B+"),
    (60, "B"),
    (50, "C"),
    (40, "D"),
    (0, "F"),
]
PASS_PERCENTAGE = 40.0


# --------------------------------------------------------------------------
# Data-access layer
# --------------------------------------------------------------------------

class Database:
    """Owns the SQLite connection and schema for the application."""

    def __init__(self, path: Path = DB_PATH):
        self.path = path
        self.conn = sqlite3.connect(path)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._create_schema()

    def _create_schema(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS students (
                roll_no    INTEGER PRIMARY KEY,
                name       TEXT NOT NULL,
                class_name TEXT NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS subjects (
                subject_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT NOT NULL UNIQUE,
                max_marks  INTEGER NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS marks (
                mark_id        INTEGER PRIMARY KEY AUTOINCREMENT,
                roll_no        INTEGER NOT NULL,
                subject_id     INTEGER NOT NULL,
                marks_obtained REAL NOT NULL,
                FOREIGN KEY (roll_no) REFERENCES students(roll_no),
                FOREIGN KEY (subject_id) REFERENCES subjects(subject_id),
                UNIQUE (roll_no, subject_id)
            )
            """
        )
        self.conn.commit()

    # -- students -----------------------------------------------------
    def add_student(self, roll_no: int, name: str, class_name: str) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO students (roll_no, name, class_name) VALUES (?, ?, ?)",
            (roll_no, name, class_name),
        )
        self.conn.commit()

    def get_student(self, roll_no: int):
        return self.conn.execute(
            "SELECT roll_no, name, class_name FROM students WHERE roll_no = ?",
            (roll_no,),
        ).fetchone()

    def all_students(self):
        return self.conn.execute(
            "SELECT roll_no, name, class_name FROM students ORDER BY roll_no"
        ).fetchall()

    # -- subjects -----------------------------------------------------
    def add_subject(self, name: str, max_marks: int) -> int:
        cur = self.conn.execute(
            "INSERT OR IGNORE INTO subjects (name, max_marks) VALUES (?, ?)",
            (name, max_marks),
        )
        self.conn.commit()
        row = self.conn.execute(
            "SELECT subject_id FROM subjects WHERE name = ?", (name,)
        ).fetchone()
        return row[0]

    def all_subjects(self):
        return self.conn.execute(
            "SELECT subject_id, name, max_marks FROM subjects ORDER BY subject_id"
        ).fetchall()

    # -- marks --------------------------------------------------------
    def set_marks(self, roll_no: int, subject_id: int, marks_obtained: float) -> None:
        self.conn.execute(
            """
            INSERT INTO marks (roll_no, subject_id, marks_obtained)
            VALUES (?, ?, ?)
            ON CONFLICT(roll_no, subject_id)
            DO UPDATE SET marks_obtained = excluded.marks_obtained
            """,
            (roll_no, subject_id, marks_obtained),
        )
        self.conn.commit()

    def marks_for_student(self, roll_no: int):
        return self.conn.execute(
            """
            SELECT s.name, s.max_marks, m.marks_obtained
            FROM marks m JOIN subjects s ON m.subject_id = s.subject_id
            WHERE m.roll_no = ?
            ORDER BY s.subject_id
            """,
            (roll_no,),
        ).fetchall()

    def marks_for_subject(self, subject_id: int):
        return self.conn.execute(
            "SELECT roll_no, marks_obtained FROM marks WHERE subject_id = ?",
            (subject_id,),
        ).fetchall()

    def close(self) -> None:
        self.conn.close()


# --------------------------------------------------------------------------
# Business-logic layer
# --------------------------------------------------------------------------

class MarksValidationError(ValueError):
    """Raised when a marks entry fails validation (out of range, etc.)."""


@dataclass
class StudentResult:
    roll_no: int
    name: str
    class_name: str
    subject_marks: list  # list of (subject_name, max_marks, obtained)
    total_obtained: float
    total_max: float
    percentage: float
    grade: str
    division: str
    status: str  # "Pass" / "Fail"


class ResultEngine:
    """Pure computation logic - deliberately kept free of any I/O so it
    can be unit-tested in isolation (see test_result_analysis.py)."""

    @staticmethod
    def validate_marks(marks_obtained: float, max_marks: float) -> None:
        if marks_obtained < 0:
            raise MarksValidationError("Marks cannot be negative.")
        if marks_obtained > max_marks:
            raise MarksValidationError(
                f"Marks ({marks_obtained}) cannot exceed the maximum ({max_marks})."
            )

    @staticmethod
    def grade_for_percentage(percentage: float) -> str:
        for cutoff, grade in GRADE_BANDS:
            if percentage >= cutoff:
                return grade
        return "F"

    @staticmethod
    def division_for_percentage(percentage: float, passed: bool) -> str:
        if not passed:
            return "Fail"
        if percentage >= 60:
            return "First Division"
        if percentage >= 50:
            return "Second Division"
        if percentage >= 40:
            return "Third Division"
        return "Fail"

    @classmethod
    def compute_result(cls, db: Database, roll_no: int) -> StudentResult:
        student = db.get_student(roll_no)
        if student is None:
            raise ValueError(f"No student with roll number {roll_no}")
        _, name, class_name = student

        rows = db.marks_for_student(roll_no)
        if not rows:
            raise ValueError(f"No marks recorded for roll number {roll_no}")

        total_obtained = sum(r[2] for r in rows)
        total_max = sum(r[1] for r in rows)
        percentage = round(total_obtained / total_max * 100, 2) if total_max else 0.0

        # A student must clear each subject individually AND meet the
        # overall passing percentage to be declared "Pass" (documented
        # in Chapter 3.1 - Design Methodology).
        cleared_each_subject = all(
            (obtained / max_marks * 100) >= PASS_PERCENTAGE
            for _, max_marks, obtained in rows
        )
        passed = cleared_each_subject and percentage >= PASS_PERCENTAGE

        grade = cls.grade_for_percentage(percentage) if passed else "F"
        division = cls.division_for_percentage(percentage, passed)
        status = "Pass" if passed else "Fail"

        return StudentResult(
            roll_no=roll_no,
            name=name,
            class_name=class_name,
            subject_marks=rows,
            total_obtained=total_obtained,
            total_max=total_max,
            percentage=percentage,
            grade=grade,
            division=division,
            status=status,
        )


# --------------------------------------------------------------------------
# Presentation layer
# --------------------------------------------------------------------------

class ReportGenerator:
    """Formats StudentResult / class-analysis data as printable text."""

    @staticmethod
    def report_card(result: StudentResult) -> str:
        width = 62
        lines = []
        lines.append("=" * width)
        lines.append("STUDENT REPORT CARD".center(width))
        lines.append("=" * width)
        lines.append(f"Roll No : {result.roll_no}")
        lines.append(f"Name    : {result.name}")
        lines.append(f"Class   : {result.class_name}")
        lines.append("-" * width)
        lines.append(f"{'Subject':<34}{'Max':>10}{'Obtained':>18}")
        lines.append("-" * width)
        for subject_name, max_marks, obtained in result.subject_marks:
            lines.append(f"{subject_name:<34}{max_marks:>10.0f}{obtained:>18.1f}")
        lines.append("-" * width)
        lines.append(f"{'Total':<34}{result.total_max:>10.0f}{result.total_obtained:>18.1f}")
        lines.append("-" * width)
        lines.append(f"Percentage : {result.percentage:.2f}%")
        lines.append(f"Grade      : {result.grade}")
        lines.append(f"Division   : {result.division}")
        lines.append(f"Result     : {result.status}")
        lines.append("=" * width)
        return "\n".join(lines)

    @staticmethod
    def class_results(db: Database) -> list:
        """Results for every student who has marks recorded."""
        results = []
        for s in db.all_students():
            try:
                results.append(ResultEngine.compute_result(db, s[0]))
            except ValueError:
                continue  # no marks recorded yet for this student
        return results

    @staticmethod
    def class_analysis(db: Database) -> str:
        width = 56
        results = ReportGenerator.class_results(db)

        lines = []
        lines.append("=" * width)
        lines.append("CLASS RESULT ANALYSIS".center(width))
        lines.append("=" * width)
        if not results:
            lines.append("No results yet - enter marks first (option 3).")
            lines.append("=" * width)
            return "\n".join(lines)

        total = len(results)
        passed = sum(1 for r in results if r.status == "Pass")
        pass_pct = round(passed / total * 100, 1) if total else 0.0
        lines.append(f"Total Students : {total}")
        lines.append(f"Passed         : {passed}")
        lines.append(f"Failed         : {total - passed}")
        lines.append(f"Pass %         : {pass_pct}%")
        lines.append("-" * width)

        topper = max(results, key=lambda r: r.percentage)
        lines.append(f"Topper         : {topper.name} (Roll {topper.roll_no}) - {topper.percentage:.2f}%")
        lines.append("-" * width)

        lines.append(f"{'Rank':<6}{'Roll':<8}{'Name':<20}{'%':>8}{'Grade':>8}")
        lines.append("-" * width)
        for rank, r in enumerate(sorted(results, key=lambda r: -r.percentage), start=1):
            lines.append(f"{rank:<6}{r.roll_no:<8}{r.name:<20}{r.percentage:>8.2f}{r.grade:>8}")
        lines.append("=" * width)
        return "\n".join(lines)

    @staticmethod
    def subject_wise_stats(db: Database) -> str:
        width = 66
        lines = []
        lines.append("=" * width)
        lines.append("SUBJECT-WISE STATISTICS".center(width))
        lines.append("=" * width)
        lines.append(f"{'Subject':<32}{'Avg':>10}{'Highest':>12}{'Lowest':>12}")
        lines.append("-" * width)
        for subject_id, name, max_marks in db.all_subjects():
            rows = db.marks_for_subject(subject_id)
            if not rows:
                continue
            values = [m for _, m in rows]
            avg = sum(values) / len(values)
            lines.append(f"{name:<32}{avg:>10.1f}{max(values):>12.1f}{min(values):>12.1f}")
        lines.append("=" * width)
        return "\n".join(lines)


# --------------------------------------------------------------------------
# CLI (menu-driven interface)
# --------------------------------------------------------------------------

def read_number(prompt: str, cast=int):
    """Read a number from the keyboard; a non-numeric entry raises ValueError."""
    text = input(prompt).strip()
    try:
        return cast(text)
    except ValueError:
        kind = "whole number" if cast is int else "number"
        raise ValueError(f"'{text}' is not a valid {kind}.") from None


def run_cli() -> None:
    db = Database()
    menu = """
==================================================
     STUDENT RESULT ANALYSIS SYSTEM - MAIN MENU
==================================================
 1. Add Student
 2. Add Subject
 3. Enter / Update Marks
 4. View Report Card
 5. Class Result Analysis
 6. Subject-wise Statistics
 7. Exit
--------------------------------------------------
"""
    while True:
        print(menu)
        try:
            choice = input("Enter your choice (1-7): ").strip()
        except (EOFError, KeyboardInterrupt):
            choice = "7"

        try:
            if choice == "1":
                roll_no = read_number("Roll No: ")
                name = input("Name: ")
                class_name = input("Class: ")
                db.add_student(roll_no, name, class_name)
                print("Student added.\n")

            elif choice == "2":
                name = input("Subject name: ")
                max_marks = read_number("Maximum marks: ", float)
                if max_marks <= 0:
                    raise ValueError("Maximum marks must be a positive number.")
                db.add_subject(name, max_marks)
                print("Subject added.\n")

            elif choice == "3":
                roll_no = read_number("Roll No: ")
                if db.get_student(roll_no) is None:
                    raise ValueError(f"No student with roll number {roll_no}")
                subjects = db.all_subjects()
                for sid, name, max_marks in subjects:
                    try:
                        marks = read_number(f"Marks in {name} (out of {max_marks}): ", float)
                        ResultEngine.validate_marks(marks, max_marks)
                    except ValueError as exc:  # includes MarksValidationError
                        print(f" Rejected: {exc}")
                        continue
                    db.set_marks(roll_no, sid, marks)
                print("Marks recorded.\n")

            elif choice == "4":
                roll_no = read_number("Roll No: ")
                result = ResultEngine.compute_result(db, roll_no)
                print(ReportGenerator.report_card(result))

            elif choice == "5":
                print(ReportGenerator.class_analysis(db))

            elif choice == "6":
                print(ReportGenerator.subject_wise_stats(db))

            elif choice == "7":
                print("Exiting. Goodbye!")
                db.close()
                break

            else:
                print("Invalid choice, please try again.\n")

        except ValueError as exc:
            print(f"Error: {exc}\n")
        except (EOFError, KeyboardInterrupt):
            print("\nCancelled.\n")


if __name__ == "__main__":
    run_cli()
