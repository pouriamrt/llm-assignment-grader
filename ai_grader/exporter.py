"""Export graded feedback files into a single CSV grade sheet (one row per submission).

Parses the rubric table in each ``*_feedback.md`` so every criterion becomes a
column, ending in the Total. Stdlib ``csv`` only — opens directly in Excel.
"""

import csv
import re
from pathlib import Path

from loguru import logger

# Table row:  | Criterion | score/max | comment |   (header/separator rows won't match)
_ROW_RE = re.compile(r"^\|\s*(.+?)\s*\|\s*\*{0,2}([\d.]+)\s*/\s*(\d+)\*{0,2}\s*\|", re.M)


def _parse_feedback(text: str) -> tuple[dict[str, float], list[tuple[str, int]], float | None]:
    """Return (criterion->score, ordered [(criterion, max)], total) from one feedback file."""
    scores: dict[str, float] = {}
    order: list[tuple[str, int]] = []
    seen: set[str] = set()
    total: float | None = None
    for name, score, mx in _ROW_RE.findall(text):
        label = name.replace("**", "").strip()
        value = float(score)
        if label.lower() == "total":
            total = value
            continue
        scores[label] = value
        if label not in seen:
            seen.add(label)
            order.append((label, int(mx)))
    return scores, order, total


def export_grades(output_dir: Path, dest: Path) -> int:
    """
    Build a CSV grade sheet from all ``*_feedback.md`` files in ``output_dir``.

    Columns: Submission, <each criterion (/max)>, Total. Criterion columns are
    the union across files, ordered by first appearance. Returns the row count.
    """
    feedback_files = sorted(Path(output_dir).glob("*_feedback.md"))
    rows: list[tuple[str, dict[str, float], float | None]] = []
    columns: list[tuple[str, int]] = []
    seen_cols: set[str] = set()
    for f in feedback_files:
        try:
            text = f.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            logger.warning("Skipping unreadable feedback file {}: {}", f.name, e)
            continue
        scores, order, total = _parse_feedback(text)
        if not scores and total is None:
            continue
        for col in order:
            if col[0] not in seen_cols:
                seen_cols.add(col[0])
                columns.append(col)
        rows.append((f.stem.removesuffix("_feedback"), scores, total))

    headers = ["Submission"] + [f"{name} (/{mx})" for name, mx in columns] + ["Total"]
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.writer(fh)
        writer.writerow(headers)
        for name, scores, total in rows:
            writer.writerow(
                [name] + [scores.get(c[0], "") for c in columns] + ["" if total is None else total]
            )
    return len(rows)
