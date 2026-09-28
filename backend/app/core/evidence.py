from app.core.config import settings
from app.core.enums import SkillSourceType


def source_reliability(source_type: str) -> float:
    mapping = {
        SkillSourceType.SELF.value: settings.self_declaration_reliability,
        SkillSourceType.RESUME.value: settings.resume_reliability,
        SkillSourceType.GITHUB.value: settings.github_reliability,
        SkillSourceType.COURSE.value: settings.course_reliability,
        SkillSourceType.ASSESSMENT.value: settings.assessment_reliability,
        SkillSourceType.PROJECT.value: settings.project_reliability,
        SkillSourceType.CERT.value: settings.cert_reliability,
        SkillSourceType.WORK.value: settings.work_reliability,
    }
    return mapping.get(source_type, settings.self_declaration_reliability)


def configured_source_reliabilities() -> dict[str, float]:
    return {
        source.value: source_reliability(source.value) for source in SkillSourceType
    }
