from uuid import uuid4

from ml.skill_extraction.dictionary_extractor import extract_dictionary_hits
from ml.skill_extraction.pipeline import extract_skills_from_text
from ml.skill_extraction.segmenter import segment_resume
from ml.skill_extraction.taxonomy_mapper import TaxonomyEntry, TaxonomyMapper


def _mapper() -> TaxonomyMapper:
    return TaxonomyMapper(
        [
            TaxonomyEntry(uuid4(), "Java", "Java", ()),
            TaxonomyEntry(uuid4(), "JavaScript", "JavaScript", ("js",)),
            TaxonomyEntry(uuid4(), "Machine Learning", "Machine Learning", ("ML",)),
            TaxonomyEntry(uuid4(), "Python", "Python", ()),
        ]
    )


def test_javascript_does_not_become_java() -> None:
    mapper = _mapper()
    text = "Skills\nJavaScript, Python\n"
    hits = extract_dictionary_hits(text, mapper, segment_resume(text))
    names = {hit.canonical_name for hit in hits}
    assert "JavaScript" in names
    assert "Java" not in names


def test_ml_alias_maps_to_machine_learning() -> None:
    mapper = _mapper()
    text = "Skills\nML, Python\n"
    extracted = extract_skills_from_text(text, mapper)
    names = {item.canonical_name: item for item in extracted}
    assert "Machine Learning" in names
    assert names["Machine Learning"].inferred is True
    assert names["Machine Learning"].source == "RESUME"
    assert names["Machine Learning"].match_type == "alias"


def test_unknown_terms_are_not_invented() -> None:
    mapper = _mapper()
    extracted = extract_skills_from_text("Skills\nquantum knitting, Python\n", mapper)
    names = {item.canonical_name for item in extracted}
    assert names == {"Python"}


def test_snippet_does_not_start_mid_word() -> None:
    mapper = _mapper()
    text = (
        "Experience\n"
        "Developed production Python services for reporting dashboards.\n"
    )
    extracted = extract_skills_from_text(text, mapper)
    python = next(item for item in extracted if item.canonical_name == "Python")
    starts_clean = not python.evidence_snippet[
        0
    ].islower() or python.evidence_snippet.startswith("…")
    assert starts_clean
    assert "Python" in python.evidence_snippet


def test_extracted_skills_are_inferred() -> None:
    mapper = _mapper()
    extracted = extract_skills_from_text("Experience\nDeveloped Python APIs.\n", mapper)
    assert extracted
    assert all(item.inferred for item in extracted)
    assert all(item.evidence_snippet for item in extracted)
