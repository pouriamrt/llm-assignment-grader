"""Validate and correct grading output to enforce valid score bounds."""

import re

from loguru import logger

_SCORE_RE = re.compile(r"(\d+(?:\.\d+)?)/(\d+(?:\.\d+)?)")


def _parse_total_score(text: str) -> tuple[float, float] | None:
    """Extract total (score, out_of) from feedback. Returns None if not found."""
    for line in text.splitlines():
        if "total" not in line.lower():
            continue
        m = _SCORE_RE.search(line)
        if m:
            return (float(m.group(1)), float(m.group(2)))
    matches = list(_SCORE_RE.finditer(text))
    if matches:
        m = matches[-1]
        return (float(m.group(1)), float(m.group(2)))
    return None


def _fmt(score: float) -> str:
    """Format a score without trailing zeros: 16.0 -> '16', 18.5 -> '18.5'."""
    return f"{score:g}"


def _replace_total_in_text(text: str, new_score: float, out_of: float) -> str:
    """Replace the Total row score in the feedback text, preserving bold style."""

    def repl(m: re.Match) -> str:
        prefix, suffix = m.group(1), m.group(2)
        if "**" in m.group(0):
            return f"{prefix}**{_fmt(new_score)}/{_fmt(out_of)}**{suffix}"
        return f"{prefix}{_fmt(new_score)}/{_fmt(out_of)}{suffix}"

    pattern = r"(\|\s*.*?Total.*?\|\s*)\*{0,2}\d+(?:\.\d+)?/\d+(?:\.\d+)?\*{0,2}(\s*\|)"
    return re.sub(pattern, repl, text, count=1, flags=re.IGNORECASE)


def apply_grade_guardrails(
    feedback: str,
    *,
    min_grade: float = 0.0,
    max_grade: float | None = None,
    out_of: float | None = None,
) -> str:
    """
    Clamp the total grade into a valid range and rewrite it in the feedback.

    The total's scale (out_of) is read from the feedback itself, so this works
    for any rubric (e.g. /20, /100). The clamp is [min_grade, upper] where
    upper = min(max_grade, scale) — a grade can never exceed its own scale.

    Args:
        feedback: Raw LLM feedback markdown.
        min_grade: Lower bound / floor (e.g. 10 for a 10-20 rubric).
        max_grade: Upper bound; if None, the detected scale is used.
        out_of: If set, only apply when the detected scale matches this value.

    Returns:
        Feedback with the Total clamped, or unchanged if no total is found or
        it is already in range.
    """
    parsed = _parse_total_score(feedback)
    if not parsed:
        return feedback

    score, scale = parsed
    if scale <= 0:
        return feedback
    if out_of is not None and abs(scale - out_of) > 0.01:
        return feedback

    if min_grade > scale:
        logger.warning(
            "min_grade={} exceeds rubric scale={}; clamping floor to scale", min_grade, scale
        )
    upper = min(max_grade, scale) if max_grade is not None else scale
    lower = min(min_grade, upper)
    clamped = max(lower, min(upper, score))
    if abs(clamped - score) > 1e-9:
        return _replace_total_in_text(feedback, clamped, scale)
    return feedback
