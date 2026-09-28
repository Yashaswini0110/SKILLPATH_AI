from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.common import ORMModel


class EducationBase(BaseModel):
    degree: str = Field(min_length=1, max_length=255)
    institution: str = Field(min_length=1, max_length=255)
    field_of_study: str | None = Field(default=None, max_length=255)
    start_year: int | None = Field(default=None, ge=1950, le=2100)
    end_year: int | None = Field(default=None, ge=1950, le=2100)
    description: str | None = None

    @field_validator("degree", "institution")
    @classmethod
    def strip_required(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("This field is required")
        return stripped

    @model_validator(mode="after")
    def validate_years(self) -> "EducationBase":
        if self.start_year is not None and self.end_year is not None:
            if self.end_year < self.start_year:
                raise ValueError("end_year cannot be before start_year")
        return self


class EducationCreate(EducationBase):
    pass


class EducationUpdate(BaseModel):
    degree: str | None = Field(default=None, min_length=1, max_length=255)
    institution: str | None = Field(default=None, min_length=1, max_length=255)
    field_of_study: str | None = Field(default=None, max_length=255)
    start_year: int | None = Field(default=None, ge=1950, le=2100)
    end_year: int | None = Field(default=None, ge=1950, le=2100)
    description: str | None = None


class EducationPublic(ORMModel):
    id: UUID
    degree: str
    institution: str
    field_of_study: str | None = None
    start_year: int | None = None
    end_year: int | None = None
    description: str | None = None


class ExperienceBase(BaseModel):
    company: str = Field(min_length=1, max_length=255)
    role_title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    start_date: date
    end_date: date | None = None
    is_current: bool = False

    @field_validator("company", "role_title")
    @classmethod
    def strip_required(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("This field is required")
        return stripped

    @model_validator(mode="after")
    def validate_dates(self) -> "ExperienceBase":
        if self.is_current:
            object.__setattr__(self, "end_date", None)
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("end_date cannot be before start_date")
        if not self.is_current and self.end_date is None:
            raise ValueError("end_date is required unless is_current is true")
        return self


class ExperienceCreate(ExperienceBase):
    pass


class ExperienceUpdate(BaseModel):
    company: str | None = Field(default=None, min_length=1, max_length=255)
    role_title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool | None = None


class ExperiencePublic(ORMModel):
    id: UUID
    company: str
    role_title: str
    description: str | None = None
    start_date: date
    end_date: date | None = None
    is_current: bool
