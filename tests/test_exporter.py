"""Checks for the feedback-to-CSV grade sheet export."""

import csv

from ai_grader.exporter import export_grades

_FB = """| Criterion | Score | Brief comment |
|-----------|-------|---------------|
| Data choice | {a}/1 | ok |
| Error analysis | {b}/3 | ok |
| **Total** | **{t}/20** | |

feedback text
"""


def _write(dirpath, name, **kw):
    (dirpath / f"{name}_feedback.md").write_text(_FB.format(**kw), encoding="utf-8")


def test_export_builds_grade_sheet(tmp_path):
    _write(tmp_path, "group-1", a=1, b=3, t=18)
    _write(tmp_path, "group-2", a="0.5", b=2, t=12)
    dest = tmp_path / "grades.csv"

    count = export_grades(tmp_path, dest)

    assert count == 2
    with dest.open(encoding="utf-8-sig") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        body = list(reader)
    assert header == ["Submission", "Data choice (/1)", "Error analysis (/3)", "Total"]
    assert ["group-1", "1.0", "3.0", "18.0"] == body[0]
    assert ["group-2", "0.5", "2.0", "12.0"] == body[1]


def test_export_handles_missing_total(tmp_path):
    # Feedback with criterion rows but no Total line: row included, Total blank.
    (tmp_path / "g_feedback.md").write_text(
        "| Criterion | Score | C |\n|--|--|--|\n| Data choice | 1/1 | ok |\n", encoding="utf-8"
    )
    dest = tmp_path / "out.csv"
    assert export_grades(tmp_path, dest) == 1
    last = dest.read_text(encoding="utf-8-sig").splitlines()[-1]
    assert last.endswith(",")  # empty Total column


def test_export_skips_unreadable_file(tmp_path):
    _write(tmp_path, "good", a=1, b=3, t=18)
    (tmp_path / "bad_feedback.md").write_bytes(b"\xff\xfe invalid utf-8 \x80\x81")
    dest = tmp_path / "out.csv"
    # Bad file is skipped, the good one still exported (no crash).
    assert export_grades(tmp_path, dest) == 1


def test_export_ignores_total_in_criteria_columns(tmp_path):
    _write(tmp_path, "g", a=1, b=3, t=18)
    dest = tmp_path / "out.csv"
    export_grades(tmp_path, dest)
    header = dest.read_text(encoding="utf-8-sig").splitlines()[0]
    assert header.count("Total") == 1  # Total only as the final column, not a criterion
