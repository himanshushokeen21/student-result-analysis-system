"""
Sample-data generator for the Student Result Analysis System.

Loads the seeded sample class of 15 BCA-II students used for system testing
and for the sample outputs in Annexure A-10 of the project report.

    python seed_data.py        (replaces everything in result_analysis.db)
"""

from result_analysis_system import DB_PATH, Database

CLASS_NAME = "BCA-II"

SUBJECTS = [
    ("Programming in Python", 100),
    ("Database Management Systems", 100),
    ("Data Structures", 100),
    ("Computer Networks", 100),
    ("English & Communication Skills", 50),
]

# roll_no: (name, marks in the same order as SUBJECTS)
STUDENTS = {
    101: ("Aarav Sharma",   (52.5, 55.0, 48.4, 50.6, 25.5)),
    102: ("Devansh Mehta",  (32.5, 35.0, 28.4, 31.6, 18.5)),
    103: ("Priya Verma",    (62.0, 65.5, 58.4, 60.2, 30.5)),
    104: ("Rohit Kumar",    (74.0, 70.5, 68.2, 72.5, 37.5)),
    105: ("Sneha Gupta",    (45.5, 38.4, 41.0, 39.5, 20.5)),
    106: ("Manish Yadav",   (70.5, 66.0, 68.4, 71.4, 33.0)),
    107: ("Kavya Nair",     (72.4, 78.0, 74.5, 76.2, 38.5)),
    108: ("Aditya Singh",   (86.0, 84.5, 88.2, 83.4, 42.5)),
    109: ("Neha Chauhan",   (78.5, 82.0, 76.4, 80.0, 42.5)),
    110: ("Vikram Rathi",   (52.0, 48.5, 36.0, 42.5, 21.0)),
    111: ("Ishita Bhatt",   (84.8, 94.0, 91.5, 91.2, 44.1)),
    112: ("Karan Malhotra", (88.5, 90.0, 87.4, 89.6, 42.3)),
    113: ("Pooja Rani",     (80.2, 76.5, 78.0, 77.6, 39.5)),
    114: ("Saurabh Tiwari", (30.0, 28.5, 33.2, 29.1, 17.5)),
    115: ("Ananya Joshi",   (34.5, 44.0, 42.2, 40.5, 22.0)),
}


def seed(db: Database) -> None:
    """Clear the database and load the sample class."""
    db.conn.execute("DELETE FROM marks")
    db.conn.execute("DELETE FROM students")
    db.conn.execute("DELETE FROM subjects")
    db.conn.execute("DELETE FROM sqlite_sequence WHERE name IN ('subjects', 'marks')")
    db.conn.commit()
    subject_ids = [db.add_subject(name, max_marks) for name, max_marks in SUBJECTS]
    for roll_no, (name, marks) in STUDENTS.items():
        db.add_student(roll_no, name, CLASS_NAME)
        for subject_id, obtained in zip(subject_ids, marks):
            db.set_marks(roll_no, subject_id, obtained)


if __name__ == "__main__":
    database = Database(DB_PATH)
    seed(database)
    database.close()
    print(f"Sample class of {len(STUDENTS)} students and {len(SUBJECTS)} subjects "
          f"loaded into {DB_PATH.name}.")
