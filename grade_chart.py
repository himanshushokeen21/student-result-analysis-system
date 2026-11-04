"""
Grade-distribution chart utility (Figure 3.4 of the project report).

    python grade_chart.py      (saves grade_distribution.png)

Requires Matplotlib:  pip install matplotlib
"""

from result_analysis_system import DB_PATH, Database, ReportGenerator

GRADES = ["A+", "A", "B+", "B", "C", "D", "F"]
COLOURS = ["#2E7D32", "#4C9A4E", "#7FB2D5", "#5A8FC0", "#F2B843", "#E08A3C", "#C0392B"]


def grade_counts(db: Database) -> dict:
    counts = {g: 0 for g in GRADES}
    for result in ReportGenerator.class_results(db):
        counts[result.grade] += 1
    return counts


def make_figure(db: Database):
    """Return the grade-distribution bar chart as a Matplotlib Figure."""
    from matplotlib.figure import Figure

    counts = grade_counts(db)
    values = [counts[g] for g in GRADES]
    fig = Figure(figsize=(6.4, 4.2), dpi=100)
    ax = fig.add_subplot(111)
    bars = ax.bar(GRADES, values, color=COLOURS, edgecolor="#333333", linewidth=0.8)
    for bar, value in zip(bars, values):
        if value:
            ax.text(bar.get_x() + bar.get_width() / 2, value + 0.08, str(value),
                    ha="center", va="bottom", fontsize=10)
    ax.set_title(f"Grade Distribution - Class of {sum(values)} Students",
                 fontsize=12, fontweight="bold")
    ax.set_xlabel("Grade")
    ax.set_ylabel("Number of Students")
    ax.set_ylim(0, max(values + [1]) + 1.5)
    ax.yaxis.get_major_locator().set_params(integer=True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    return fig


if __name__ == "__main__":
    database = Database(DB_PATH)
    make_figure(database).savefig("grade_distribution.png", dpi=150)
    database.close()
    print("Chart saved as grade_distribution.png")
