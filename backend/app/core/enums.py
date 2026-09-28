from enum import StrEnum


class UserRole(StrEnum):
    EMPLOYEE = "EMPLOYEE"
    MANAGER = "MANAGER"
    MENTOR = "MENTOR"
    HR_ADMIN = "HR_ADMIN"
    SYSTEM_ADMIN = "SYSTEM_ADMIN"


class TokenType(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"


class SkillSourceType(StrEnum):
    SELF = "SELF"
    RESUME = "RESUME"
    GITHUB = "GITHUB"
    COURSE = "COURSE"
    ASSESSMENT = "ASSESSMENT"
    PROJECT = "PROJECT"
    CERT = "CERT"
    WORK = "WORK"


class LearningFormat(StrEnum):
    VIDEO = "video"
    TEXT = "text"
    HANDS_ON = "hands-on"
    LIVE = "live"


class JDSourceType(StrEnum):
    PASTE = "PASTE"
    FILE = "FILE"


class RequirementType(StrEnum):
    REQUIRED = "REQUIRED"
    PREFERRED = "PREFERRED"
    MENTIONED = "MENTIONED"
