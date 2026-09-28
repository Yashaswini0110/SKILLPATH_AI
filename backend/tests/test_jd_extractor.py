from uuid import uuid4

from ml.skill_extraction.jd_extractor import (
    RequirementType,
    RequirementWeights,
    extract_jd_skills,
)
from ml.skill_extraction.segmenter import segment_resume
from ml.skill_extraction.taxonomy_mapper import TaxonomyEntry, TaxonomyMapper


def _mapper() -> TaxonomyMapper:
    return TaxonomyMapper(
        [
            TaxonomyEntry(uuid4(), "Python", "Python", ()),
            TaxonomyEntry(uuid4(), "FastAPI", "FastAPI", ()),
            TaxonomyEntry(uuid4(), "Docker", "Docker", ()),
            TaxonomyEntry(uuid4(), "Git", "Git", ()),
            TaxonomyEntry(
                uuid4(),
                "Natural Language Processing",
                "Natural Language Processing",
                ("NLP",),
            ),
            TaxonomyEntry(uuid4(), "Kubernetes", "Kubernetes", ("K8s",)),
            TaxonomyEntry(uuid4(), "Machine Learning", "Machine Learning", ("ML",)),
        ]
    )


SAMPLE_JD = """Senior ML Engineer

Teams here also use Git for day-to-day collaboration.

Requirements
- Expert Python
- Must have FastAPI and Docker
- Machine Learning

Preferred qualifications
- Kubernetes (K8s)
- Nice to have NLP

Unknown tools such as quantum knitting are omitted.
"""


def test_required_preferred_and_mentioned_classification() -> None:
    extracted = extract_jd_skills(SAMPLE_JD, _mapper())
    skills = {item.canonical_name: item for item in extracted}
    assert skills["Python"].requirement is RequirementType.REQUIRED
    assert skills["Python"].importance == 1.0
    assert skills["FastAPI"].requirement is RequirementType.REQUIRED
    assert skills["Docker"].requirement is RequirementType.REQUIRED
    assert skills["Kubernetes"].requirement is RequirementType.PREFERRED
    assert skills["Kubernetes"].importance == 0.6
    nlp = skills["Natural Language Processing"]
    assert nlp.requirement is RequirementType.PREFERRED
    assert skills["Git"].requirement is RequirementType.MENTIONED
    assert skills["Git"].importance == 0.4


def test_unknown_jd_terms_are_not_invented() -> None:
    names = {item.canonical_name for item in extract_jd_skills(SAMPLE_JD, _mapper())}
    assert "quantum knitting" not in {name.lower() for name in names}
    assert names == {
        "Python",
        "FastAPI",
        "Docker",
        "Kubernetes",
        "Natural Language Processing",
        "Git",
        "Machine Learning",
    }


def test_requirement_weights_are_configurable() -> None:
    weights = RequirementWeights(required=0.8, preferred=0.5, mentioned=0.2)
    skills = {
        item.canonical_name: item
        for item in extract_jd_skills(SAMPLE_JD, _mapper(), weights)
    }
    assert skills["Python"].importance == 0.8
    assert skills["Kubernetes"].importance == 0.5
    assert skills["Git"].importance == 0.2


def test_jd_headings_are_segmented() -> None:
    sections = {section.name for section in segment_resume(SAMPLE_JD)}
    assert "required" in sections
    assert "preferred" in sections
