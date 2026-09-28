from decimal import Decimal

from app.core.config import settings
from app.core.enums import RequirementType
from app.core.paths import ensure_repo_on_path

ensure_repo_on_path()

from ml.skill_extraction.jd_extractor import RequirementWeights  # noqa: E402


def requirement_from_importance(importance: Decimal | float) -> RequirementType:
    value = float(importance)
    if value >= 0.85:
        return RequirementType.REQUIRED
    if value >= 0.5:
        return RequirementType.PREFERRED
    return RequirementType.MENTIONED


def configured_jd_weights() -> RequirementWeights:
    return RequirementWeights(
        required=settings.jd_weight_required,
        preferred=settings.jd_weight_preferred,
        mentioned=settings.jd_weight_mentioned,
    )
