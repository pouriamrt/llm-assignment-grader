"""Validate and correct grading output to enforce valid score bounds."""

import re


def _parse_total_score(text: str) -> tuple[float, float] | None:
    """Extract total (score, out_of) from feedback. Returns None if not found."""
    for line in text.splitlines():
        if "total" not in line.lower():
            continue
        m = re.search(r"(\d+(?:\.\d+)?)/(\d+(?:\.\d+)?)", line)
        if m:
            return (float(m.group(1)), float(m.group(2)))
    matches = list(re.finditer(r"(\d+(?:\.\d+)?)/(\d+(?:\.\d+)?)", text))
    if matches:
        m = matches[-1]
        return (float(m.group(1)), float(m.group(2)))
    return None


def _replace_total_in_text(text: str, new_score: float, out_of: float) -> str:
    """Replace the Total row score in the feedback text."""

    # Match Total row: | **Total** | **2/2** | or | Total | 2/2 |
    def repl(m: re.Match) -> str:
        prefix = m.group(1)
        suffix = m.group(2)
        # Preserve bold style if present
        if "**" in prefix or "**" in text[m.start() : m.end()]:
            return f"{prefix}**{new_score:.1f}/{out_of:.0f}**{suffix}"
        return f"{prefix}{new_score:.1f}/{out_of:.0f}{suffix}"

    pattern = r"(\|\s*.*?Total.*?\|\s*)\*{0,2}\d+(?:\.\d+)?/\d+(?:\.\d+)?\*{0,2}(\s*\|)"
    return re.sub(pattern, repl, text, count=1, flags=re.IGNORECASE)


def apply_grade_guardrails(
    feedback: str,
    *,
    min_grade: float = 1.0,
    max_grade: float = 2.0,
    out_of: float | None = 2.0,
) -> str:
    """
    Ensure total grade is valid: within [min_grade, max_grade].
    Only applies when total is out of 2 (or specified out_of).
    """
    parsed = _parse_total_score(feedback)
    if not parsed:
        return feedback

    score, parsed_out_of = parsed
    if parsed_out_of <= 0:
        return feedback

    # Only apply when scale matches (e.g. out of 2)
    if out_of is not None and abs(parsed_out_of - out_of) > 0.01:
        return feedback

    clamped = max(min_grade, min(max_grade, score))
    if clamped != score:
        return _replace_total_in_text(feedback, clamped, parsed_out_of)
    return feedback
