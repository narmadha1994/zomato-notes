from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=8)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError(
                "Name cannot be empty or whitespace-only"
            )

        return value.strip()


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NoteCreate(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=120
    )

    content: str = Field(
        min_length=1
    )

    tag: str
    owner_id: int


class NoteResponse(BaseModel):
    id: int
    title: str
    content: str
    tag: str
    owner_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NoteUpdate(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=120
    )

    content: str = Field(
        min_length=1
    )

    tag: str