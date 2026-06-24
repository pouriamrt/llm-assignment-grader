"""Checks for the bounded CSV/text extraction that keeps datasets from crowding out deliverables."""

from ai_grader.loaders import formats


def test_large_csv_is_sampled(tmp_path):
    rows = 5000
    csv = tmp_path / "data.csv"
    csv.write_text("col_a,col_b\n" + "\n".join(f"{i},x{i}" for i in range(rows)), encoding="utf-8")

    out = formats.extract_text_from_file(csv)

    assert "col_a,col_b" in out  # header kept
    assert "0,x0" in out  # first rows kept
    assert f"{rows - 1},x{rows - 1}" not in out  # last row dropped
    assert "preview" in out.lower()  # truncation note present
    assert len(out) < 50_000  # bounded


def test_small_csv_is_untouched(tmp_path):
    csv = tmp_path / "small.csv"
    body = "a,b\n1,2\n3,4"
    csv.write_text(body, encoding="utf-8")

    assert formats.extract_text_from_file(csv) == body


def test_header_only_csv_untouched(tmp_path):
    csv = tmp_path / "h.csv"
    csv.write_text("a,b,c", encoding="utf-8")  # header, zero data rows
    out = formats.extract_text_from_file(csv)
    assert out == "a,b,c"
    assert "preview" not in out.lower()


def test_oversized_text_is_capped(tmp_path):
    f = tmp_path / "big.txt"
    f.write_text("z" * 200_000, encoding="utf-8")

    out = formats.extract_text_from_file(f)

    assert len(out) <= formats.MAX_TEXT_CHARS + 100
    assert "truncated" in out
