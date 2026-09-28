from app.models.skill import Skill
from app.schemas.skill import SkillPublic


def to_skill_public(skill: Skill) -> SkillPublic:
    aliases = sorted({row.alias for row in skill.aliases}, key=str.lower)
    return SkillPublic(
        id=skill.id,
        name=skill.name,
        canonical_name=skill.canonical_name,
        category=skill.category,
        description=skill.description,
        difficulty=skill.difficulty,
        aliases=aliases,
    )
