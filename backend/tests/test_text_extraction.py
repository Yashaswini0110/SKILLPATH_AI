from pathlib import Path

from ml.skill_extraction.text_extraction import extract_text


def test_extract_text_from_txt(tmp_path: Path) -> None:
    path = tmp_path / "resume.txt"
    path.write_text("Skills\nPython\n", encoding="utf-8")
    assert "Python" in extract_text(path)
