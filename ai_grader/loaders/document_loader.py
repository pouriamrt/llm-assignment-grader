"""Load documents from various file formats into text and images for LLM context (multimodal)."""

from pathlib import Path
from typing import Any

from loguru import logger

from ai_grader.loaders.formats import (
    IMAGE_EXTENSIONS,
    SUPPORTED_EXTENSIONS,
    extract_content_parts_from_file,
)

# All extensions we can load (text + images)
LOADABLE_EXTENSIONS = SUPPORTED_EXTENSIONS | IMAGE_EXTENSIONS


def _is_empty_text_only(parts: list[dict[str, Any]], file_path: Path) -> bool:
    """True if the only content is a single text part with no content beyond the file label."""
    if len(parts) != 1 or parts[0].get("type") != "text":
        return False
    text = (parts[0].get("text") or "").strip()
    label = f"=== FILE: {file_path.name} ==="
    return not text or text == label or text == label + "\n"


def load_document(file_path: Path) -> list[dict[str, Any]] | None:
    """
    Load a single document and return multimodal content parts for the LLM.

    Text files yield one text part; image files yield a label part plus an image_url part.

    Args:
        file_path: Path to the file.

    Returns:
        List of content parts (e.g. [{"type": "text", "text": "..."}] or
        [{"type": "text", ...}, {"type": "image_url", ...}]) or None if loading failed.
    """
    try:
        parts = extract_content_parts_from_file(file_path)
        if _is_empty_text_only(parts, file_path):
            return None
        return parts
    except Exception as e:
        logger.debug("Failed to load {}: {}", file_path, e)
        return None


def load_documents_from_folder(
    folder_path: Path,
    recursive: bool = True,
) -> list[tuple[Path, list[dict[str, Any]]]]:
    """
    Load all supported documents (including images) from a folder.

    Args:
        folder_path: Path to the folder.
        recursive: If True, scan subfolders.

    Returns:
        List of (file_path, content_parts) tuples. content_parts is a list of
        multimodal parts (text and/or image_url) for LangChain.
    """
    results: list[tuple[Path, list[dict[str, Any]]]] = []

    pattern = "**/*" if recursive else "*"
    for file_path in folder_path.glob(pattern):
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() not in LOADABLE_EXTENSIONS:
            continue

        parts = load_document(file_path)
        if parts:
            results.append((file_path, parts))

    return results
