"""Authentication and Guest schemas."""

from typing import Optional

from ninja.schema import Schema


class LoginSchema(Schema):
    email: str
    provider: str
    username: str
    password: str


class TokenSchema(Schema):
    token: str
    token_type: str = "bearer"


class GuestSchema(Schema):
    id: int
    name: str
    provider: str
    provider_id: int
    unique_id: str
    email: Optional[str]


class GuestLoginSchema(Schema):
    name: str
    provider: str
    provider_id: int
    avatar: str
