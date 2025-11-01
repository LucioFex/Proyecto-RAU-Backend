from pydantic import BaseModel, EmailStr
from app.schemas.users import UserPublic

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class AuthResponse(BaseModel):
    user: UserPublic
    access_token: str
    token_type: str = "bearer"
