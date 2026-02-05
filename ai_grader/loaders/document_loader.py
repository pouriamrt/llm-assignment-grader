"""Load documents from various file formats into text and images for LLM context (multimodal)."""

from pathlib import Path
from typing import Any

from loguru import logger
from pathspec import PathSpec

from ai_grader.loaders.formats import (
    IMAGE_EXTENSIONS,
    SUPPORTED_EXTENSIONS,
    extract_content_parts_from_file,
)

# Ignore file names (gitignore-style), checked in each scanned folder
DEFAULT_IGNORE_FILES = (".graderignore", ".gitignore")

# All extensions we can load (text + images)
LOADABLE_EXTENSIONS = SUPPORTED_EXTENSIONS | IMAGE_EXTENSIONS


def _load_ignore_spec(
    folder_path: Path,
    extra_patterns: list[str] | None = None,
    ignore_file_names: tuple[str, ...] = DEFAULT_IGNORE_FILES,
) -> PathSpec | None:
    """
    Build a gitignore-style PathSpec from .graderignore/.gitignore in folder_path
    and optional extra patterns.

    Args:
        folder_path: Directory to look for ignore files.
        extra_patterns: Additional exclude patterns (e.g. from CLI).
        ignore_file_names: Names of ignore files to read (.graderignore, .gitignore).

    Returns:
        PathSpec to match paths that should be excluded, or None if no patterns.
    """
    lines: list[str] = []
    for name in ignore_file_names:
        path = folder_path / name
        if path.is_file():
            try:
                content = path.read_text(encoding="utf-8", errors="replace")
                lines.extend(content.splitlines())
            except OSError as e:
                logger.debug("Could not read {}: {}", path, e)
    if extra_patterns:
        lines.extend(extra_patterns)
    if not lines:
        return None
    return PathSpec.from_lines("gitignore", lines)


def _path_should_ignore(relative_path: Path, spec: PathSpec | None, root: Path) -> bool:
    """Return True if the path should be excluded by the ignore spec."""
    if spec is None:
        return False
    # PathSpec expects path relative to root, with forward slashes
    try:
        rel = relative_path.relative_to(root)
    except ValueError:
        return False
    path_str = rel.as_posix()
    return spec.match_file(path_str)


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
    exclude_patterns: list[str] | None = None,
    ignore_file_names: tuple[str, ...] = DEFAULT_IGNORE_FILES,
) -> list[tuple[Path, list[dict[str, Any]]]]:
    """
    Load all supported documents (including images) from a folder.

    Excludes files and folders matching gitignore-style patterns from
    .graderignore and .gitignore in the folder, plus any extra exclude_patterns.

    Args:
        folder_path: Path to the folder.
        recursive: If True, scan subfolders.
        exclude_patterns: Additional gitignore-style patterns (e.g. from CLI).
        ignore_file_names: Names of ignore files to read in the folder.

    Returns:
        List of (file_path, content_parts) tuples. content_parts is a list of
        multimodal parts (text and/or image_url) for LangChain.
    """
    results: list[tuple[Path, list[dict[str, Any]]]] = []
    ignore_spec = _load_ignore_spec(
        folder_path,
        extra_patterns=exclude_patterns,
        ignore_file_names=ignore_file_names,
    )

    pattern = "**/*" if recursive else "*"
    for file_path in folder_path.glob(pattern):
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() not in LOADABLE_EXTENSIONS:
            continue
        if _path_should_ignore(file_path, ignore_spec, folder_path):
            logger.debug("Excluded (ignore): {}", file_path.relative_to(folder_path))
            continue

        parts = load_document(file_path)
        if parts:
            results.append((file_path, parts))

    return results
