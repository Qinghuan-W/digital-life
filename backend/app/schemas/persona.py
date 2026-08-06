from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


def normalize_required_text(value: str, *, label: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{label}不能为空")
    return normalized


def normalize_optional_text(value: object) -> object:
    if not isinstance(value, str):
        return value
    normalized = value.strip()
    return normalized or None


class PersonaCreateRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=80)
    relationship_label: str = Field(min_length=1, max_length=50)
    age: int | None = Field(default=None, ge=1, le=150)
    gender_label: str | None = Field(default=None, max_length=50)
    description: str | None = Field(default=None, max_length=500)

    @field_validator("display_name")
    @classmethod
    def validate_display_name(cls, value: str) -> str:
        return normalize_required_text(value, label="Persona 名称")

    @field_validator("relationship_label")
    @classmethod
    def validate_relationship(cls, value: str) -> str:
        return normalize_required_text(value, label="关系")

    @field_validator("gender_label", "description", mode="before")
    @classmethod
    def normalize_optional_fields(cls, value: object) -> object:
        return normalize_optional_text(value)


class PersonaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    display_name: str
    relationship_label: str
    age: int | None
    gender_label: str | None
    description: str | None
    avatar_url: str | None
    created_at: datetime
    updated_at: datetime


class PersonaSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    display_name: str
    relationship_label: str
    age: int | None
    gender_label: str | None
