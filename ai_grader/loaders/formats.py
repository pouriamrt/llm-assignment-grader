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


def _read_ipynb(path: Path) -> str:
    """Convert Jupyter notebook to Python script using nbformat for grading.

    Extracts code cells and joins them into executable Python. Markdown and raw
    cells are excluded so the grader receives only the student's code.
    """
    import nbformat

    nb = nbformat.read(str(path), as_version=4)
    code_parts: list[str] = []
    for cell in nb.cells:
        if cell.cell_type != "code":
            continue
        source = cell.source
        if isinstance(source, list):
            source = "".join(source)
        if source.strip():
            code_parts.append(source.rstrip())
    return "\n\n".join(code_parts) if code_parts else ""


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
