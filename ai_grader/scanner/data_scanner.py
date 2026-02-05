"""Scan data folder and collect assignment content for grading (text + images, multimodal)."""

import zipfile
from pathlib import Path
from typing import Any

from loguru import logger
from tqdm import tqdm

from ai_grader.loaders import load_documents_from_folder


def _unzip_in_folder(folder_path: Path) -> None:
    """Unzip any .zip files in folder (and subfolders), delete zips after extracting."""
    while True:
        zips = list(folder_path.rglob("*.zip"))
        if not zips:
            break
        for z in zips:
            try:
                with zipfile.ZipFile(z, "r") as zf:
                    zf.extractall(z.parent)
                z.unlink()
                logger.debug("Extracted and removed {}", z.name)
            except (zipfile.BadZipFile, zipfile.LargeZipFile, OSError) as e:
                logger.warning("Failed to unzip {}: {}", z.name, e)


def scan_assignments(
    data_folder: Path,
    exclude_patterns: list[str] | None = None,
) -> list[dict]:
    """
    Scan the data folder: each subfolder is treated as one assignment submission.

    Excludes files/folders matching .graderignore and .gitignore in each submission
    folder, plus any extra exclude_patterns (gitignore-style).

    Args:
        data_folder: Path to the data folder (e.g., ./data).
        exclude_patterns: Additional gitignore-style patterns (e.g. from --exclude).

    Returns:
        List of dicts with keys:
          - folder_name: Name of the subfolder (e.g., student_id)
          - folder_path: Full path to the subfolder
          - files: List of (relative_path, content_parts) tuples
          - context: Combined text of all files (text-only, fallback)
          - content_parts: List of multimodal parts (text + images) for the LLM
    """
    data_path = Path(data_folder)
    if not data_path.is_dir():
        logger.warning("Data path is not a directory: {}", data_path)
        return []

    results: list[dict] = []
    extra = exclude_patterns or []

    for item in tqdm(sorted(data_path.iterdir()), desc="Scanning data folder", unit="folder"):
        if not item.is_dir():
            continue
        if item.name == "Archive":
            continue

        _unzip_in_folder(item)
        files = load_documents_from_folder(item, recursive=True, exclude_patterns=extra)
        if not files:
            logger.debug("Skipping empty folder: {}", item.name)
            continue

        file_entries: list[tuple[str, list[dict[str, Any]]]] = []
        context_parts: list[str] = []
        all_content_parts: list[dict[str, Any]] = []

        for file_path, parts in files:
            rel = str(file_path.relative_to(item))
            file_entries.append((rel, parts))
            for part in parts:
                all_content_parts.append(part)
                if part.get("type") == "text" and part.get("text"):
                    context_parts.append(part["text"])

        context = "\n\n".join(context_parts)
        results.append(
            {
                "folder_name": item.name,
                "folder_path": item,
                "files": file_entries,
                "context": context,
                "content_parts": all_content_parts,
            }
        )
        logger.debug("Scanned {} ({} files)", item.name, len(file_entries))

    logger.info("Scanned {} assignment(s) from {}", len(results), data_path)
    return results
