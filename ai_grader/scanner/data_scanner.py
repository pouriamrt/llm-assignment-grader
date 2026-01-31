"""Scan data folder and collect assignment content for grading."""

from pathlib import Path

from ai_grader.loaders import load_documents_from_folder


def scan_assignments(data_folder: Path) -> list[dict]:
    """
    Scan the data folder: each subfolder is treated as one assignment submission.

    Args:
        data_folder: Path to the data folder (e.g., ./data).

    Returns:
        List of dicts with keys:
          - folder_name: Name of the subfolder (e.g., student_id)
          - folder_path: Full path to the subfolder
          - files: List of (relative_path, content) tuples
          - context: Combined text of all files for LLM
    """
    data_path = Path(data_folder)
    if not data_path.is_dir():
        return []

    results: list[dict] = []

    for item in sorted(data_path.iterdir()):
        if not item.is_dir():
            continue

        files = load_documents_from_folder(item, recursive=True)
        if not files:
            continue

        # Build (relative_path, content) and combined context
        file_entries: list[tuple[str, str]] = []
        context_parts: list[str] = []

        for file_path, content in files:
            rel = str(file_path.relative_to(item))
            file_entries.append((rel, content))
            context_parts.append(f"=== FILE: {rel} ===\n\n{content}")

        context = "\n\n".join(context_parts)

        results.append(
            {
                "folder_name": item.name,
                "folder_path": item,
                "files": file_entries,
                "context": context,
            }
        )

    return results
