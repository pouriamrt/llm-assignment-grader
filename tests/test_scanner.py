"""Checks for safe, bounded archive extraction of untrusted submissions."""

import zipfile

from ai_grader.scanner.data_scanner import _unzip_in_folder


def test_unzip_extracts_normal_entries(tmp_path):
    sub = tmp_path / "submission"
    sub.mkdir()
    z = sub / "work.zip"
    with zipfile.ZipFile(z, "w") as zf:
        zf.writestr("report.txt", "hello")
        zf.writestr("nested/code.py", "print(1)")

    _unzip_in_folder(sub)

    assert (sub / "report.txt").read_text() == "hello"
    assert (sub / "nested" / "code.py").exists()
    assert not z.exists()  # zip removed after extraction


def test_unzip_blocks_path_traversal(tmp_path):
    sub = tmp_path / "submission"
    sub.mkdir()
    z = sub / "evil.zip"
    with zipfile.ZipFile(z, "w") as zf:
        zf.writestr("../escaped.txt", "pwned")  # zip-slip attempt
        zf.writestr("safe.txt", "ok")

    _unzip_in_folder(sub)

    assert (sub / "safe.txt").read_text() == "ok"  # safe entry still extracted
    assert not (tmp_path / "escaped.txt").exists()  # traversal blocked
