from uuid import UUID

from pydantic import Field

from src.core.schemas import Base


class UserProfileViewModel(Base):
    id: UUID = Field(
        ...,
        description="User's unique identifier",
        examples=["123e4567-e89b-12d3-a456-426614174000"],
    )
    first_name: str | None = Field(
        None, description="User's first name", examples=["John"]
    )
    last_name: str | None = Field(
        None, description="User's last name", examples=["Doe"]
    )
    username: str | None = Field(None, description="Username", examples=["johndoe"])
    language_code: str | None = Field(
        None, description="User's preferred language code", examples=["en"]
    )
    photo_url: str | None = Field(
        None,
        description="URL of user's profile photo",
        examples=["https://example.com/photo.jpg"],
    )


class UserSummaryViewModel(Base):
    id: UUID = Field(
        ...,
        description="User's unique identifier",
        examples=["123e4567-e89b-12d3-a456-426614174000"],
    )
    first_name: str | None = Field(
        None, description="User's first name", examples=["John"]
    )
    last_name: str | None = Field(
        None, description="User's last name", examples=["Doe"]
    )
    username: str | None = Field(None, description="Username", examples=["johndoe"])


class UserSummaryWithContactsViewModel(Base):
    id: UUID = Field(
        ...,
        description="User's unique identifier",
        examples=["123e4567-e89b-12d3-a456-426614174000"],
    )
    full_name: str = Field(..., description="User's full name", examples=["John Doe"])
    username: str | None = Field(None, description="Username", examples=["johndoe"])
