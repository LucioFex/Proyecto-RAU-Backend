from pydantic import BaseModel, EmailStr
from app.schemas.common import Role

class UserBase(BaseModel):
    name: str
    username: str
    email: EmailStr
    role: Role

class UserPublic(UserBase):
    id: str
    avatar_url: str | None = None
    title: str | None = None
    bio: str | None = None

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    username: str
    role: Role
    password: str

class UserUpdate(BaseModel):
    name: str | None = None
    title: str | None = None
    bio: str | None = None
    avatar_url: str | None = None
