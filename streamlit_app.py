"""
Web front end for the Student Result Analysis System (Streamlit).

It reuses the Database, ResultEngine and ReportGenerator classes from
result_analysis_system.py unchanged - only the presentation layer is new,
as planned in Chapter 3.1 and Chapter 5.4 of the project report.

    Run on a computer :  streamlit run streamlit_app.py
    Put online        :  Streamlit Community Cloud, main file streamlit_app.py
"""

import os
from pathlib import Path

import streamlit as st

import grade_chart
import seed_data
from result_analysis_system import (DB_PATH, GRADE_BANDS, PASS_PERCENTAGE, Database,
                                    ReportGenerator, ResultEngine)

st.set_page_config(page_title="Student Result Analysis System", layout="wide")

MENU = [
    "1. Add Student",
    "2. Add Subject",
    "3. Enter / Update Marks",
    "4. View Report Card",
    "5. Class Result Analysis",
    "6. Subject-wise Statistics",
]

db = Database(Path(os.environ.get("SRAS_DB", DB_PATH)))
if not db.all_students() and not db.all_subjects():
    seed_data.seed(db)  # first visit: load the sample class of 15 students


def student_label(row):
    return f"{row[0]} - {row[1]}"


def table_height(rows):
    return min(38 + 35 * max(len(rows), 1), 600)


def parse_number(text, cast, what):
    try:
        return cast(str(text).strip())
    except ValueError:
        raise ValueError(f"'{text}' is not a valid {what}.") from None


# ---------------------------------------------------------------- sidebar

with st.sidebar:
    st.markdown("## Student Result Analysis System")
    st.caption("BCA 311 Summer Training · Himanshu Shokeen")
    page = st.radio("Main menu", MENU)
    st.divider()
    with st.expander("How results are calculated"):
        st.markdown(
            f"- **Pass:** at least {PASS_PERCENTAGE:.0f}% in **every** subject and "
            f"{PASS_PERCENTAGE:.0f}% overall\n"
            "- **Grade:** " + " · ".join(f"{g} ≥ {c}" for c, g in GRADE_BANDS if g != "F")
            + " · F = failed\n"
            "- **Division:** First ≥ 60 · Second ≥ 50 · Third ≥ 40")
    if st.button("Reload sample data"):
        seed_data.seed(db)
        for key in [k for k in st.session_state.keys() if str(k).startswith("m_")]:
            del st.session_state[key]
        st.success("Sample class of 15 students reloaded.")
    st.caption(f"{len(db.all_students())} students · {len(db.all_subjects())} subjects · SQLite")

st.title(page[3:])

# ---------------------------------------------------------------- 1. Add Student

if page == MENU[0]:
    form_col, list_col = st.columns([1, 1.3], gap="large")
    with form_col:
        st.caption("Entering an existing roll number updates that student's details.")
        with st.form("student_form", clear_on_submit=True):
            roll = st.text_input("Roll No")
            name = st.text_input("Name")
            class_name = st.text_input("Class", value=seed_data.CLASS_NAME)
            submitted = st.form_submit_button("Save Student", type="primary")
        if submitted:
            try:
                roll_no = parse_number(roll, int, "roll number")
                if roll_no <= 0:
                    raise ValueError("Roll No must be a positive whole number.")
                if not name.strip() or not class_name.strip():
                    raise ValueError("Name and Class cannot be empty.")
                existed = db.get_student(roll_no) is not None
                db.add_student(roll_no, name.strip(), class_name.strip())
                st.success(f"Student {roll_no} {'updated' if existed else 'added'}.")
            except ValueError as err:
                st.error(str(err))
    with list_col:
        st.subheader("Students")
        rows = [{"Roll No": r, "Name": n, "Class": c} for r, n, c in db.all_students()]
        st.dataframe(rows, hide_index=True, height=table_height(rows))

# ---------------------------------------------------------------- 2. Add Subject

elif page == MENU[1]:
    form_col, list_col = st.columns([1, 1.3], gap="large")
    with form_col:
        st.caption("New subjects appear in Enter / Update Marks for every student.")
        with st.form("subject_form", clear_on_submit=True):
            name = st.text_input("Subject name")
            max_marks = st.text_input("Maximum marks", value="100")
            submitted = st.form_submit_button("Save Subject", type="primary")
        if submitted:
            try:
                if not name.strip():
                    raise ValueError("Subject name cannot be empty.")
                maximum = parse_number(max_marks, float, "number")
                if maximum <= 0:
                    raise ValueError("Maximum marks must be a positive number.")
                if any(s[1] == name.strip() for s in db.all_subjects()):
                    raise ValueError(f"Subject '{name.strip()}' already exists.")
                db.add_subject(name.strip(), maximum)
                st.success(f"Subject '{name.strip()}' added.")
            except ValueError as err:
                st.error(str(err))
    with list_col:
        st.subheader("Subjects")
        rows = [{"ID": i, "Subject": n, "Max Marks": m} for i, n, m in db.all_subjects()]
        st.dataframe(rows, hide_index=True, height=table_height(rows))

# ---------------------------------------------------------------- 3. Enter / Update Marks

elif page == MENU[2]:
    students, subjects = db.all_students(), db.all_subjects()
    if not students:
        st.info("Add a student first (menu option 1).")
    elif not subjects:
        st.info("Add a subject first (menu option 2).")
    else:
        student = st.selectbox("Student", students, format_func=student_label)
        roll_no = student[0]
        with st.form(f"marks_form_{roll_no}"):
            typed = []
            for sid, name, max_marks in subjects:
                current = dict(db.marks_for_subject(sid)).get(roll_no)
                text = st.text_input(f"Marks in {name} (out of {max_marks})",
                                     value="" if current is None else f"{current:.1f}",
                                     key=f"m_{roll_no}_{sid}")
                typed.append((sid, name, max_marks, text))
            saved = st.form_submit_button("Save Marks", type="primary")
        if saved:
            rejected, recorded = [], 0
            for sid, name, max_marks, text in typed:
                if not text.strip():
                    continue  # not entered yet
                try:
                    marks = parse_number(text, float, "number")
                    ResultEngine.validate_marks(marks, max_marks)
                except ValueError as err:  # includes MarksValidationError
                    rejected.append(f"{name}: {err}")
                    continue
                db.set_marks(roll_no, sid, marks)
                recorded += 1
            if recorded:
                st.success(f"Marks recorded for {recorded} subject(s).")
            if rejected:
                st.error("Rejected:\n\n" + "\n".join(f"- {r}" for r in rejected))
        try:
            result = ResultEngine.compute_result(db, roll_no)
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total", f"{result.total_obtained:.1f} / {result.total_max:.0f}")
            c2.metric("Percentage", f"{result.percentage:.2f}%")
            c3.metric("Grade", result.grade)
            c4.metric("Result", f"{result.status} · {result.division}")
        except ValueError as err:
            st.info(str(err))

# ---------------------------------------------------------------- 4. View Report Card

elif page == MENU[3]:
    students = db.all_students()
    if not students:
        st.info("Add a student first (menu option 1).")
    else:
        student = st.selectbox("Student", students, format_func=student_label)
        try:
            result = ResultEngine.compute_result(db, student[0])
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Percentage", f"{result.percentage:.2f}%")
            c2.metric("Grade", result.grade)
            c3.metric("Division", result.division)
            c4.metric("Result", result.status)
            st.code(ReportGenerator.report_card(result), language=None)
        except ValueError as err:
            st.info(f"{err}. Enter marks in option 3 first.")

# ---------------------------------------------------------------- 5. Class Result Analysis

elif page == MENU[4]:
    results = ReportGenerator.class_results(db)
    if not results:
        st.info("No results yet. Enter marks first (menu option 3).")
    else:
        passed = sum(1 for r in results if r.status == "Pass")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total students", len(results))
        c2.metric("Passed", passed)
        c3.metric("Failed", len(results) - passed)
        c4.metric("Pass %", f"{round(passed / len(results) * 100, 1)}%")
        topper = max(results, key=lambda r: r.percentage)
        st.success(f"Topper: {topper.name} (Roll {topper.roll_no}) - {topper.percentage:.2f}%")
        left, right = st.columns([1.15, 1], gap="large")
        with left:
            st.subheader("Rank list")
            ranked = sorted(results, key=lambda r: -r.percentage)
            rows = [{"Rank": i, "Roll No": r.roll_no, "Name": r.name,
                     "Percentage": r.percentage, "Grade": r.grade, "Result": r.status}
                    for i, r in enumerate(ranked, start=1)]
            st.dataframe(rows, hide_index=True, height=table_height(rows))
        with right:
            st.subheader("Grade distribution")
            st.pyplot(grade_chart.make_figure(db))
        with st.expander("Show as text (same output as the menu program, option 5)"):
            st.code(ReportGenerator.class_analysis(db), language=None)

# ---------------------------------------------------------------- 6. Subject-wise Statistics

elif page == MENU[5]:
    rows = []
    for sid, name, max_marks in db.all_subjects():
        values = [m for _, m in db.marks_for_subject(sid)]
        if values:
            rows.append({"Subject": name, "Max": max_marks, "Students": len(values),
                         "Average": round(sum(values) / len(values), 1),
                         "Highest": max(values), "Lowest": min(values)})
    if not rows:
        st.info("No marks recorded yet.")
    else:
        st.dataframe(rows, hide_index=True, height=table_height(rows))
        with st.expander("Show as text (same output as the menu program, option 6)"):
            st.code(ReportGenerator.subject_wise_stats(db), language=None)
