from uuid import uuid4

from ml.skill_extraction.taxonomy_mapper import (
    ALIAS_CONFIDENCE,
    EXACT_CONFIDENCE,
    MatchType,
    TaxonomyEntry,
    TaxonomyMapper,
)

ML_ID = uuid4()
K8S_ID = uuid4()
NLP_ID = uuid4()
MARKUP_ID = uuid4()


def _mapper() -> TaxonomyMapper:
    return TaxonomyMapper(
        [
            TaxonomyEntry(
                skill_id=ML_ID,
                canonical_name="Machine Learning",
                name="Machine Learning",
                aliases=("ML", "machine-learning"),
            ),
            TaxonomyEntry(
                skill_id=K8S_ID,
                canonical_name="Kubernetes",
                name="Kubernetes",
                aliases=("K8s", "k8s"),
            ),
            TaxonomyEntry(
                skill_id=NLP_ID,
                canonical_name="Natural Language Processing",
                name="NLP",
                aliases=("nlp",),
            ),
        ]
    )


def test_exact_canonical_has_full_confidence() -> None:
    match = _mapper().resolve("Machine Learning")
    assert match.skill_id == ML_ID
    assert match.canonical_name == "Machine Learning"
    assert match.confidence == EXACT_CONFIDENCE
    assert match.match_type is MatchType.EXACT


def test_punctuation_and_case_are_exact() -> None:
    mapper = _mapper()
    hyphen = mapper.resolve("machine-learning")
    camel = mapper.resolve("MachineLearning")
    assert hyphen.skill_id == ML_ID
    assert hyphen.match_type is MatchType.EXACT
    assert camel.skill_id == ML_ID
    assert camel.match_type is MatchType.EXACT


def test_alias_has_lower_confidence_than_exact() -> None:
    mapper = _mapper()
    alias = mapper.resolve("ML")
    exact = mapper.resolve("Machine Learning")
    assert alias.skill_id == ML_ID
    assert alias.match_type is MatchType.ALIAS
    assert alias.confidence == ALIAS_CONFIDENCE
    assert exact.confidence > alias.confidence


def test_k8s_and_nlp_aliases() -> None:
    mapper = _mapper()
    assert mapper.resolve("K8s").canonical_name == "Kubernetes"
    assert mapper.resolve("nlp").canonical_name == "Natural Language Processing"


def test_unknown_term_is_unmatched() -> None:
    match = _mapper().resolve("quantum knitting")
    assert match.skill_id is None
    assert match.canonical_name is None
    assert match.confidence == 0.0
    assert match.match_type is MatchType.UNMATCHED


def test_alias_collision_does_not_invent_a_skill() -> None:
    mapper = TaxonomyMapper(
        [
            TaxonomyEntry(ML_ID, "Machine Learning", "Machine Learning", ("ML",)),
            TaxonomyEntry(MARKUP_ID, "Markup Language", "Markup Language", ("ML",)),
        ]
    )
    match = mapper.resolve("ML")
    assert match.skill_id is None
    assert match.match_type is MatchType.COLLISION
    assert match.confidence == 0.0
