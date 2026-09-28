from ml.skill_extraction.segmenter import segment_resume


def test_segment_identifies_skills_and_experience() -> None:
    text = """Summary
Builder of data products.

Skills
Python, SQL

Experience
Acme — used Python daily.
"""
    sections = {section.name: section.text for section in segment_resume(text)}
    assert "skills" in sections
    assert "experience" in sections
    assert "Python, SQL" in sections["skills"]
