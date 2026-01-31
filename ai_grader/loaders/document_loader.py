"""Load documents from various file formats into text for LLM context."""

from pathlib import Path

from loguru import logger
from tqdm import tqdm

from ai_grader.loaders.formats import (
    SUPPORTED_EXTENSIONS,
    extract_text_from_file,
)


def load_document(file_path: Path) -> str | None:
    """
    Load a single document and return its text content.

    Args:
        file_path: Path to the file.

    Returns:
        Extracted text content or None if loading failed.
    """
    try:
        return extract_text_from_file(file_path)
    except Exception as e:
        logger.debug("Failed to load {}: {}", file_path, e)
        return None


def load_documents_from_folder(
    folder_path: Path,
    recursive: bool = True,
) -> list[tuple[Path, str]]:
    """
    Load all supported documents from a folder (and optionally subfolders).

    Args:
        folder_path: Path to the folder.
        recursive: If True, scan subfolders.

    Returns:
        List of (file_path, text_content) tuples.
    """
    results: list[tuple[Path, str]] = []

    pattern = "**/*" if recursive else "*"
    for file_path in tqdm(folder_path.glob(pattern), desc="Loading documents"):
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        text = load_document(file_path)
        if text and text.strip():
            results.append((file_path, text))

    return results
