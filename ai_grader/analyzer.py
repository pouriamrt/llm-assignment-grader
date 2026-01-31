"""Analyze grading output files and compute statistics."""

import re
from pathlib import Path
from statistics import mean, median, stdev


def _parse_score(text: str) -> tuple[float, float] | None:
    """
    Extract total score from feedback text.
    Looks for Total row with x/y format. Returns (score, out_of) or None.
    """
    score = None
    out_of = None

    for line in text.splitlines():
        line_lower = line.lower()
        if "total" not in line_lower:
            continue
        m = re.search(r"(\d+)/(\d+)", line)
        if m:
            score = float(m.group(1))
            out_of = float(m.group(2))
            break

    if score is None:
        # Fallback: last x/y in file
        matches = list(re.finditer(r"(\d+)/(\d+)", text))
        if matches:
            m = matches[-1]
            score = float(m.group(1))
            out_of = float(m.group(2))

    if score is not None and out_of is not None and out_of > 0:
        return (score, out_of)
    return None


def analyze_outputs(output_dir: Path) -> dict:
    """
    Analyze feedback files in output directory and return statistics.

    Returns:
        Dict with keys: graded, errors, scores, stats, distribution, errors_list
    """
    output_path = Path(output_dir)
    if not output_path.is_dir():
        return {
            "graded": 0,
            "errors": 0,
            "scores": [],
            "stats": {},
            "distribution": {},
            "errors_list": [],
        }

    feedback_files = sorted(output_path.glob("*_feedback.md"))
    error_files = sorted(output_path.glob("*_error.txt"))

    scores: list[tuple[float, float, str]] = []  # (score, out_of, name)
    for f in feedback_files:
        name = f.stem.removesuffix("_feedback")
        try:
            text = f.read_text(encoding="utf-8")
        except OSError:
            continue
        parsed = _parse_score(text)
        if parsed:
            score, out_of = parsed
            scores.append((score, out_of, name))

    errors_list = [f.stem.removesuffix("_error") for f in error_files]

    # Normalize to percentage for aggregation (when out_of varies)
    raw_scores = [s[0] for s in scores]
    pcts = [100 * s[0] / s[1] for s in scores] if scores else []
    out_of_values = list({s[1] for s in scores})

    stats: dict = {}
    if scores:
        stats["count"] = len(scores)
        stats["errors_count"] = len(errors_list)
        stats["total_submissions"] = len(feedback_files) + len(errors_list)
        stats["mean_score"] = round(mean(raw_scores), 2)
        stats["mean_pct"] = round(mean(pcts), 1) if pcts else 0
        stats["median_score"] = round(median(raw_scores), 2)
        stats["min_score"] = min(raw_scores)
        stats["max_score"] = max(raw_scores)
        stats["std_dev"] = round(stdev(raw_scores), 2) if len(raw_scores) > 1 else 0
        stats["out_of"] = out_of_values[0] if len(out_of_values) == 1 else out_of_values

        # Distribution by score
        dist: dict[str, int] = {}
        for s, o, _ in scores:
            key = f"{int(s)}/{int(o)}"
            dist[key] = dist.get(key, 0) + 1
        stats["distribution"] = dict(sorted(dist.items(), reverse=True))

    return {
        "graded": len(scores),
        "errors": len(errors_list),
        "scores": scores,
        "stats": stats,
        "errors_list": errors_list,
    }


def format_stats_report(result: dict, output_dir: Path) -> str:
    """Format analysis result as a readable report."""
    lines: list[str] = []
    lines.append("# Grading Statistics")
    lines.append("")
    lines.append(f"**Output directory:** `{output_dir}`")
    lines.append("")

    stats = result.get("stats", {})
    if not stats:
        lines.append("No graded feedback files found.")
        if result.get("errors", 0) > 0:
            lines.append(f"Error files: {result['errors']}")
        return "\n".join(lines)

    s = stats
    lines.append("## Summary")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Graded | {s.get('count', 0)} |")
    lines.append(f"| Errors | {s.get('errors_count', 0)} |")
    lines.append(f"| Total submissions | {s.get('total_submissions', 0)} |")
    mean_str = f"{s.get('mean_score', 0)}/{s.get('out_of', '?')} ({s.get('mean_pct', 0)}%)"
    lines.append(f"| Mean score | {mean_str} |")
    lines.append(f"| Median score | {s.get('median_score', 0)} |")
    lines.append(f"| Min | {s.get('min_score', 0)} |")
    lines.append(f"| Max | {s.get('max_score', 0)} |")
    lines.append(f"| Std dev | {s.get('std_dev', 0)} |")
    lines.append("")

    dist = s.get("distribution", {})
    if dist:
        lines.append("## Score distribution")
        lines.append("")
        lines.append("| Score | Count |")
        lines.append("|-------|-------|")
        for score, count in dist.items():
            lines.append(f"| {score} | {count} |")
        lines.append("")

    if result.get("errors_list"):
        lines.append("## Submissions with errors")
        lines.append("")
        for name in result["errors_list"][:20]:
            lines.append(f"- {name}")
        if len(result["errors_list"]) > 20:
            lines.append(f"- ... and {len(result['errors_list']) - 20} more")
        lines.append("")

    return "\n".join(lines)
