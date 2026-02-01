"""Text extraction for various file formats."""

from pathlib import Path

SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".pptx",
    ".py",
    ".txt",
    ".md",
    ".json",
    ".xml",
    ".html",
    ".htm",
    ".csv",
    ".yaml",
    ".yml",
    ".ipynb",
}


def _read_pdf(path: Path) -> str:
    """Extract text from PDF."""
    from pypdf import PdfReader

    reader = PdfReader(path)
    parts = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            parts.append(text)
    return "\n\n".join(parts)


def _read_docx(path: Path) -> str:
    """Extract text from Word document."""
    from docx import Document

    doc = Document(path)
    parts = []
    for para in doc.paragraphs:
        if para.text.strip():
            parts.append(para.text)
    for table in doc.tables:
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells]
            if any(cells):
                parts.append(" | ".join(cells))
    return "\n\n".join(parts)


def _read_pptx(path: Path) -> str:
    """Extract text from PowerPoint."""
    from pptx import Presentation

    prs = Presentation(path)
    parts = []
    for slide_num, slide in enumerate(prs.slides, 1):
        slide_texts = [f"--- Slide {slide_num} ---"]
        for shape in slide.shapes:
            if hasattr(shape, "text") and shape.text.strip():
                slide_texts.append(shape.text)
        if len(slide_texts) > 1:
            parts.append("\n".join(slide_texts))
    return "\n\n".join(parts)


def _read_text(path: Path) -> str:
    """Read plain text file with encoding fallback."""
    encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
    last_error = None
    for enc in encodings:
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError as e:
            last_error = e
    raise last_error or UnicodeDecodeError("unknown", b"", 0, 1, "")


# Notebook extraction limits to avoid filling context with non-essential content
_MAX_MARKDOWN_LINES = 25  # Keep first N lines of long markdown; rest truncated
_MAX_MARKDOWN_CHARS = 1200  # Or truncate by chars (whichever hits first)
_MAX_CODE_LINES = 800  # Truncate very long code cells with a note


def _truncate_text(text: str, max_lines: int, max_chars: int, label: str = "truncated") -> str:
    """Truncate text to max_lines and max_chars; append a short note if truncated."""
    lines = text.splitlines()
    if len(lines) <= max_lines and len(text) <= max_chars:
        return text
    head_lines = lines[:max_lines]
    head = "\n".join(head_lines)
    if len(head) > max_chars:
        head = (
            head[: max_chars - 50].rsplit("\n", 1)[0]
            if "\n" in head[: max_chars - 50]
            else head[: max_chars - 50]
        )
    return head.rstrip() + f"\n\n[... {label} for context ...]"


def _read_ipynb(path: Path) -> str:
    """Extract code and markdown from Jupyter notebook, truncating long non-code content.

    - Code cells: included in full (or truncated if extremely long) for grading.
    - Markdown/raw cells: truncated when long so instructions and prose do not fill context.
    - Cell outputs are not included (they would bloat context with plots, data, etc.).
    """
    import json

    nb = json.loads(path.read_text(encoding="utf-8"))
    parts = []
    for cell in nb.get("cells", []):
        cell_type = cell.get("cell_type", "")
        source = "".join(cell.get("source", []))
        if not source.strip():
            continue

        if cell_type == "code":
            lines = source.splitlines()
            if len(lines) > _MAX_CODE_LINES:
                head = "\n".join(lines[:_MAX_CODE_LINES])
                source = (
                    head
                    + f"\n\n[... code truncated ({len(lines) - _MAX_CODE_LINES} more lines) ...]"
                )
            parts.append(f"[{cell_type}]\n{source}")

        elif cell_type in ("markdown", "raw"):
            truncated = _truncate_text(
                source,
                max_lines=_MAX_MARKDOWN_LINES,
                max_chars=_MAX_MARKDOWN_CHARS,
                label="markdown truncated",
            )
            parts.append(f"[{cell_type}]\n{truncated}")

        else:
            # Unknown cell type: include but truncate
            truncated = _truncate_text(
                source,
                max_lines=_MAX_MARKDOWN_LINES,
                max_chars=_MAX_MARKDOWN_CHARS,
                label="cell truncated",
            )
            parts.append(f"[{cell_type}]\n{truncated}")

    return "\n\n".join(parts)


def extract_text_from_file(file_path: Path) -> str:
    """
    Extract text from a file based on its extension.

    Args:
        file_path: Path to the file.

    Returns:
        Extracted text content.

    Raises:
        ValueError: If the file format is not supported.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    ext = path.suffix.lower()

    if ext == ".pdf":
        return _read_pdf(path)
    if ext == ".docx":
        return _read_docx(path)
    if ext == ".pptx":
        return _read_pptx(path)
    if ext == ".ipynb":
        return _read_ipynb(path)
    if ext in SUPPORTED_EXTENSIONS:
        return _read_text(path)

    raise ValueError(f"Unsupported file format: {ext}")
