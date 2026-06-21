from pydantic import Field

from src.core.schemas import Base, TokenModel
from src.user.schemas import UserProfileViewModel


class PasswordLoginRequest(Base):
    login: str = Field(
        ...,
        min_length=4,
        max_length=60,
        description="User login identifier",
        examples=["john_doe"],
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="User password",
        examples=["Passw0rd!"],
    )


class PasswordAuthResponse(Base):
    tokens: TokenModel = Field(..., description="Access and Refresh tokens")
    user: UserProfileViewModel = Field(..., description="Authenticated user profile")
