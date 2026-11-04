# Student Result Analysis System

BCA 311 Summer Training Project · Himanshu Shokeen · Guide: Dr. Ranjeeta Kaur

This folder is the project described in the project report: the menu-driven Python program
from Annexure A-11, its sample data and test suite, plus a web front end so the same system
can be opened from a link.

| File | What it is |
|---|---|
| `result_analysis_system.py` | The main program (Annexure A-11): Database, ResultEngine, ReportGenerator, CLI menu |
| `seed_data.py` | Loads the sample class of 15 BCA-II students (Annexure A-10) |
| `test_result_analysis.py` | The 18 automated tests (Chapter 4.3, Annexure A-8) |
| `grade_chart.py` | Grade-distribution chart utility (Figure 3.4) |
| `streamlit_app.py` | Web front end that reuses the same three classes |
| `run_menu.bat` / `run_web.bat` | Double-click starters for Windows |

---

## 1. Run it on a laptop (Implementation Manual, Chapter 4.4)

1. Install Python 3.8 or later from python.org (on Windows tick **"Add python.exe to PATH"**).
2. Open a terminal in this folder and run:

```
python seed_data.py                 # optional: load the sample class of 15 students
python result_analysis_system.py    # start the menu
```

On Windows you can instead double-click **`run_menu.bat`** (it loads the sample class the first
time). On Mac or Linux use `python3` instead of `python`.

The program creates `result_analysis.db` in this folder on its first run.

**Tests** (should print `Ran 18 tests ... OK`, the same as Annexure A-8):

```
python -m unittest test_result_analysis -v
```

**Chart** (Figure 3.4, needs `pip install matplotlib`):

```
python grade_chart.py
```

## 2. Run the web version on the laptop

Double-click **`run_web.bat`**, or:

```
python -m pip install -r requirements.txt
python -m streamlit run streamlit_app.py
```

It opens in the browser at http://localhost:8501. The first visit loads the sample class.

## 3. Put it online (get a link)

Streamlit Community Cloud hosts it for free. It needs a GitHub account and takes about 10 minutes.

1. On github.com, create a new **public** repository, for example `student-result-analysis-system`.
2. On the new repository page choose **Add file → Upload files**, drag in every file from this
   folder (plus the `.streamlit` folder if it shows), then **Commit changes**.
   `result_analysis.db` does not need to be uploaded.
3. Go to **share.streamlit.io**, sign in with GitHub, click **Create app**, then
   **"Yup, I have an app"**.
4. Choose the repository, branch `main`, main file path `streamlit_app.py`. In **App URL** you can
   pick a name, for example `sras-himanshu`.
5. Click **Deploy**. After a few minutes the app is live at `https://<name>.streamlit.app`.

Free apps go to sleep after 12 hours without visitors. Opening the link shows a
"Yes, get this app back up!" button and it wakes in about a minute, so open it shortly before a
demo. **Reload sample data** in the sidebar resets the online data at any time.

---

## How results are calculated (Table 3.1 and Annexure A-6)

| Cleared every subject (≥ 40%)? | Overall % | Result | Grade | Division |
|---|---|---|---|---|
| No | any | Fail | F | Fail |
| Yes | ≥ 90 | Pass | A+ | First Division |
| Yes | 80 – 89.99 | Pass | A | First Division |
| Yes | 70 – 79.99 | Pass | B+ | First Division |
| Yes | 60 – 69.99 | Pass | B | First Division |
| Yes | 50 – 59.99 | Pass | C | Second Division |
| Yes | 40 – 49.99 | Pass | D | Third Division |
| Yes | < 40 | Fail | F | Fail |

The class analysis ranks every student by percentage and shows the pass percentage, the topper,
subject-wise average/highest/lowest marks and the grade distribution chart.

## Changes from the listing printed in Annexure A-11

The classes, method names, rules and output formats are the same as the printed listing. Four
small changes stop the menu from crashing during a demo:

1. Typing letters where a number is expected now shows an error message instead of stopping the
   program (new `read_number()` helper, and the menu catches `ValueError`).
2. Option 3 checks the roll number exists before asking for marks.
3. Option 2 rejects a maximum of 0 or less, as Table 3.2 says.
4. Class analysis skips students who have no marks yet instead of stopping with an error
   (new `ReportGenerator.class_results()` helper).
