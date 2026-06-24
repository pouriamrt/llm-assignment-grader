"""Checks for total-grade clamping across arbitrary rubric scales."""

from ai_grader.guardrails import apply_grade_guardrails

_FB = "| **Total** | **{}/20** | |\n\nsome feedback"


def test_clamps_below_floor():
    out = apply_grade_guardrails(_FB.format(4), min_grade=10)
    assert "**10/20**" in out


def test_clamps_above_scale():
    # 22/20 is impossible; ceiling defaults to the rubric scale (20).
    out = apply_grade_guardrails(_FB.format(22))
    assert "**20/20**" in out


def test_in_range_unchanged():
    text = _FB.format(18.5)
    assert apply_grade_guardrails(text, min_grade=10) == text


def test_no_trailing_zero_formatting():
    out = apply_grade_guardrails(_FB.format(3), min_grade=10)
    assert "**10/20**" in out and "10.0" not in out


def test_out_of_gate_skips_mismatched_scale():
    # Only act on /2 rubrics; a /20 total is left alone.
    text = _FB.format(40)
    assert apply_grade_guardrails(text, max_grade=2, out_of=2.0) == text


def test_no_total_is_passthrough():
    text = "no rubric here"
    assert apply_grade_guardrails(text, min_grade=10) == text


def test_fractional_scale_preserved():
    # /2.5 rubric must not be rewritten to /2 (regression: out_of was formatted :.0f).
    out = apply_grade_guardrails("| **Total** | **0.5/2.5** | |", min_grade=1)
    assert "**1/2.5**" in out


def test_min_equals_max_forces_single_value():
    out = apply_grade_guardrails(_FB.format(5), min_grade=15, max_grade=15)
    assert "**15/20**" in out
